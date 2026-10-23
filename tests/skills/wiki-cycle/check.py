"""wiki-cycle test suite: sandbox, prompts and checks for run_skill_test.py.

The cycle is an orchestrator: it spawns wiki-ingester workers and runs other skills
(/wiki-update inside each worker, /wiki-report at the end). So the sandbox carries
repo copies of all of them, never the installed ones:
- the step skills in EXTRA_SKILLS are rendered beside wiki-cycle by the runner;
- the wiki-ingester agent is rendered into the sandbox project's .claude/agents/
  (a project agent takes precedence over the user-level one of the same name), with
  its ~/.claude paths pointed at this repo's scripts and the sandbox copies;
- the Skill tool is blocked, so "/wiki-report" can only be followed from the file.
The agent is rendered from the working tree even under --skill-ref.

The sandbox root stands in for the project-notebooks repo: a git repo holding the
registry and notebooks/<nb>/, with the project folder, the skills and the agent
files ignored. Each case resets the notebook, prepares its own state and commits it
as the fixture commit; the checks read what changed since that commit from git.

Seed: the wiki-update suite's seed notebook plus fixtures/extra-seed/. The two
queued sources are short live pages (cases.json); resume's staged entries are filed
from test-authored bodies by wiki-update.py itself, so no third-party text is committed.

Since #42 (2026-09-24) the sandbox also carries the wiki-checker agent and a second
registered project, `other` (bot other-bot), so a case can give the notebook a second
reader. `triage-shared` sends one live page to other-bot's bucket; `checker-resume`
resumes a run after ingest with one staged entry from a 21-minute test transcript
whose entry drops the talk's ninth technique and inflates a number (fixtures/checker/).

Since #65 (2026-10-03) the email step: `email-approve` and `email-unattended` run
`--discover-only` with `email.enabled` in the project config and three test-written
emails in sandbox/mail/ (a Medium-style digest, a full-text newsletter, a link roundup
behind redirects), which the script reads through $WIKI_GMAIL_FROM_DIR and
$WIKI_GMAIL_RESOLVE_MAP, so no session can reach a real mailbox. Four candidates are in
the seed notebook's scope (AI agents, language models) and three plainly are not; the
user's answer is given in the prompt for the first case and absent in the second.

Since #75 (2026-10-05) the Drive step: `drive-files` runs `--discover-only` with `drive.enabled` and a
test Drive folder on disk (sandbox/drive/, read through $WIKI_DRIVE_FROM_DIR, so no session can reach a
real Drive; its parent folder name exists in no real Drive either). It holds a link capture, a PDF, a
PowerPoint deck, an image (each saved as a raw and queued), a note with no link and a voice memo (both
left in Drive, which the report must tell the user).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = "cycletest"
EXTRA_SKILLS = ["wiki-update", "wiki-report", "wiki-refresh", "wiki-claims", "wiki-discover",
                "wiki-lint", "wiki-promote", "wiki-list", "wiki-search", "wiki-triage"]
DISALLOWED_TOOLS = ["Skill"]
ALLOWED_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep", "Agent", "Task", "TodoWrite", "WebFetch",
    "Bash(python:*)", "Bash(python3:*)", "Bash(uv:*)", "Bash(node:*)", "Bash(cd:*)", "Bash(ls:*)",
    "Bash(mv:*)", "Bash(rm:*)", "Bash(mkdir:*)", "Bash(cp:*)", "Bash(cat:*)",
    "Bash(grep:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)", "Bash(find:*)", "Bash(xargs:*)",
    "Bash(sort:*)", "Bash(echo:*)", "Bash(pwd:*)", "Bash(date:*)", "Bash(git:*)", "Bash(curl:*)",
    "Bash(yt-dlp:*)", "Bash(sed:*)", "Bash(awk:*)", "Bash(test:*)", "Bash(touch:*)",
]
MACHINE_FILES = {"_index.md", "_map.md", "index.md", "map.md", "readme.md"}
STEP_FIELDS = ("skill", "cycle_id", "step", "timestamp", "status", "summary",
               "queued", "skipped", "deferred", "notes", "errors")
# The step pairs a quick --ingest-only run must leave (cycle-step-return-format.md)
QUICK_STEPS = ("update", "lint-mechanical", "reciprocate-backlinks", "index-per-folder", "map-compile")
# only a --full run writes these
FULL_ONLY = ("lint-semantic", "claims")  # synthesis runs in every ingesting mode since 2026-10-19, promote since #184 follows confirm_before_promote in every mode (Mark's yes for each, 2026-10-19 and 2026-10-23)


def _suite() -> dict:
    return json.loads((HERE / "cases.json").read_text(encoding="utf-8"))


def _rmtree(path: Path) -> None:
    def onexc(func, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass
    if path.exists():
        shutil.rmtree(path, onexc=onexc)


def _qmd() -> list[str]:
    shim = shutil.which("qmd")
    if not shim:
        raise SystemExit("qmd not found on PATH")
    entry = Path(shim).resolve().parent / "node_modules" / "@tobilu" / "qmd" / "dist" / "cli" / "qmd.js"
    node = shutil.which("node")
    return [node, str(entry)] if entry.exists() and node else [shim]


def _qmd_index_file(index: str) -> Path:
    return Path.home() / ".cache" / "qmd" / f"{index}.sqlite"


def _git(ctx: dict, *args: str) -> str:
    return subprocess.run(["git", "-C", str(ctx["sandbox"]), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def _script(ctx: dict, name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ctx["scripts"] / name), *args], cwd=ctx["project"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env={**os.environ, **ctx["env"]})


def _today(ctx: dict) -> str:
    sys.path.insert(0, str(ctx["scripts"]))
    from _wiki_config import today_label
    return today_label()


# ---------- fixtures ----------

def prepare_fixtures(repo: Path, refresh: bool = False) -> list[dict]:
    """The queued sources are fetched live by the workers; report whether each answers."""
    import urllib.request
    out = []
    for sid, src in _suite()["sources"].items():
        try:
            req = urllib.request.Request(src["url"], headers={"User-Agent": "llm-wiki-skilltest"})
            with urllib.request.urlopen(req, timeout=30) as r:
                out.append({"source": sid, "status": f"live {r.status}", "bytes": len(r.read())})
        except Exception as e:  # noqa: BLE001 - reported, never fatal
            out.append({"source": sid, "status": "UNREACHABLE", "detail": str(e)[:200]})
    return out


# ---------- sandbox ----------

def _seed(ctx: dict) -> None:
    """A fresh copy of the seed notebook at ctx['notebook']."""
    nb, repo = ctx["notebook"], ctx["repo"]
    _rmtree(nb)
    shutil.copytree(HERE.parent / "wiki-update" / "fixtures" / "seed-notebook", nb)
    shutil.copytree(HERE / "fixtures" / "extra-seed", nb, dirs_exist_ok=True)
    sys.path.insert(0, str(ctx["scripts"]))
    from _wiki_config import SCAFFOLD_TAXONOMY
    for d in ["_inbox/proposed", "_inbox/pending", "_inbox/done", "_inbox/temp", "_inbox/reports", "raw",
              *[f"wiki/{t}" for t in SCAFFOLD_TAXONOMY]]:
        (nb / d).mkdir(parents=True, exist_ok=True)
        (nb / d / ".gitkeep").touch()


def render_replacements(ctx: dict) -> dict:
    agents = ctx["sandbox"] / "agents"
    return {
        "~/.claude/agents/wiki-ingester-config.json": (agents / "wiki-ingester-config.json").as_posix(),
        "~/.claude/agents/wiki-ingester-reading-list.json": (agents / "wiki-ingester-reading-list.json").as_posix(),
        "~/.claude/agents/wiki-checker-config.json": (agents / "wiki-checker-config.json").as_posix(),
        "~/.claude/wiki-scripts": ctx["scripts"].as_posix(),
        "~/.claude/skills/": ctx["skill_dir"].parent.as_posix() + "/",
    }


def setup(model: str, sandbox: Path, repo: Path) -> dict:
    _rmtree(sandbox)
    scripts = repo / "scripts"
    nb = sandbox / "notebooks" / NOTEBOOK
    project = sandbox / "project"
    ctx = {"sandbox": sandbox, "project": project, "notebook": nb, "repo": repo, "scripts": scripts,
           "skill_dir": sandbox / "skill" / "wiki-cycle", "registry": sandbox / "linked-notebooks.json"}
    _seed(ctx)
    ctx["registry"].write_text(json.dumps({"notebooks": {
        NOTEBOOK: {"root": f"notebooks/{NOTEBOOK}", "confirm_before_create": True, "confirm_before_promote": True},
        "other": {"root": "notebooks/other", "discord": {"bot_name": "other-bot", "user_id": "222"}}}},
        indent=2), encoding="utf-8")
    (sandbox / "notebooks" / "other" / "wiki").mkdir(parents=True)
    (sandbox / "notebooks" / "other" / "wiki" / ".gitkeep").touch()
    _write_config(ctx, email=False)

    # the wiki-ingester and wiki-checker agents and their sidecars, from this repo, install paths -> sandbox
    repl = render_replacements(ctx)
    src = repo / "agents" / "wiki-ingester"
    chk = repo / "agents" / "wiki-checker"
    (sandbox / "agents").mkdir()
    (project / ".claude" / "agents").mkdir()
    for f, dest in ((src / "AGENT.md", project / ".claude" / "agents" / "wiki-ingester.md"),
                    (src / "wiki-ingester-config.json", sandbox / "agents" / "wiki-ingester-config.json"),
                    (src / "wiki-ingester-reading-list.json", sandbox / "agents" / "wiki-ingester-reading-list.json"),
                    (chk / "AGENT.md", project / ".claude" / "agents" / "wiki-checker.md"),
                    (chk / "wiki-checker-config.json", sandbox / "agents" / "wiki-checker-config.json")):
        text = f.read_text(encoding="utf-8").replace("{{WIKI_SCRIPTS_DIR}}", scripts.as_posix())
        # the reading list says where the skills are installed; point it at the sandbox copies
        text = text.replace("Installed globally at ~/.claude/skills/", "Rendered for this run at ~/.claude/skills/")
        for old, new in repl.items():
            text = text.replace(old, new)
        dest.write_text(text, encoding="utf-8")

    (sandbox / ".gitignore").write_text("project/\nskill/\nagents/\n.claude/\nmail/\nmail-resolve.json\ndrive/\n",
                                        encoding="utf-8")

    index = f"cycletest-{model}-{sandbox.parent.name}"  # one per run, so two runs never share an index
    _qmd_index_file(index).unlink(missing_ok=True)
    for args in (["collection", "add", str(nb / "wiki")], ["embed"]):
        subprocess.run([*_qmd(), "--index", index, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    ctx["index"] = index
    ctx["env"] = {"WIKI_QMD_INDEX": index, "WIKI_QMD_CALLER": f"cycletest-{model}-{sandbox.parent.name}",
                  "PYTHONIOENCODING": "utf-8",
                  # every case: the email step, if a case turns it on, reads the sandbox's mail, never Gmail
                  "WIKI_GMAIL_FROM_DIR": str(sandbox / "mail"),
                  "WIKI_GMAIL_RESOLVE_MAP": str(sandbox / "mail-resolve.json"),
                  # and the Drive step reads the sandbox's folder, never Drive
                  "WIKI_DRIVE_FROM_DIR": str(sandbox / "drive")}
    return ctx


def _write_config(ctx: dict, email: bool, drive: bool = False) -> None:
    """The project config (and the same at the sandbox root); the email block only for email cases, the
    drive block only for the Drive case."""
    cfg = {"tool": "claude-code", "project_name": NOTEBOOK, "notebook": NOTEBOOK,
           "persona": "main", "registry": ctx["registry"].as_posix()}
    if email:
        cfg["email"] = {"enabled": True, "label": "...wiki-inbox", "done_label": "...wiki-inbox/read"}
    if drive:
        cfg["drive"] = {"enabled": True, "parent_folder": DRIVE_PARENT, "subfolder": NOTEBOOK}
    for d in (ctx["project"], ctx["sandbox"]):
        (d / ".claude").mkdir(parents=True, exist_ok=True)
        (d / ".claude" / "wiki-config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def teardown(ctx: dict) -> None:
    try:
        _rmtree(ctx["sandbox"])
    except OSError:
        pass
    _qmd_index_file(ctx["index"]).unlink(missing_ok=True)


def snapshot(ctx: dict) -> dict:
    nb = ctx["notebook"]
    if not nb.exists():
        return {}
    return {p.relative_to(nb).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in nb.rglob("*") if p.is_file()}


# ---------- per-case state ----------

def _prepare_quick(case: dict, ctx: dict) -> None:
    for sid in case["queue"]:
        url = _suite()["sources"][sid]["url"]
        p = _script(ctx, "wiki-list-add.py", "--topic", NOTEBOOK, "--source", url, "--added-by", "skilltest")
        if p.returncode != 0:
            raise RuntimeError(f"could not queue {url}: {p.stdout}{p.stderr}")


def _prepare_models(case: dict, ctx: dict) -> None:
    """Give the ingester's setting file this case's content. The pristine file is restored first,
    on every case, so no case leaks its setting into the next."""
    f = ctx["sandbox"] / "agents" / "wiki-ingester-config.json"
    keep = f.with_name(f.name + ".orig")
    if keep.is_file():
        shutil.copy2(keep, f)
    else:
        shutil.copy2(f, keep)
    if not case.get("ingester_config_set") and not case.get("ingester_config_broken"):
        return
    cfg = json.loads(f.read_text(encoding="utf-8"))
    cfg.update(case.get("ingester_config_set") or {})
    text = json.dumps(cfg, indent=2)
    if case.get("ingester_config_broken"):  # a trailing comma: strict JSON refuses it
        text = text.rstrip()[:-1].rstrip() + ",\n}\n"
    f.write_text(text, encoding="utf-8")


RESUME_ITEMS = [
    ("resume-one", "Handoff files between agent sessions", "agents,memory,handoff"),
    ("resume-two", "Trimming tool results before they re-enter the context", "context-engineering,tools"),
]


import random

BIG_SLUG = "ledger-handoff-field-guide"
BIG_URL = f"https://example.com/skilltest/{BIG_SLUG}"
SMALL_SLUG = "retry-budgets-for-agent-tools"
SMALL_URL = f"https://example.com/skilltest/{SMALL_SLUG}"
BIG_FACT = r"\b417\b"  # only in section 25 of 26

# One row per section: title, concept, purpose (an infinitive), 3 failures, 3 remedies, 2 artifacts, a metric.
# Written for the test: themed prose about AI agents (in the seed notebook's scope), built from per-section vocabularies.
_BIG_SECTIONS = [
    ("intake and framing", "the intake brief", "tell the receiving agent what the work is and what done looks like",
     ["a goal restated differently by each agent", "scope that grows during the handoff", "a missing definition of done"],
     ["writing the goal as one testable sentence", "listing explicit out-of-scope items", "attaching an acceptance check to every brief"],
     ["the intake brief", "the acceptance checklist"], "the share of briefs accepted without a clarifying question"),
    ("ledger structure", "the ledger schema", "fix which fields every entry must carry",
     ["free-text entries nobody can query", "fields added by one agent and ignored by the rest", "entries that mix decisions with chatter"],
     ["a versioned schema with required fields", "rejecting entries that fail validation", "separating decisions from working notes"],
     ["the schema file", "the validation report"], "the rejection rate at write time"),
    ("entry identifiers", "entry identifiers", "let any agent point at exactly one prior decision",
     ["two entries sharing an identifier", "identifiers reused after compaction", "references that name a topic instead of an entry"],
     ["content-derived identifiers", "monotonic counters per ledger", "reference checks at write time"],
     ["the identifier index", "the reference graph"], "the count of dangling references"),
    ("ownership transfer", "ownership transfer", "make it clear which agent is responsible for a task at any moment",
     ["two agents working one task", "a task nobody owns after a crash", "a transfer announced but never accepted"],
     ["an explicit accept step", "a single owner field with an expiry", "a transfer log with timestamps"],
     ["the ownership table", "the transfer log"], "the average time a task spends unowned"),
    ("acknowledgement rules", "acknowledgement rules", "confirm that the receiver has understood the handoff",
     ["silent drops", "acknowledgements sent before the receiver read the brief", "duplicate acknowledgements that hide a lost message"],
     ["acknowledging only after a read-back of the goal", "a bounded wait with escalation", "idempotent acknowledgement tokens"],
     ["the acknowledgement record", "the pending-ack list"], "the median time to acknowledge"),
    ("stale handoffs", "stale-handoff detection", "find work that was handed off and then forgotten",
     ["tasks that age quietly for weeks", "alerts so noisy that nobody reads them", "a sweep that reassigns work still in progress"],
     ["an age threshold per task class", "a sweep that only flags and never reassigns", "a weekly review of the oldest items"],
     ["the aging report", "the sweep log"], "the number of items older than the review window"),
    ("partial handoffs", "partial handoff", "cover work passed on before it is finished",
     ["half-written files treated as complete", "lost intermediate results", "a receiver that redoes finished steps"],
     ["recording completed steps beside the remaining ones", "checkpointing before every transfer", "marking unfinished outputs as drafts"],
     ["the checkpoint file", "the step list"], "the share of repeated steps after a handoff"),
    ("retries and idempotence", "idempotent operations", "let an agent repeat a step without doing harm",
     ["a payment sent twice", "duplicate tickets after a timeout", "a counter incremented on every replay"],
     ["idempotency keys on every write", "checking for the effect before repeating it", "separating planning from applying"],
     ["the operation journal", "the key store"], "the number of duplicate side effects per thousand operations"),
    ("ordering guarantees", "ordering", "decide which entry wins when two agents write at once",
     ["a later decision overwritten by an earlier one", "readers seeing entries out of order", "merge conflicts resolved by whichever agent wrote last"],
     ["per-task sequence numbers", "a single writer per task", "explicit supersedes links"],
     ["the sequence index", "the conflict log"], "the count of conflicting writes per week"),
    ("clock handling", "time handling", "keep timestamps comparable across agents and machines",
     ["clock skew that reorders events", "local times stored without a zone", "a date written into a prompt that invalidates cached context"],
     ["storing UTC instants with an explicit offset", "taking times from one service", "placing the current time late in the context"],
     ["the time source", "the timestamp convention"], "the largest observed skew between agents"),
    ("storage layout", "storage layout", "decide where durable state lives and how it is found",
     ["state scattered across temporary folders", "a single file that every agent rewrites", "paths that only one machine can resolve"],
     ["one folder per task with a fixed shape", "append-only files for the ledger", "relative paths from a documented root"],
     ["the folder map", "the layout note"], "the time a new engineer needs to find a task's state"),
    ("compaction", "compaction", "shrink old entries so the ledger stays readable",
     ["summaries that drop the reason for a decision", "compaction that deletes entries still referenced", "a ledger so long that agents skip it"],
     ["keeping the decision and its reason while dropping the chatter", "never compacting an entry with open references", "compacting on a schedule, not on demand"],
     ["the compaction log", "the archive folder"], "the ratio of compacted to original size"),
    ("audit trails", "the audit trail", "let a person reconstruct why the agents did what they did",
     ["actions with no recorded cause", "logs that omit the tool results", "an audit trail edited after the fact"],
     ["recording the cause beside every action", "storing tool results by reference", "making the trail append-only"],
     ["the audit log", "the evidence index"], "the share of actions with a recorded cause"),
    ("access scopes", "access scopes", "limit which agent may read or change which part of the ledger",
     ["a helper agent able to edit decisions", "secrets written into shared notes", "read access granted by default"],
     ["least-privilege roles per agent", "a separate store for secrets", "review of every scope change"],
     ["the role table", "the scope review"], "the number of agents holding write access to decisions"),
    ("failure drills", "failure drills", "test the handoff path before a real outage does",
     ["a ledger that cannot be restored", "recovery steps known to one person", "drills run once and never repeated"],
     ["restoring from a backup each quarter", "writing recovery steps as a checklist", "stopping an agent mid-handoff on purpose"],
     ["the drill checklist", "the restore report"], "the time to resume work after a simulated crash"),
    ("metrics", "handoff metrics", "show whether handoffs are getting better or worse",
     ["dashboards nobody owns", "averages that hide a long tail", "counts with no baseline"],
     ["reporting percentiles beside averages", "naming an owner for each metric", "recording a baseline before any change"],
     ["the metrics dashboard", "the weekly summary"], "the ninety-fifth percentile handoff duration"),
    ("alert thresholds", "alert thresholds", "decide when a person is paged about the ledger",
     ["pages for events that fix themselves", "thresholds copied from another system", "a silent failure with no alert at all"],
     ["paging only on sustained breaches", "tuning thresholds from a month of data", "adding one alert for the absence of events"],
     ["the alert rules", "the on-call notes"], "the share of alerts that needed action"),
    ("migration from notes files", "migration from notes files", "move an older agent from free-form notes to the ledger",
     ["notes imported without review", "two sources of truth during the switch", "history lost in the conversion"],
     ["converting one task at a time", "running the old and new paths side by side", "keeping the original notes as a read-only archive"],
     ["the migration plan", "the conversion report"], "the number of tasks still on the old notes"),
    ("multi-agent fan-out", "fan-out", "cover one task split across several parallel agents",
     ["workers repeating each other's searches", "results merged without checking for conflicts", "a coordinator that becomes the bottleneck"],
     ["giving each worker a distinct slice", "merging through a reviewer step", "capping the number of parallel workers"],
     ["the work split", "the merge report"], "the overlap between workers' outputs"),
    ("review cadence", "the review cadence", "set how often people read the ledger and the rules around it",
     ["reviews skipped when the team is busy", "review comments that never reach the schema", "rules that outlive the problem they solved"],
     ["a fixed monthly review", "turning review findings into schema changes", "retiring a rule when its trigger disappears"],
     ["the review notes", "the rule register"], "the number of rules retired each quarter"),
    ("naming conventions", "naming conventions", "keep tasks, agents and files easy to recognise",
     ["two tasks with the same name", "agent names that describe the model instead of the job", "file names that change on every edit"],
     ["names built from the job and a short date", "one name per agent role", "stable names with the version inside the file"],
     ["the naming guide", "the name registry"], "the count of ambiguous names found in review"),
    ("testing the ledger", "ledger tests", "check that the ledger behaves under concurrent and partial writes",
     ["tests that only cover the happy path", "fixtures copied from production data", "a test suite too slow to run often"],
     ["property tests on ordering and identifiers", "small synthetic fixtures", "a fast subset that runs on every change"],
     ["the test suite", "the fixture set"], "the share of ledger code covered by concurrent tests"),
    ("capacity planning", "capacity planning", "estimate how much state the agents will produce",
     ["growth discovered only when disks fill", "entries far larger than planned", "a read path that slows as the ledger grows"],
     ["projecting from the last quarter's growth", "setting a size limit per entry", "indexing the fields agents query most"],
     ["the growth forecast", "the size report"], "the daily growth of the ledger in entries"),
    ("operator checklists", "operator checklists", "give the person on duty a short list of steps for known problems",
     ["checklists too long to follow under stress", "steps that assume knowledge nobody wrote down", "checklists never updated after an incident"],
     ["keeping each checklist to one screen", "stating the expected result of every step", "updating the list in the incident review"],
     ["the runbook", "the incident notes"], "the time an operator needs to complete a checklist"),
    ("backpressure limits", "backpressure", "slow intake when the receivers cannot keep up",
     ["queues that grow without bound", "new work accepted while old work waits", "producers that cannot tell the queue is full"],
     ["a hard limit on pending handoffs", "telling producers to wait when the limit is reached", "draining the oldest items first"],
     ["the queue limit setting", "the backlog report"], "the length of the pending queue at peak"),
    ("closing guidance", "the set of habits that hold the rest together", "turn the earlier sections into daily practice",
     ["rules written down but not followed", "a ledger treated as paperwork", "improvements that stop after launch"],
     ["reviewing a few real handoffs each week", "treating every incident as a schema question", "keeping the guide short enough to reread"],
     ["this guide", "the team's own checklist"], "the number of incidents traced to a missing ledger entry"),
]

_BIG_TEMPLATES = [
    "{Cc} exists to {P}. Teams that neglect it usually find the gap through {F}, not through a design review.",
    "In one internal review of {N} agent sessions, {X} percent of the incidents traced back to {F}. The sessions that avoided it shared one habit in common: {R}.",
    "A practical rule for {C}: {R}. It costs little to adopt and it removes the ambiguity that otherwise shows up as {F}.",
    "Keep {A} next to the agent's other durable state and review it as often as the code. When it is neglected, the usual result is {F}.",
    "Measure {C} with {M}. A healthy deployment holds it steady across {N} consecutive days; a sudden change usually means {F} or a recent edit to {A}.",
    "Consider a support agent handing a case to a billing agent. Without a clear approach to {C}, the receiving agent repeats work and the customer sees {F}. With {R}, the same handoff finishes in {N} fewer turns.",
    "There is a trade-off. The fix is {R}, which reduces {F} but adds a step to every handoff and makes {A} larger. Most teams accept that cost once they have seen {F2} in production.",
    "Do not rely on the model to remember anything about {C}. The model's context is rebuilt each session, so whatever is not written to {A} is gone, and the usual result is {F}.",
    "When migrating an existing agent, start with {A}. Run the old and new paths side by side for {N} days, compare {M}, and only then switch over with {R}.",
    "Reviewers should ask three questions about {C}: what {A} says, who may change it, and what happens after {F}. An answer of 'the agent will work it out' counts as a finding.",
    "A reasonable share of design time for {C} is about {X} percent, because {F} is expensive to debug after launch and cheap to prevent with {R}.",
    "First versions of {C} usually fail through {F}. The second version fixes that with {R}, then fails differently, through {F2}; plan for at least two iterations.",
    "One team tracked {M} for {N} weeks before and after adopting {R}. The figure improved by roughly {X} percent, and the on-call engineers reported fewer incidents involving {F}.",
    "If {A} is out of date, new agents inherit the wrong assumptions about {C}. The cheapest defence is {R}, applied before the next release rather than after the next incident.",
    "Write down what {C} guarantees and what it does not. Readers of {A} should never have to guess whether {F} is possible, and the answer should be checked against {M}.",
    "A common objection is that {C} slows the team down. In practice the slowdown is a few minutes per task, while {F} can cost a full day of rework; the team that chose {R} came out ahead within {N} weeks.",
]


def _big_raw() -> str:
    """About 345 KB of written-for-the-test prose about handoffs and durable state in AI agents, in 26 headed
    sections; the fact the case looks for is only in section 25. Numbers filled in are 3 to 71, never 417."""
    rng = random.Random(7)
    out = ["# Field Guide to Handoffs and Durable State in Long-Running AI Agents", "",
           "A written-for-the-test guide to passing work between agent sessions through a shared ledger of decisions.", ""]
    for i, (title, c, purpose, fails, remedies, arts, metric) in enumerate(_BIG_SECTIONS, 1):
        out += [f"## Section {i}: {title}", ""]
        size = 0
        while size < 13200:
            sents = []
            for t in rng.sample(_BIG_TEMPLATES, 3):
                f, f2 = rng.sample(fails, 2)
                sents.append(t.format(C=c, Cc=c[0].upper() + c[1:], P=purpose, F=f, F2=f2, R=rng.choice(remedies),
                                      A=rng.choice(arts), M=metric, N=rng.randint(3, 60), X=rng.randint(4, 71)))
            para = " ".join(sents)
            out += [para, ""]
            size += len(para) + 1
        if i == 25:
            out += ["The Harrowgate ledger applies backpressure when a handoff queue holds 417 pending items; below that it accepts every handoff.", ""]
    text = "\n".join(out)
    if len(text) < 330_000 or re.search(BIG_FACT, text.replace("holds 417 pending items", "")):
        raise RuntimeError(f"big raw fixture is wrong: {len(text)} chars")
    return text


_SMALL_RAW = """# Retry budgets for agent tools

Give every tool call a retry budget instead of an open-ended loop. A budget of three attempts with doubling waits
(1 s, 2 s, 4 s) stops a flaky tool from stalling a whole session.

Count the budget per tool, not per task, so one failing search tool cannot consume the attempts another tool needs.

When the budget is spent, return the error to the model with the attempt count, and let it choose another route or stop.
Log each exhausted budget so a pattern of failures is visible across sessions.
"""


def _prepare_bigraw(case: dict, ctx: dict) -> None:
    """Two tickets in pending/, each with a raw_path to a raw written into raw/: one oversized, one ordinary."""
    nb = ctx["notebook"]
    for slug, url, text in ((BIG_SLUG, BIG_URL, _big_raw()), (SMALL_SLUG, SMALL_URL, _SMALL_RAW)):
        (nb / "raw" / f"{slug}.md").write_text(text, encoding="utf-8")
        p = _script(ctx, "wiki-list-add.py", "--topic", NOTEBOOK, "--source", url, "--added-by", "skilltest")
        if p.returncode != 0:
            raise RuntimeError(f"could not queue {url}: {p.stdout}{p.stderr}")
        for t in (nb / "_inbox" / "pending").glob("*.md"):
            body = t.read_text(encoding="utf-8")
            if url in body and "raw_path:" not in body:
                t.write_text(re.sub(r"\A---\r?\n", f"---\nraw_path: raw/{slug}.md\n", body, count=1), encoding="utf-8")


def _prepare_resume(ctx: dict, cycle_id: str) -> None:
    """An --ingest-only cycle interrupted after its ingest phase: both items staged,
    both tickets in done/, update.json written, the scratchpad saying so."""
    nb, fx = ctx["notebook"], HERE / "fixtures" / "resume"
    queued = []
    for name, title, tags in RESUME_ITEMS:
        url = f"https://example.com/skilltest/{name}"
        shutil.copy2(fx / "raw" / f"{name}.md", nb / "raw" / f"{name}.md")
        p = _script(ctx, "wiki-list-add.py", "--topic", NOTEBOOK, "--source", url, "--added-by", "skilltest")
        if p.returncode != 0:
            raise RuntimeError(p.stdout + p.stderr)
        p = _script(ctx, "wiki-update.py", "--topic", NOTEBOOK, "--source", str(fx / "bodies" / f"{name}.md"),
                    "--source-url", url, "--raw-path", f"raw/{name}.md", "--title", title, "--tags", tags,
                    "--folder", "research/best-practices", "--tier", "3", "--confidence", "medium",
                    "--ingested-by", "skilltest-fixture", "--staged", "--skip-integration", "--no-index")
        if p.returncode != 0:
            raise RuntimeError(f"could not stage {name}: {p.stdout}{p.stderr}")
        slug = re.search(r"^wiki_path=.*?([^/\\]+)\.md\s*$", p.stdout, re.M)
        queued.append({"priority": 3, "url": url, "slug": slug.group(1) if slug else name,
                       "reason": f"staged: {title}", "timestamp": ctx["started"]})
    for t in (nb / "_inbox" / "pending").glob("*.md"):
        if not t.name.startswith("_"):
            t.rename(nb / "_inbox" / "done" / t.name)
    _write_run(ctx, cycle_id, fx / "scratchpad.md", queued)


def _set_confirm(ctx: dict, value: bool) -> None:
    """The notebook's confirm_before_promote in the sandbox registry (the other registered project is kept)."""
    reg = json.loads(ctx["registry"].read_text(encoding="utf-8"))
    reg["notebooks"][NOTEBOOK]["confirm_before_promote"] = bool(value)
    ctx["registry"].write_text(json.dumps(reg, indent=2), encoding="utf-8")


def _prepare_promote_setting(case: dict, ctx: dict, cycle_id: str) -> None:
    """The resume fixture (two staged entries, tickets in done/, update pair). mode 'full' swaps in a --full
    scratchpad that resumes from Phase 2.6; mode 'quick' keeps the --ingest-only one (resume from 2.5)."""
    _prepare_resume(ctx, cycle_id)
    nb = ctx["notebook"]
    if case["mode"] == "full":
        run = nb / "_inbox" / "reports" / cycle_id[:10] / cycle_id
        tmpl = HERE / "fixtures" / "promote" / "scratchpad-full.md"
        (run / "scratchpad.md").write_text(tmpl.read_text(encoding="utf-8").format(
            date=cycle_id[:10], started=ctx["started"], notebook=NOTEBOOK, cycle_id=cycle_id), encoding="utf-8")
    ctx["promote_stems"] = {p.stem for p in (nb / "_inbox" / "proposed").glob("*.md")
                            if _is_entry(p.relative_to(nb).as_posix())}


def _find_staged(ctx: dict, root: str) -> dict:
    """The two fixture entries found under nb/<root> (wiki or _inbox/proposed), by source_url or file stem."""
    from _entry_checks import split_frontmatter
    nb = ctx["notebook"]
    urls = {_norm_url(f"https://example.com/skilltest/{n}"): t for n, t, _ in RESUME_ITEMS}
    found = {}
    base = nb / root
    for p in sorted(base.rglob("*.md")) if base.is_dir() else []:
        rel = p.relative_to(nb).as_posix()
        if not _is_entry(rel):
            continue
        fm, _ = split_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        u = _norm_url(fm.get("source_url"))
        if u in urls or p.stem in ctx.get("promote_stems", set()):
            found[u or p.stem] = rel
    return found


def _check_promote_setting(case: dict, add, res: list, ctx: dict, run_dir: Path) -> None:
    nb, cid = ctx["notebook"], ctx["cycle_id"]
    # The common checks below describe a staged-only run; this kind's point is whether entries move.
    drop = {"no --full-only step ran", "nothing filed straight into wiki/ (staged run)"}
    if case["mode"] == "full":
        drop.add("quick steps all wrote their pair")
    res[:] = [x for x in res if x["name"] not in drop]
    in_wiki, in_proposed = _find_staged(ctx, "wiki"), _find_staged(ctx, "_inbox/proposed")
    if case["confirm_before_promote"]:
        present = {p.stem for p in run_dir.glob("*.json")} if run_dir.is_dir() else set()
        add("premise: the resumed run went on as --full (a lint-semantic or claims step was written)",
            any(s.startswith(("lint-semantic", "claims")) for s in present), sorted(present))
        add("setting true: neither staged entry reached wiki/", not in_wiki, in_wiki)
        add("setting true: both staged entries still in _inbox/proposed/", len(in_proposed) == 2, in_proposed)
        rep = run_dir / f"{cid}-run-cycle-report.md"
        rtext = rep.read_text(encoding="utf-8", errors="replace").lower() if rep.is_file() else ""
        titles = [t.lower() for _, t, _ in RESUME_ITEMS]
        stems = [s.lower() for s in sorted(ctx.get("promote_stems", set()))]
        listed = sum(1 for t in titles if t in rtext)
        listed_by_slug = sum(1 for s in stems if s in rtext)
        add("setting true: the cycle report lists each waiting entry (by title or by file name)",
            len(stems) == 2 and max(listed, listed_by_slug) == 2, f"{listed} by title, {listed_by_slug} by file name")
        add("setting true: the cycle report says they are waiting to be promoted", "wait" in rtext,
            rtext[-300:] or "no report")
    else:
        add("setting false: both staged entries are in wiki/ by the end of the run", len(in_wiki) == 2, in_wiki)
        add("setting false: none left in _inbox/proposed/", not in_proposed, in_proposed)


def _write_run(ctx: dict, cycle_id: str, scratch_template: Path, queued: list[dict]) -> None:
    """A run folder interrupted after ingest: its scratchpad and the orchestrator's update pair."""
    run = ctx["notebook"] / "_inbox" / "reports" / cycle_id[:10] / cycle_id
    run.mkdir(parents=True, exist_ok=True)
    (run / "scratchpad.md").write_text(scratch_template.read_text(encoding="utf-8").format(
        date=cycle_id[:10], started=ctx["started"], notebook=NOTEBOOK, cycle_id=cycle_id), encoding="utf-8")
    n = len(queued)
    step = {"skill": "wiki-update", "cycle_id": cycle_id, "step": "update", "timestamp": ctx["started"],
            "status": "completed", "summary": {"items_attempted": n, "items_ingested": n, "items_skipped": 0,
                                               "items_deferred": 0},
            "queued": queued, "skipped": [], "deferred": [], "notes": "", "errors": []}
    (run / "update.json").write_text(json.dumps(step, indent=2), encoding="utf-8")
    rows = "\n".join(f"| P3 | {q['slug']} | {q['reason']} | {q['timestamp']} |" for q in queued)
    (run / "update.md").write_text(
        f"# Update — {cycle_id}\n\n**Status**: completed\n**Timestamp**: {ctx['started']}\n"
        f"**Summary**: {n} attempted, {n} ingested\n\n## Queued\n\n| Priority | URL/Slug | Reason | Timestamp |\n"
        f"|---|---|---|---|\n{rows}\n\n## Skipped\n\n(none)\n\n## Deferred\n\n(none)\n\n## Notes\n\n\n## Errors\n\n",
        encoding="utf-8")


TRIAGE_README = """---
buckets:
  - folder: main
    purpose: Context engineering, agent memory, and anything relevant that fits no other bucket
    reader: cycletest
  - folder: other
    purpose: AI agent security (prompt injection, tool misuse, data exfiltration)
    reader: other-bot
---

# Intake buckets (test)
"""


def _prepare_triage(case: dict, ctx: dict) -> None:
    intake = ctx["notebook"] / "_inbox" / "intake"
    intake.mkdir(parents=True, exist_ok=True)
    (intake / "README.md").write_text(TRIAGE_README, encoding="utf-8")
    _prepare_quick(case, ctx)


CHECKER_TITLE = "Keeping an agent's context small: eight techniques"


def _prepare_checker(ctx: dict, cycle_id: str) -> None:
    """A run interrupted after its staging check, with one staged entry from a 21-minute
    transcript: the entry drops the ninth technique and says 70% where the talk says a third."""
    nb, fx = ctx["notebook"], HERE / "fixtures" / "checker"
    shutil.copy2(fx / "talk-transcript.md", nb / "raw" / "talk-transcript.md")
    url = "https://www.youtube.com/watch?v=skilltest01"
    p = _script(ctx, "wiki-update.py", "--topic", NOTEBOOK, "--source", str(fx / "entry-body.md"),
                "--source-url", url, "--raw-path", "raw/talk-transcript.md", "--title", CHECKER_TITLE,
                "--tags", "context-engineering,agents,youtube", "--folder", "research/best-practices",
                "--tier", "3", "--confidence", "medium", "--ingested-by", "skilltest-fixture",
                "--staged", "--skip-integration", "--no-index")
    if p.returncode != 0:
        raise RuntimeError(f"could not stage the checker entry: {p.stdout}{p.stderr}")
    staged = sorted((nb / "_inbox" / "proposed").glob("*.md"))
    ctx["checker_slug"] = staged[0].stem if staged else ""
    _write_run(ctx, cycle_id, fx / "scratchpad.md", [{"priority": 3, "url": url, "slug": ctx["checker_slug"],
                                                     "reason": "staged from a 21-minute talk",
                                                     "timestamp": ctx["started"]}])


KOSHY = "https://medium.com/@koshy/restarting-your-agent-is-not-repairing-it-0a1b2c3d4e5f"
ANA = "https://medium.com/@ana.k/giving-a-coding-agent-memory-that-survives-a-restart-1a2b3c4d5e6f"
LETTER = "https://skilltest-letters.substack.com/p/what-prompt-caching-changes-for-agents"  # the full-text email
REPO = "https://github.com/skilltest-org/agent-scratchpad-memory"
HUSTLE = "https://medium.com/@hustle.daily/i-made-10000-a-month-with-ai-side-hustles-9f8e7d6c5b4a"
DOOM = "https://medium.com/@listicles/10-websites-better-than-doomscrolling-8e7d6c5b4a3f"
BREAD = "https://example.org/blog/the-perfect-sourdough-starter"
ON_TOPIC = {KOSHY, ANA, LETTER, REPO}
OFF_TOPIC = {HUSTLE, DOOM, BREAD}
# A signed, first-hand essay, so a reader judging it sees a real newsletter: one paragraph repeated twelve times
# read as filler, and Opus rightly skipped it once (2026-10-04). 700+ words, few links: a full-text email.
_ESSAY_PARAS = [
    "By Dana Whitfield, staff engineer on our agent platform. Over the last six weeks we moved four production "
    "agents onto prompt caching, and the bill was the least interesting thing we learned. This letter is what we "
    "measured, what surprised us, and the three layout rules we now hold every agent to.",
    "The first surprise was how little of our context was actually stable. We assumed the system prompt and tool "
    "definitions never changed between turns. In practice two of the four agents rebuilt their tool list on every "
    "turn, sorting tools by recent use, so the cached prefix ended after the system prompt and every turn paid full "
    "price for twenty kilobytes of tool schema. Sorting the tools once, at session start, raised our cache hit rate "
    "from 31 percent to 88 percent on those two agents without touching anything else.",
    "The second surprise was the timestamp. One agent put the current time in its system prompt so it could answer "
    "date questions. That single line, changing every minute, invalidated the whole prefix. We moved the time into "
    "the last user message, where it belongs, and the agent answered date questions exactly as well as before.",
    "Third, the scratchpad. Our coding agent keeps a running scratchpad of what it has tried. We had placed it near "
    "the top, beside the instructions, because it felt important. Every edit to it broke the cache for everything "
    "after it, including the long reference documents. Moving the scratchpad after the cache breakpoint cut the "
    "agent's median latency on long sessions by about a third, and its success rate on our internal task suite did "
    "not move.",
    "Here are the rules we now apply. One: order the context from most stable to least stable, and treat that order "
    "as part of the agent's design rather than an accident of how the code assembled it. Two: anything derived from "
    "the clock, the user, or the last tool call goes after the breakpoint, never before it. Three: when a stable "
    "block must change, change it between sessions, not mid-session, and accept the one cold turn that follows.",
    "We also learned where caching does not help. Short sessions of two or three turns rarely reuse a prefix long "
    "enough to matter, and agents that fan out to many parallel workers each pay their own cold start unless the "
    "workers share an identical prefix. For the parallel case we now give every worker the same opening block, "
    "byte for byte, and put the per-worker instructions after it. That alone recovered most of the savings we had "
    "assumed we were getting.",
    "A word on measurement. The provider reports cached and uncached input tokens per request, and we log both. "
    "Before this project nobody looked at the split. Now it sits on the same dashboard as latency and task success, "
    "and a drop in the cache hit rate pages the owning team the way an error spike does. Two regressions this month "
    "were caught that way within a day, both caused by a well-meant edit near the top of a system prompt.",
    "Retrieval needed its own rule. Our support agent pulls three to five documents per question. We used to insert "
    "them right after the system prompt, which put a different block of text at the front of every request. Now the "
    "retrieved documents go after the stable reference material and before the conversation, inside the volatile "
    "part, and the stable part stays byte-identical across every question. The documents themselves are not cached, "
    "but everything before them is, and that is most of the tokens.",
    "Finally, tool results. Some of our tools return large payloads, a full file listing or a long log. We trim them "
    "before they enter the context and keep the full output on disk with a pointer the agent can follow. That is "
    "good practice for any agent, but caching made the cost visible: a single forty-kilobyte log placed early in a "
    "session was being re-sent uncached on every later turn, because everything after it had shifted.",
    "If you take one thing from this letter, make it this: prompt caching is not a billing setting you switch on. "
    "It is a constraint on how you lay out context, and it rewards the same discipline that makes an agent easier "
    "to debug. Stable things first, volatile things last, and measure the split so you notice when someone breaks "
    "it. Next week: what we changed in our evaluation harness so it caches too.",
]
_ESSAY = "</p><p>".join(_ESSAY_PARAS)


def _eml(subject: str, sender: str, html: str) -> bytes:
    from email.message import EmailMessage
    m = EmailMessage()
    m["Subject"], m["From"], m["To"] = subject, sender, "user@example.com"
    m["Date"] = "Thu, 02 Oct 2026 12:50:00 +0000"
    m.set_content("(html only)")
    m.add_alternative(html, subtype="html")
    return bytes(m)


def _prepare_email(ctx: dict) -> None:
    """Three emails in sandbox/mail/ and the redirect map; the project config turns email on."""
    mail = ctx["sandbox"] / "mail"
    _rmtree(mail)
    mail.mkdir(parents=True)
    digest = f"""<html><body><p>Today's highlights</p>
<a href="https://medium.com/@koshy?source=email-digest">Koshy</a>
<a href="{KOSHY}?source=email-abc-digest">Restarting Your Agent Is Not Repairing It</a>
<a href="{ANA}?source=email-abc-digest">Giving a coding agent memory that survives a restart</a>
<a href="{HUSTLE}?source=email-abc-digest">I Made $10,000 a Month With AI Side Hustles</a>
<a href="{DOOM}?source=email-abc-digest">10 Websites Better Than Doomscrolling</a>
<a href="https://medium.com/me/email-settings">Email settings</a>
<a href="https://help.medium.com/hc/en-us/articles/unsubscribe">Unsubscribe</a></body></html>"""
    letter = f"""<html><body><a href="https://substack.com/redirect/view-online">View in browser</a>
<h1>What prompt caching changes for agents</h1><p>{_ESSAY}</p>
<a href="https://skilltest-letters.substack.com/subscribe">Subscribe</a></body></html>"""
    roundup = """<html><body><p>Links of the week</p>
<a href="https://api.daily.dev/r/mem1">agent-scratchpad-memory: a scratchpad memory layer for coding agents</a>
<a href="https://api.daily.dev/r/bread">The perfect sourdough starter</a>
<a href="https://app.daily.dev/settings/notifications">Manage your notifications</a></body></html>"""
    for name, data in (("m1", _eml("Restarting Your Agent Is Not Repairing It | Koshy", "Medium Daily Digest <noreply@medium.com>", digest)),
                       ("m2", _eml("What prompt caching changes for agents", "Skilltest Letters <letters@substack.com>", letter)),
                       ("m3", _eml("Your weekly links", "daily.dev <informer@daily.dev>", roundup))):
        (mail / f"{name}.eml").write_bytes(data)
    (ctx["sandbox"] / "mail-resolve.json").write_text(json.dumps({
        "https://substack.com/redirect/view-online": LETTER,
        "https://api.daily.dev/r/mem1": REPO,
        "https://api.daily.dev/r/bread": BREAD,
    }), encoding="utf-8")


DRIVE_PARENT = "__SKILLTEST DRIVE"  # in no real Drive: a run that missed $WIKI_DRIVE_FROM_DIR finds nothing to move
DRIVE_LINK = "https://example.org/skilltest/handoff-files-between-agent-sessions"
DRIVE_SOURCES = ("Agent memory survey.pdf", "Orchestrator patterns.pptx", "Screenshot 2026-10-02.png")
DRIVE_LEFT = ("remember this.txt", "voice memo.mp3")
DRIVE_TOKEN = Path.home() / ".config" / "wiki-cycle" / "drive-token.json"


def _prepare_drive(ctx: dict) -> None:
    """The test Drive folder: a link capture, three files that are the source, two the cycle leaves."""
    sys.path.insert(0, str(HERE.parents[1] / "scripts"))
    from _samples import PNG, tiny_pdf, tiny_pptx
    root = ctx["sandbox"] / "drive"
    _rmtree(root)
    scan = root / DRIVE_PARENT / NOTEBOOK
    scan.mkdir(parents=True)
    (scan / "handoff notes.txt").write_text(f"Handoff files between agent sessions {DRIVE_LINK}", encoding="utf-8")
    (scan / DRIVE_SOURCES[0]).write_bytes(tiny_pdf("A survey of memory architectures for LLM agents"))
    (scan / DRIVE_SOURCES[1]).write_bytes(tiny_pptx("Orchestrator and worker agents: when to split a task"))
    (scan / DRIVE_SOURCES[2]).write_bytes(PNG)
    (scan / DRIVE_LEFT[0]).write_text("look at the agent memory papers again next week", encoding="utf-8")
    (scan / DRIVE_LEFT[1]).write_bytes(b"ID3")


def _mtime(p: Path):
    return p.stat().st_mtime_ns if p.exists() else None


def _commit_fixture(ctx: dict, case_id: str) -> None:
    """Commit this case's starting state. One repo per sandbox: deleting and re-creating
    .git between cases fails on Windows (a half-deleted .git broke the next `git add`)."""
    if not (ctx["sandbox"] / ".git").is_dir():
        for args in (["init", "-q"], ["config", "user.name", "skilltest"],
                     ["config", "user.email", "skilltest@example.com"], ["config", "core.autocrlf", "false"],
                     ["config", "core.longpaths", "true"]):
            _git(ctx, *args)
    _git(ctx, "add", "-A")
    _git(ctx, "commit", "-q", "--allow-empty", "-m", f"fixture: {case_id}")
    ctx["fixture_commit"] = _git(ctx, "rev-parse", "HEAD").strip()


# ---------- prompts ----------

HEADER = """You are running an automated test of the wiki-cycle skill. The skill under test is at {skill}/SKILL.md. Read it and follow it exactly, as if the user had typed the command below in this project. Do not use any installed copy of any skill.

Every skill it names is rendered beside it: /wiki-update is {skills}/wiki-update/SKILL.md, /wiki-report is {skills}/wiki-report/SKILL.md, and so on for wiki-triage, wiki-refresh, wiki-claims, wiki-discover, wiki-lint, wiki-promote, wiki-list and wiki-search. Where the skill says to run one of them, read that file and follow it; the Skill tool is not available. The wiki-ingester and wiki-checker agents are this project's own (their definitions are in .claude/agents/); their config files are at {agents}. This session has no Discord channel and no browser.

The notebook is `{notebook}`, this project's notebook, at {nb}. The notebooks repository (git) is {sandbox}. Run scripts as the skill writes them, `uv run --project <scripts dir> python <path> ...` or `node <path> ...`, with no environment-variable prefix, and write only inside {sandbox}. The user started this run and will read your report, but cannot answer questions while it runs: where the skill says to ask or confirm, make the choice the skill gives for a session that cannot ask, and say what you chose.

The user typed: """


def prompt(case: dict, ctx: dict) -> str:
    sys.path.insert(0, str(ctx["scripts"]))
    from _wiki_config import now_stamp
    _seed(ctx)
    ctx["started"] = now_stamp()
    cycle_id = f"{_today(ctx)}-01"
    ctx["cycle_id"] = cycle_id
    if case["kind"] in ("ingest-only", "scratch", "models"):
        _prepare_quick(case, ctx)
    elif case["kind"] == "triage":
        _prepare_triage(case, ctx)
    elif case["kind"] == "resume":
        _prepare_resume(ctx, cycle_id)
    elif case["kind"] in ("checker", "checker-promote"):
        _prepare_checker(ctx, cycle_id)
    elif case["kind"] == "retry":
        _prepare_retry(case, ctx)
    elif case["kind"] == "bigraw":
        _prepare_bigraw(case, ctx)
    elif case["kind"] == "synthesis":
        _prepare_synthesis(case, ctx)
    elif case["kind"] == "promote-setting":
        _prepare_promote_setting(case, ctx, cycle_id)
    elif case["kind"] in ("model-mix", "model-ask"):
        _prepare_local_items(case, ctx)
    elif case["kind"] == "scope":
        _prepare_scope(case, ctx, cycle_id)
    elif case["kind"] == "hub":
        _prepare_hub(case, ctx, cycle_id)
    elif case["kind"] == "checker-gate":
        _prepare_checker_gate(case, ctx, cycle_id)
    elif case["kind"] == "lint-all":
        _prepare_lint_all(case, ctx)
    elif case["kind"] == "youtube-batch":
        _prepare_youtube(case, ctx)
    _write_config(ctx, email=case["kind"] == "email", drive=case["kind"] == "drive")
    if case["kind"] == "email":
        _prepare_email(ctx)
    if case["kind"] == "drive":
        _prepare_drive(ctx)
    ctx["drive_token_before"] = _mtime(DRIVE_TOKEN)
    ctx["gmail_token_before"] = (Path.home() / ".config" / "wiki-cycle" / "gmail-token.json").exists()
    _prepare_models(case, ctx)
    _set_confirm(ctx, case.get("confirm_before_promote", True))
    _commit_fixture(ctx, case["id"])
    ctx["fixture_files"] = snapshot(ctx)
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), skills=ctx["skill_dir"].parent.as_posix(),
                         agents=(ctx["sandbox"] / "agents").as_posix(), notebook=NOTEBOOK,
                         nb=ctx["notebook"].as_posix(), sandbox=ctx["sandbox"].as_posix()) \
        + case["say"].format(cycle_id=cycle_id)


# ---------- checks ----------

def _is_entry(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1].lower()
    if not rel.endswith(".md") or name in MACHINE_FILES or name.startswith("_"):
        return False
    if rel.startswith("_inbox/proposed/"):
        return True
    return rel.startswith("wiki/") and not rel.startswith("wiki/sessions/")


def _norm_url(u) -> str:
    return str(u or "").strip().strip('"').strip("'").rstrip("/").lower().replace("://www.", "://")


def _tickets(folder: Path) -> list[str]:
    """Queue tickets only: a file carrying a `source:` line, the rule wiki-dequeue.py uses. /wiki-discover moves
    its checklist (`<date>-discovery.md`) into done/ after the review, as its skill says; that is not a ticket
    (2026-10-04: three email cases failed on it)."""
    return sorted(p.name for p in folder.glob("*.md") if not p.name.startswith(("_", "README"))
                  and re.search(r"^source:", p.read_text(encoding="utf-8", errors="replace"), re.M))


def _agent_calls(run: dict) -> list[dict]:
    return [c["input"] for c in run["tool_calls"] if c["name"] in ("Agent", "Task")]


def _scratch_status(text: str) -> str:
    m = re.search(r"\*\*Status\*\*:\s*([a-z_]+)", text)
    return m.group(1) if m else ""


def add_denials(add, run: dict) -> None:
    """Denials that point at the harness fail the case; two kinds are expected and counted
    apart: the blocked Skill tool (on purpose, see DISALLOWED_TOOLS) and the machine's
    global read-guard hook refusing a partial read of a document, which the session
    then reads whole (all four runs of the first baseline, 2026-09-24)."""
    errs = run.get("error_texts") or {}
    guard, skill, other = [], [], []
    for d in run["result"].get("permission_denials") or []:
        d = d if isinstance(d, dict) else {"tool_name": str(d)}
        if d.get("tool_name") == "Skill":
            skill.append(d)
        elif "read-guard:" in str(errs.get(d.get("tool_use_id"), "")):
            guard.append(d)
        else:
            other.append(d)
    add("no permission denials (read-guard and the blocked Skill tool counted apart)", not other,
        f"other: {[d.get('tool_name') for d in other]}; read-guard: {len(guard)}; Skill: {len(skill)}")


def _check_email(case: dict, add, ctx: dict, run_dir: Path, stext: str, text: str, workers: list) -> None:
    nb, mail = ctx["notebook"], ctx["sandbox"] / "mail"
    sys.path.insert(0, str(ctx["scripts"]))
    from _entry_checks import split_frontmatter
    token = Path.home() / ".config" / "wiki-cycle" / "gmail-token.json"
    add("never reached the real mailbox (no Gmail sign-in)",
        ctx.get("gmail_token_before") or not token.exists(), "a gmail-token.json appeared")
    add("no ingest worker spawned (--discover-only)", not workers, [a.get("description") for a in workers])
    step_file = run_dir / "email-fetch.json"
    try:
        step = json.loads(step_file.read_text(encoding="utf-8")) if step_file.is_file() else {}
    except json.JSONDecodeError:
        step = {}
    cands = step.get("candidates") or []
    add("email-fetch.json written with the candidates", bool(cands), step_file.name)
    by_url = {_norm_url(c["url"]): c for c in cands}
    add("every on-topic and off-topic link is a candidate",
        all(_norm_url(u) in by_url for u in ON_TOPIC | OFF_TOPIC), sorted(by_url))
    rv_file = run_dir / "email-review.json"
    try:
        review = json.loads(rv_file.read_text(encoding="utf-8")) if rv_file.is_file() else {}
    except json.JSONDecodeError:
        review = {}
    undecided = [c["n"] for c in cands if (review.get(str(c["n"])) or {}).get("decision") not in ("recommend", "skip")
                 or not str((review.get(str(c["n"])) or {}).get("reason", "")).strip()]
    add("email-review.json: a decision and a reason for every candidate", review and not undecided, undecided)
    rec = {_norm_url(c["url"]) for c in cands if (review.get(str(c["n"])) or {}).get("decision") == "recommend"}
    on, off = {_norm_url(u) for u in ON_TOPIC}, {_norm_url(u) for u in OFF_TOPIC}
    add("every off-topic link skipped", not (rec & off), sorted(rec & off))
    add("at least 3 of the 4 on-topic links recommended", len(rec & on) >= 3, sorted(rec & on))
    add("scratchpad records the email step", bool(re.search(r"1\.1[^\n]*email", stext, re.I)))
    pending = {}
    for t in (nb / "_inbox" / "pending").glob("*.md"):
        if not t.name.startswith("_"):
            fm, _ = split_frontmatter(t.read_text(encoding="utf-8"))
            pending[_norm_url(fm.get("source"))] = fm
    left = sorted(p.name for p in mail.glob("*.eml"))
    archived = sorted(p.name for p in (mail / "read").glob("*.eml")) if (mail / "read").is_dir() else []
    if case.get("approve"):
        add("exactly the recommended links queued", set(pending) == rec, {"queued": sorted(pending), "rec": sorted(rec)})
        letter = pending.get(_norm_url(LETTER)) or {}
        rp = str(letter.get("raw_path") or "")
        add("the full-text email queued with its raw in raw/", bool(rp) and (nb / rp).is_file(), rp or "no raw_path")
        add("every email moved to the done label", not left and len(archived) == 3, {"left": left, "done": archived})
        add("email-fetch.json records the review", step.get("reviewed") is True
            and (step.get("summary") or {}).get("queued") == len(rec), step.get("summary"))
    else:
        add("nothing queued without the user's answer", not pending, sorted(pending))
        add("the emails stay in the label", len(left) == 3 and not archived, {"left": left, "done": archived})
        add("the report gives the recommendations", "recommend" in text, "no 'recommend' in the reply")


def _check_drive(add, ctx: dict, run_dir: Path, text: str, workers: list) -> None:
    nb, scan = ctx["notebook"], ctx["sandbox"] / "drive" / DRIVE_PARENT / NOTEBOOK
    sys.path.insert(0, str(ctx["scripts"]))
    from _entry_checks import split_frontmatter
    add("never reached the real Drive (its token untouched)", _mtime(DRIVE_TOKEN) == ctx.get("drive_token_before"))
    add("no ingest worker spawned (--discover-only)", not workers, [a.get("description") for a in workers])
    step_file = run_dir / "drive-fetch.json"
    try:
        step = json.loads(step_file.read_text(encoding="utf-8")) if step_file.is_file() else {}
    except json.JSONDecodeError:
        step = {}
    add("drive-fetch.json written by the script", step.get("step") == "drive-fetch", step_file.name)
    pending = {}
    for t in (nb / "_inbox" / "pending").glob("*.md"):
        if not t.name.startswith("_"):
            fm, _ = split_frontmatter(t.read_text(encoding="utf-8"))
            pending[str(fm.get("source") or "")] = fm
    add("the link capture's URL queued", DRIVE_LINK in pending, sorted(pending))
    with_raw = [fm for src, fm in pending.items() if "drive.google.com" in src and fm.get("raw_path")
                and (nb / str(fm["raw_path"])).is_file()]
    add("the PDF, the deck and the image queued, each with its raw", len(with_raw) == 3 and len(pending) == 4,
        sorted(pending))
    left = sorted(p.name for p in scan.iterdir() if p.is_file()) if scan.is_dir() else []
    done = scan / "_completed" / ctx["cycle_id"]
    moved = sorted(p.name for p in done.iterdir()) if done.is_dir() else []
    add("handled files moved to _completed/<cycle_id>/; the note and the memo stay",
        left == sorted(DRIVE_LEFT) and len(moved) == 4, {"left": left, "moved": moved})
    report = run_dir / f"{ctx['cycle_id']}-run-cycle-report.md"
    rtext = report.read_text(encoding="utf-8", errors="replace") if report.is_file() else ""
    add("the cycle report names both files left in Drive", all(n in rtext for n in DRIVE_LEFT),
        [n for n in DRIVE_LEFT if n not in rtext])
    add("the reply tells the user what was left in Drive", all(n.split(".")[0] in text for n in DRIVE_LEFT),
        [n for n in DRIVE_LEFT if n.split(".")[0] not in text])


import http.server
import threading

RETRY_OWNER = {"main": NOTEBOOK, "other": "other"}  # intake bucket folder -> the notebook of its reader


def _serve_stub(status: int, body: str, retry_after=None):
    """A loopback page that answers every request with one status. srv.hits counts requests."""
    class H(http.server.BaseHTTPRequestHandler):
        def _send(self):
            srv.hits.append(self.path)
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            if retry_after:
                self.send_header("Retry-After", str(retry_after))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)
        do_GET = do_HEAD = _send

        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    srv.hits = []
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _task_dir(ctx: dict, nb_name: str) -> Path:
    base = ctx["notebook"] if nb_name == NOTEBOOK else ctx["sandbox"] / "notebooks" / nb_name
    return base / "wiki" / "tasks"


def _cards(ctx: dict, nb_name: str) -> set:
    d = _task_dir(ctx, nb_name)
    return {p.name for p in d.glob("*.md") if p.name.upper() not in ("ORDER.MD", "README.MD")
            and not p.name.startswith("_")} if d.is_dir() else set()


def _prepare_retry(case: dict, ctx: dict) -> None:
    """The intake buckets (main: cycletest, other: other-bot), other-bot's project folder, empty task lists, one
    live queued source, and one queued source that is a loopback page answering with the case's status."""
    st = case["stub"]
    srv = _serve_stub(st["status"], st["body"], st.get("retry_after"))
    ctx["stub_srv"] = srv
    ctx["stub_url"] = f"http://127.0.0.1:{srv.server_address[1]}{st['path']}"
    ctx["stub_tail"] = st["path"].rsplit("/", 1)[-1]
    _prepare_triage(case, ctx)  # intake README with both buckets + the live source(s)
    p = _script(ctx, "wiki-list-add.py", "--topic", NOTEBOOK, "--source", ctx["stub_url"], "--added-by", "skilltest")
    if p.returncode != 0:
        raise RuntimeError(f"could not queue {ctx['stub_url']}: {p.stdout}{p.stderr}")
    op = ctx["sandbox"] / "other-project"
    (op / ".claude").mkdir(parents=True, exist_ok=True)
    (op / ".claude" / "wiki-config.json").write_text(json.dumps({
        "tool": "claude-code", "project_name": "other", "notebook": "other", "persona": "main",
        "registry": ctx["registry"].as_posix()}, indent=2), encoding="utf-8")
    gi = ctx["sandbox"] / ".gitignore"
    if "other-project/" not in gi.read_text(encoding="utf-8"):
        gi.write_text(gi.read_text(encoding="utf-8") + "other-project/\n", encoding="utf-8")
    _rmtree(_task_dir(ctx, "other"))
    for name in (NOTEBOOK, "other"):
        d = _task_dir(ctx, name)
        d.mkdir(parents=True, exist_ok=True)
        if not (d / "ORDER.md").exists():
            (d / "ORDER.md").write_text("# Task order\n", encoding="utf-8")
    ctx["cards_before"] = {n: _cards(ctx, n) for n in (NOTEBOOK, "other")}


def _check_retry(case: dict, add, ctx: dict, run_dir: Path, text: str) -> None:
    nb = ctx["notebook"]
    tail, cid, today = ctx["stub_tail"], ctx["cycle_id"], _today(ctx)
    srv = ctx["stub_srv"]
    add("the cycle tried to fetch the stubbed page", bool(srv.hits), "no request reached the stub")

    def fm_text(t: str) -> str:
        m = re.match(r"^---\n(.*?)\n---", t.replace("\r\n", "\n"), re.S)
        return m.group(1) if m else ""

    def retry_value(t: str):
        m = re.search(r"^retry:[ \t]*(.*(?:\n[ \t]+.*)*)", fm_text(t), re.M)
        return m.group(1).strip() if m else None

    tickets = []  # (folder, name, text) for every queue ticket in the notebook
    for folder in ("pending", "done", *[f"intake/{b}" for b in RETRY_OWNER]):
        d = nb / "_inbox" / folder
        for p in sorted(d.glob("*.md")) if d.is_dir() else []:
            t = p.read_text(encoding="utf-8", errors="replace")
            if re.search(r"^source:", t, re.M):
                tickets.append((folder, p.name, t))
    stub_t = [x for x in tickets if tail in x[2] or ctx["stub_url"] in x[2]]
    other_cards = {n: _cards(ctx, n) - ctx["cards_before"][n] for n in (NOTEBOOK, "other")}
    report = run_dir / f"{cid}-run-cycle-report.md"
    rtext = report.read_text(encoding="utf-8", errors="replace") if report.is_file() else ""

    if case.get("no_retry"):
        marked = [f"{f}/{n}" for f, n, t in tickets if retry_value(t) is not None]
        add("no ticket carries a retry: field (a page no fetcher can get is not a retry)", not marked, marked)
        add("no task card added to either reader's list", not any(other_cards.values()), other_cards)
        low = (rtext + "\n" + text).lower()
        add("the report or reply names the save-as-PDF path", "pdf" in low, "no 'pdf' in the report or the reply")
        add("the report or reply names the blocked item", tail.lower() in low or "127.0.0.1" in low,
            "the blocked page is not named")
        return

    add("the failed ticket is still in an intake bucket (not pending, not done)",
        bool(stub_t) and all(f.startswith("intake/") for f, _, _ in stub_t), [(f, n) for f, n, _ in stub_t])
    if not stub_t or not stub_t[0][0].startswith("intake/"):  # failed above; no bucket to find an owner by
        return
    folder, _, ttext = stub_t[0]
    val = retry_value(ttext)
    add("the ticket carries a retry: field", bool(val), val)
    val = val or ""
    add("retry: names the cycle", cid in val, val[:200])
    add("retry: names the date", today in val, val[:200])
    rest = val.replace(cid, "").replace(today, "")
    add("retry: names a reason (words beyond the date and cycle)", len(re.findall(r"[A-Za-z]", rest)) >= 6, val[:200])
    others = [(f, n) for f, n, t in tickets if t is not ttext and retry_value(t) is not None]
    add("no other ticket is marked for retry (the ingested one is not)", not others, others)

    owner = RETRY_OWNER[folder.split("/", 1)[1]]
    other_owner = ({NOTEBOOK, "other"} - {owner}).pop()
    mine = sorted(other_cards[owner])
    add(f"exactly one new task card, in the owner's ({owner}) list", len(mine) == 1, other_cards)
    add("no new card in the other reader's list", not other_cards[other_owner], other_cards[other_owner])
    ctext = (_task_dir(ctx, owner) / mine[0]).read_text(encoding="utf-8", errors="replace") if len(mine) == 1 else ""
    add("the card says retry and names the cycle", bool(re.search(r"retry", ctext, re.I)) and cid in ctext,
        ctext[:200])
    add("the card names the bucket", folder.split("/", 1)[1] in ctext.lower(), ctext[:200])
    add("the card lists the failed item", tail in ctext or ctx["stub_url"] in ctext, ctext[:200])
    add("the card does not list the ingested source",
        "simonwillison.net/2025/jun/27" not in ctext.lower(), ctext[:200])


SYNTH_FX = HERE / "fixtures" / "synthesis"
SYNTH_SLUG = "trimming-tool-results-before-reuse"
SYNTH_CANON = "wiki/project/best-practices"


def _prior_synthesis(ctx: dict, cycle_id: str, timestamp: str, status: str) -> None:
    """An earlier run folder holding only a synthesis pair, as the scope script reads it."""
    run = ctx["notebook"] / "_inbox" / "reports" / cycle_id[:10] / cycle_id
    run.mkdir(parents=True, exist_ok=True)
    step = {"skill": "wiki-cycle", "cycle_id": cycle_id, "step": "synthesis", "timestamp": timestamp,
            "status": status, "summary": {"entries_in_scope": 0}, "queued": [], "skipped": [], "deferred": [],
            "notes": "test fixture: an earlier synthesis", "errors": []}
    (run / "synthesis.json").write_text(json.dumps(step, indent=2), encoding="utf-8")
    (run / "synthesis.md").write_text(
        f"# Synthesis - {cycle_id}\n\n**Status**: {status}\n**Timestamp**: {timestamp}\n", encoding="utf-8")


def _canon_pages(cdir: Path) -> dict:
    """The best-practices pages by name and bytes. Machine files (names starting with '_', such as the
    _INDEX.md the cycle's index step writes into every wiki folder) and README.md are not pages."""
    if not cdir.is_dir():
        return {}
    return {p.name: p.read_bytes() for p in cdir.glob("*")
            if p.is_file() and not p.name.startswith("_") and p.name.lower() != "readme.md"}


def _prepare_synthesis(case: dict, ctx: dict) -> None:
    """Best-practices pages, an earlier synthesis, and one queued source. 'new': a research entry dated after
    the last completed synthesis (and a newer awaiting_approval one that must not be the cut-off). 'none': the
    last completed synthesis is later than every entry in wiki/, so only the staged entry will be new."""
    nb = ctx["notebook"]
    shutil.copytree(SYNTH_FX / "project", nb / "wiki" / "project", dirs_exist_ok=True)
    if case["synthesis"] == "new":
        shutil.copy2(SYNTH_FX / "research" / f"{SYNTH_SLUG}.md",
                     nb / "wiki" / "research" / "best-practices" / f"{SYNTH_SLUG}.md")
        _prior_synthesis(ctx, "2026-02-01-01", "2026-02-01T09:00:00+00:00", "completed")
        _prior_synthesis(ctx, "2026-09-20-01", "2026-09-20T09:00:00+00:00", "awaiting_approval")
    else:
        from datetime import datetime, timedelta
        later = (datetime.fromisoformat(ctx["started"]) + timedelta(days=1)).isoformat()
        _prior_synthesis(ctx, "2026-02-01-01", later, "completed")
    ctx["canon_before"] = _canon_pages(nb / SYNTH_CANON)
    _prepare_quick(case, ctx)


def _check_synthesis(case: dict, add, res: list, ctx: dict, run: dict, run_dir: Path, proposed: list,
                     workers: list) -> None:
    nb, cid = ctx["notebook"], ctx["cycle_id"]
    # The common "no --full-only step ran" contradicts the requirement for this kind: synthesis now runs in
    # --ingest-only. Replace it with the same check minus synthesis.
    res[:] = [x for x in res if x["name"] != "no --full-only step ran"]
    others = [p.stem for p in run_dir.glob("*.json") if p.stem.startswith(("lint-semantic", "claims", "promote"))]
    add("no --full-only step ran except synthesis", not others, others)
    add("spawned a wiki-ingester worker for the queued source", bool(workers),
        [a.get("subagent_type") for a in _agent_calls(run)])

    sj, sm, scope_f = run_dir / "synthesis.json", run_dir / "synthesis.md", run_dir / "synthesis-scope.txt"
    try:
        step = json.loads(sj.read_text(encoding="utf-8")) if sj.is_file() else {}
    except json.JSONDecodeError:
        step = {}
    add("synthesis.json and synthesis.md written in the run folder", bool(step) and sm.is_file(),
        [p.name for p in run_dir.glob("synthesis*")])
    add("synthesis-scope.txt written by the scope script", scope_f.is_file(), scope_f.name)
    scope = scope_f.read_text(encoding="utf-8", errors="replace").lower() if scope_f.is_file() else ""
    mtext = sm.read_text(encoding="utf-8", errors="replace").lower() if sm.is_file() else ""
    status = str(step.get("status") or "")

    cdir = nb / SYNTH_CANON
    now_canon = _canon_pages(cdir)
    before = ctx.get("canon_before") or {}
    changed = sorted(set(now_canon) ^ set(before)) or [k for k in before if now_canon.get(k) != before[k]]
    add("no best-practices page changed, added or removed (nothing applied without approval)",
        bool(before) and not changed, changed)

    synth_agents = [a for a in _agent_calls(run)
                    if str(a.get("subagent_type", "")) not in ("wiki-ingester", "wiki-checker")
                    and re.search(r"synthes|best.practices", str(a.get("prompt", "")) + str(a.get("description", "")), re.I)]

    if case["synthesis"] == "new":
        add("synthesis.json status is awaiting_approval (the session cannot be asked)",
            status == "awaiting_approval", status or "no status")
        add("the scope names the research entry promoted after the last completed synthesis",
            SYNTH_SLUG in scope or "trimming tool results" in scope, scope[:300])
        add("the staged entry is not in the scope", not any(Path(k).stem.lower() in scope for k in proposed),
            [Path(k).stem for k in proposed])
        add("the proposal in synthesis.md covers the scoped entry",
            SYNTH_SLUG in mtext or "trimming tool results" in mtext, mtext[:300])
        rep = run_dir / f"{cid}-run-cycle-report.md"
        sections = re.split(r"(?m)^## ", rep.read_text(encoding="utf-8", errors="replace")) if rep.is_file() else []
        needs = sections[-1].lower() if sections else ""
        add("the report's Needs you section lists the awaiting synthesis",
            bool(re.match(r"[\W_]*needs you\b", needs)) and bool(re.search(r"synthesis|best.practice", needs)), needs[:1200])
    else:
        add("synthesis.json status is skipped", bool(re.match(r"skipped", status, re.I)), status or "no status")
        reason = json.dumps([step.get("summary"), step.get("notes"), step.get("skipped")])
        add("the skip carries a reason (summary, notes or skipped hold words)",
            len(re.findall(r"[A-Za-z]", reason)) >= 8 and reason.count("null") < 3, reason[:300])
        add("no synthesis agent spawned", not synth_agents,
            [str(a.get("description", ""))[:60] for a in synth_agents])


def _check_bigraw(case: dict, add, ctx: dict, run: dict, run_dir: Path, proposed: list) -> None:
    nb = ctx["notebook"]
    sys.path.insert(0, str(ctx["scripts"]))
    from _entry_checks import check_entry_file, split_frontmatter
    # premise guard: the fixture really is too big for one worker; N is the script's own parts= line
    p = _script(ctx, "wiki-raw-parts.py", str(nb / "raw" / f"{BIG_SLUG}.md"))
    m = re.search(r"parts=(\d+)", p.stdout)
    n_parts = int(m.group(1)) if m else 0
    add("fixture: the oversized raw is reported fits_one_worker=no", "fits_one_worker=no" in p.stdout, p.stdout[:200])

    calls = _agent_calls(run)

    def says(a, slug):
        return slug in str(a.get("prompt", "")).lower()

    readers = [a for a in calls if says(a, BIG_SLUG)
               and str(a.get("subagent_type", "")) not in ("wiki-ingester", "wiki-checker")]
    add("one reader per printed part (readers other than the ingest workers, each told the raw)",
        n_parts >= 2 and len(readers) >= n_parts, f"{len(readers)} readers, {n_parts} parts")
    filers = [a for a in calls if str(a.get("subagent_type", "")) == "wiki-ingester" and says(a, BIG_SLUG)
              and str(a.get("model", "")).lower().startswith("opus")]
    add("one wiki-ingester worker on opus files the oversized item", bool(filers),
        [(a.get("subagent_type"), a.get("model")) for a in calls if says(a, BIG_SLUG)])
    small = [a for a in calls if str(a.get("subagent_type", "")) == "wiki-ingester" and says(a, SMALL_SLUG)]
    add("the ordinary item went through a wiki-ingester worker", bool(small), len(calls))

    by_url, gate_errs = {}, []
    for k in proposed:
        path = nb / k
        fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
        by_url[_norm_url(fm.get("source_url"))] = body
        g = check_entry_file(path)
        if g.get("errors"):
            gate_errs.append(f"{k}: {g['errors']}")
    add("both sources staged once, the oversized one included",
        set(by_url) == {_norm_url(BIG_URL), _norm_url(SMALL_URL)} and len(proposed) == 2, sorted(by_url))
    add("staged entries pass the gate", proposed and not gate_errs, gate_errs)
    add("the oversized entry carries the fact only the late section holds",
        bool(re.search(BIG_FACT, by_url.get(_norm_url(BIG_URL), ""))), "no 417 in the staged entry")

    upd = run_dir / "update.json"
    try:
        u = json.loads(upd.read_text(encoding="utf-8")) if upd.is_file() else {}
    except json.JSONDecodeError:
        u = {}
    queued = u.get("queued") or []
    add("update.json covers both items, the oversized one named", len(queued) == 2
        and BIG_SLUG in json.dumps(queued).lower(), json.dumps(queued)[:200])
    add("update.json: nothing skipped or deferred (the oversized item neither failed nor stalled the batch)",
        not (u.get("skipped") or u.get("deferred")), json.dumps([u.get("skipped"), u.get("deferred")])[:200])


SHORT2_SLUG = "timeouts-for-agent-tool-calls"
SHORT2_URL = f"https://example.com/skilltest/{SHORT2_SLUG}"
_SHORT2_RAW = """# Timeouts for agent tool calls

Give every tool call a timeout shorter than the session's own limit. A call that hangs for ten minutes
costs the whole session more than the call is worth.

Set the timeout per tool: a local file read needs seconds, a web fetch needs tens of seconds.

When a call times out, tell the model how long it waited and let it choose between a retry and another route.
"""
TALK_URL = "https://www.youtube.com/watch?v=skilltest01"
LONG_MARK = re.compile(r"talk-transcript|skilltest01", re.I)
LOCAL_ITEMS = {"small": (SMALL_SLUG, SMALL_URL), "short2": (SHORT2_SLUG, SHORT2_URL),
               "talk": ("talk-transcript", TALK_URL)}


def _prepare_local_items(case: dict, ctx: dict) -> None:
    """Queue the case's items from local raws in raw/ (no live fetch), each ticket carrying its raw_path."""
    nb = ctx["notebook"]
    texts = {"small": _SMALL_RAW, "short2": _SHORT2_RAW,
             "talk": (HERE / "fixtures" / "checker" / "talk-transcript.md").read_text(encoding="utf-8")}
    for key in case["items"]:
        slug, url = LOCAL_ITEMS[key]
        (nb / "raw" / f"{slug}.md").write_text(texts[key], encoding="utf-8")
        p = _script(ctx, "wiki-list-add.py", "--topic", NOTEBOOK, "--source", url, "--added-by", "skilltest")
        if p.returncode != 0:
            raise RuntimeError(f"could not queue {url}: {p.stdout}{p.stderr}")
        for t in (nb / "_inbox" / "pending").glob("*.md"):
            body = t.read_text(encoding="utf-8")
            if url in body and "raw_path:" not in body:
                t.write_text(re.sub(r"\A---\r?\n", f"---\nraw_path: raw/{slug}.md\n", body, count=1), encoding="utf-8")


def _check_model_choice(case: dict, add, res: list, ctx: dict, run_dir: Path, proposed: list, workers: list, text: str) -> None:
    nb = ctx["notebook"]
    sys.path.insert(0, str(ctx["scripts"]))
    from _entry_checks import split_frontmatter
    # Step 5.5 writes its promote pair in every ingesting mode (task #184), so the common check that counts a
    # promote step as --full-only is replaced by the same check without promote.
    res[:] = [x for x in res if x["name"] != "no --full-only step ran"]
    full = [p.stem for p in run_dir.glob("*.json") if p.stem.startswith(("lint-semantic", "claims"))] \
        if run_dir.is_dir() else []
    add("no --full-only step ran except the promote step", not full, full)
    want = {_norm_url(LOCAL_ITEMS[k][1]) for k in case["items"]}
    got = {_norm_url(split_frontmatter((nb / k).read_text(encoding="utf-8"))[0].get("source_url")) for k in proposed}
    add("each queued item staged once", got == want, sorted(got))
    add("spawned wiki-ingester workers", bool(workers), [a.get("subagent_type") for a in workers])
    model = lambda a: str(a.get("model", "")).lower()
    fields = lambda a: str(a.get("prompt", "")) + " " + str(a.get("description", ""))
    if case["kind"] == "model-mix":
        long_w = [a for a in workers if LONG_MARK.search(fields(a))]
        short_w = [a for a in workers if not LONG_MARK.search(fields(a))]
        add("a worker took the long transcript", bool(long_w), [a.get("description") for a in workers])
        add("every worker holding the long transcript is on opus",
            bool(long_w) and all("opus" in model(a) for a in long_w), [model(a) for a in long_w])
        add("the short items went to workers that do not hold the transcript", bool(short_w),
            [a.get("description") for a in workers])
        add("those workers are on sonnet (the default ingest model)",
            bool(short_w) and all("sonnet" in model(a) for a in short_w), [model(a) for a in short_w])
        scratch, rep = run_dir / "scratchpad.md", run_dir / f"{ctx['cycle_id']}-run-cycle-report.md"
        record = " ".join(p.read_text(encoding="utf-8", errors="replace") for p in (scratch, rep) if p.is_file()) + " " + text
        record = record.lower()
        add("the run's record (reply, scratchpad or cycle report) names both opus and sonnet",
            "opus" in record and "sonnet" in record, record[:200])
    else:
        add("every worker is on the default ingest model (sonnet)",
            bool(workers) and all("sonnet" in model(a) for a in workers), [model(a) for a in workers])
        raised = re.search(r"(?s)which (ingest )?model|choos\w*.{0,40}model|model.{0,60}(choice|choos|ask|pick|select)|"
                           r"(ask|pick|select)\w*.{0,60}model", text)
        add("the reply raises the model choice the user asked for", bool(raised), text[:300])
        add("the reply names the configured default (sonnet)", "sonnet" in text, text[:300])


CHECKER_URL = "https://www.youtube.com/watch?v=skilltest01"


def _check_checker_promote(case: dict, add, res: list, ctx: dict, run: dict, run_dir: Path) -> None:
    nb = ctx["notebook"]
    sys.path.insert(0, str(ctx["scripts"]))
    from _entry_checks import split_frontmatter
    # this kind's point is that the entry leaves _inbox/proposed/ for wiki/; and Step 5.5 writes its promote pair
    # in every ingesting mode (task #184), so --full-only is checked without promote
    res[:] = [x for x in res if x["name"] not in ("nothing filed straight into wiki/ (staged run)",
                                                  "no --full-only step ran")]
    full = [p.stem for p in run_dir.glob("*.json") if p.stem.startswith(("lint-semantic", "claims"))] \
        if run_dir.is_dir() else []
    add("no --full-only step ran except the promote step", not full, full)
    chk = [a for a in _agent_calls(run) if str(a.get("subagent_type", "")) == "wiki-checker"]
    add("spawned a wiki-checker", bool(chk), [a.get("subagent_type") for a in _agent_calls(run)])
    clog = nb / "_inbox" / "reports" / "checker-log.jsonl"
    rows = []
    for x in (clog.read_text(encoding="utf-8").splitlines() if clog.is_file() else []):
        try:
            rows.append(json.loads(x))
        except json.JSONDecodeError:
            pass
    add("checker-log.jsonl has the fix row", any(r.get("verdict") == "fix" for r in rows), rows)

    calls = run["tool_calls"]

    def cmd(c):
        return str((c.get("input") or {}).get("command", "")) if c["name"] == "Bash" else ""

    # the recording: the first Bash call holding checker-corrected, and where in its text
    rec_i = next((i for i, c in enumerate(calls) if "checker-corrected" in cmd(c)), None)
    add("the correction was recorded with the checker-corrected command", rec_i is not None, len(calls))

    def rechecks(text_):
        """Offsets of wiki-promote invocations that carry --check and --slug (one invocation = up to the next
        ; & | or newline)."""
        return [m.start() for m in re.finditer(r"wiki-promote[^\n;&|]*", text_)
                if "--check" in m.group(0) and "--slug" in m.group(0)]

    after = False
    if rec_i is not None:
        pos = cmd(calls[rec_i]).find("checker-corrected")
        after = any(o > pos for o in rechecks(cmd(calls[rec_i]))) \
            or any(rechecks(cmd(c)) for c in calls[rec_i + 1:])
    add("wiki-promote.py --check --slug was run after recording (in the same command or a later one)", after,
        len(calls))

    found = []
    base = nb / "wiki"
    for p in sorted(base.rglob("*.md")) if base.is_dir() else []:
        rel = p.relative_to(nb).as_posix()
        if _is_entry(rel):
            fm, body = split_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            if _norm_url(fm.get("source_url")) == _norm_url(CHECKER_URL):
                found.append((rel, body))
    add("the flagged entry is promoted into wiki/", len(found) == 1, [r for r, _ in found])
    body = found[0][1] if found else ""
    add("the promoted entry is the corrected one (no 70%, the ninth technique present)",
        bool(found) and "70%" not in body and bool(re.search(r"ninth|rollback", body, re.I)), body[:200])


# ---------- kind "checker-gate": which staged entries the checker reads (long transcript, big source, spot check) ----------

def _gate_big_raw() -> str:
    """About 79 KB of written-for-the-test prose (the first six sections of the big field guide), under a short
    summary the entry follows. No duration: it qualifies by size alone."""
    rng = random.Random(11)
    out = ["# Field Guide to Handoffs and Durable State in Long-Running AI Agents (first six sections)", "",
           "## Summary", "",
           "A shared ledger of decisions lets one agent session hand work to the next. It holds when every handoff "
           "brief states a testable goal and an acceptance check, every ledger entry follows a versioned schema and "
           "is rejected if it does not validate, every entry has an identifier that other entries can cite, every "
           "transfer is accepted by its receiver, acknowledgements follow a read-back of the goal, and a sweep flags "
           "stale handoffs by age without reassigning them.", ""]
    for i, (title, c, purpose, fails, remedies, arts, metric) in enumerate(_BIG_SECTIONS[:6], 1):
        out += [f"## Section {i}: {title}", ""]
        size = 0
        while size < 13200:
            sents = []
            for t in rng.sample(_BIG_TEMPLATES, 3):
                f, f2 = rng.sample(fails, 2)
                sents.append(t.format(C=c, Cc=c[0].upper() + c[1:], P=purpose, F=f, F2=f2, R=rng.choice(remedies),
                                      A=rng.choice(arts), M=metric, N=rng.randint(3, 60), X=rng.randint(4, 71)))
            para = " ".join(sents)
            out += [para, ""]
            size += len(para) + 1
    text = "\n".join(out)
    if not 70_000 <= len(text.encode("utf-8")) <= 120_000:
        raise RuntimeError(f"gate big raw is the wrong size: {len(text.encode('utf-8'))} bytes")
    return text


_GATE_RELATED = """
## Related

- [Agent memory architectures](agent-memory-architectures.md): a small external store read back into the context.
- [Context engineering basics](context-engineering-basics.md): choosing what enters the window is a context decision.
"""

GATE_ITEMS = {
    "big": {
        "name": "gate-handoff-ledger-guide", "url": "https://example.com/skilltest/gate-handoff-ledger-guide",
        "title": "Handoff ledger essentials from a long field guide", "tags": "agents,memory,handoff",
        "raw": _gate_big_raw,
        "body": """# Handoff ledger essentials from a long field guide

## TL;DR

A shared ledger of decisions lets one agent session hand work to the next: it holds when each brief states a testable goal, each entry follows a versioned schema, and each transfer is accepted by its receiver.

## What it says

- Intake: write the goal as one testable sentence and attach an acceptance check to every brief.
- Structure: use a versioned schema with required fields and reject entries that fail validation.
- Identifiers: give every entry an identifier other entries can cite, and check references at write time.
- Ownership: require an explicit accept step, with a single owner field that expires.
- Acknowledgement: acknowledge only after a read-back of the goal, with a bounded wait and escalation.
- Stale handoffs: flag work by an age threshold per task class; the sweep flags and never reassigns.
""" + _GATE_RELATED},
    "small0": {
        "name": "gate-budget-note-0", "url": "https://example.com/skilltest/gate-budget-note-0",
        "title": "Context window budgeting note 0", "slug": "context-window-budgeting-note-0",
        "tags": "context-engineering,agents",
        "raw": "Keep a reserve of the window empty for the model's reply. Reserve at least 15 percent so a long answer "
               "is not cut off, and measure the reserve against the longest reply seen, not the average.\n",
        "body": """# Context window budgeting note 0

## TL;DR

Leave part of the context window empty for the model's reply, sized from the longest reply seen.

## What it says

- Reserve at least 15 percent of the window so a long answer is not cut off.
- Size the reserve from the longest reply seen, not the average.
""" + _GATE_RELATED},
    "small2": {
        "name": "gate-budget-note-2", "url": "https://example.com/skilltest/gate-budget-note-2",
        "title": "Context window budgeting note 2", "slug": "context-window-budgeting-note-2",
        "tags": "context-engineering,agents",
        "raw": "Budget the context window per source. Give the system instructions, the tool definitions, the "
               "retrieved documents and the running conversation each a fixed share, and trim the largest share "
               "first when the window fills. A common split is 10 percent instructions, 20 percent tools, "
               "40 percent retrieved text and 30 percent conversation.\n",
        "body": """# Context window budgeting note 2

## TL;DR

Give each source in the context window a fixed share, and trim the largest share first when the window fills.

## What it says

- The sources are the system instructions, the tool definitions, the retrieved documents and the conversation.
- A common split is 10 percent instructions, 20 percent tools, 40 percent retrieved text and 30 percent conversation.
""" + _GATE_RELATED},
}


def _prepare_checker_gate(case: dict, ctx: dict, cycle_id: str) -> None:
    """A run interrupted after its staging check (resume from Phase 2.6), with the case's items staged: each a raw
    in raw/, a ticket moved to done/, and an entry in _inbox/proposed/ filed by wiki-update.py. None is a
    transcript and none carries a duration; the scratchpad says nothing about sizes."""
    nb = ctx["notebook"]
    bodies = ctx["project"] / "gate-bodies"
    bodies.mkdir(parents=True, exist_ok=True)
    queued, slugs = [], {}
    for key in case["items"]:
        it = GATE_ITEMS[key]
        raw = it["raw"]() if callable(it["raw"]) else it["raw"]
        (nb / "raw" / f"{it['name']}.md").write_text(
            f"---\nsource_url: {it['url']}\nfetched: {ctx['started']}\n---\n\n{raw}", encoding="utf-8")
        (bodies / f"{it['name']}.md").write_text(it["body"], encoding="utf-8")
        p = _script(ctx, "wiki-list-add.py", "--topic", NOTEBOOK, "--source", it["url"], "--added-by", "skilltest")
        if p.returncode != 0:
            raise RuntimeError(f"could not queue {it['url']}: {p.stdout}{p.stderr}")
        p = _script(ctx, "wiki-update.py", "--topic", NOTEBOOK, "--source", str(bodies / f"{it['name']}.md"),
                    "--source-url", it["url"], "--raw-path", f"raw/{it['name']}.md", "--title", it["title"],
                    "--tags", it["tags"], "--folder", "research/best-practices", "--tier", "3",
                    "--confidence", "medium", "--ingested-by", "skilltest-fixture",
                    "--staged", "--skip-integration", "--no-index")
        if p.returncode != 0:
            raise RuntimeError(f"could not stage {key}: {p.stdout}{p.stderr}")
        m = re.search(r"^wiki_path=.*?([^/\\]+)\.md\s*$", p.stdout, re.M)
        slug = m.group(1) if m else ""
        if it.get("slug") and slug != it["slug"]:
            raise RuntimeError(f"{key} was filed as '{slug}', not '{it['slug']}': the spot-check facts hold only for that name")
        slugs[key] = slug
        queued.append({"priority": 3, "url": it["url"], "slug": slug, "reason": f"staged: {it['title']}",
                       "timestamp": ctx["started"]})
    for t in (nb / "_inbox" / "pending").glob("*.md"):
        if not t.name.startswith("_"):
            t.rename(nb / "_inbox" / "done" / t.name)
    ctx["gate_slugs"] = slugs
    _write_run(ctx, cycle_id, HERE / "fixtures" / "checker-gate" / "scratchpad.md", queued)


def _check_checker_gate(case: dict, add, ctx: dict, run: dict, run_dir: Path) -> None:
    nb = ctx["notebook"]
    slugs = ctx["gate_slugs"]
    want = {slugs[k] for k in case["checked"]}
    skip = {slugs[k] for k in case["unchecked"]}
    calls = _agent_calls(run)
    chk = [a for a in calls if str(a.get("subagent_type", "")) == "wiki-checker"]
    add("spawned a wiki-checker", bool(chk), [a.get("subagent_type") for a in calls])
    d = run_dir / "checker"
    got = {p.stem for p in d.glob("*.json")} if d.is_dir() else set()
    add("a checker report for each entry the gate picks", bool(want) and want <= got, f"want {sorted(want)}, got {sorted(got)}")
    add("no checker report for an entry the gate does not pick", not (skip & got), sorted(skip & got))
    clog = nb / "_inbox" / "reports" / "checker-log.jsonl"
    rows = []
    for x in (clog.read_text(encoding="utf-8").splitlines() if clog.is_file() else []):
        try:
            rows.append(json.loads(x))
        except json.JSONDecodeError:
            pass
    add("checker-log.jsonl has one row per checked entry and no more", len(rows) == len(want), rows)
    workers = [a for a in calls if str(a.get("subagent_type", "")) == "wiki-ingester"]
    add("no ingest worker spawned (ingest was done)", not workers, [a.get("description") for a in workers])


# ---------- kind "scope": what the semantic lint and the claims step read in a --full run ----------

SCOPE_FILES = {"lint": "semantic-scope.txt", "claims": "claims-scope.txt"}


def _scope_now():
    from datetime import datetime
    return datetime.now().astimezone()


def _scope_age(nb: Path, when) -> None:
    """Every file under wiki/ gets the same old mtime, so only what a case then writes looks recent."""
    ts = when.timestamp()
    for p in (nb / "wiki").rglob("*"):
        if p.is_file():
            os.utime(p, (ts, ts))


def _scope_entry_stems(nb: Path) -> dict:
    return {p.stem: p.relative_to(nb).as_posix() for p in sorted((nb / "wiki").rglob("*.md"))
            if _is_entry(p.relative_to(nb).as_posix())}


def _scope_entry(nb: Path, stem: str, title: str, written, reviewed, tldr: str, covers: list, why: str, mtime) -> str:
    """A test-written entry under wiki/research/best-practices/; returns its path relative to the notebook."""
    from datetime import timedelta
    p = nb / "wiki" / "research" / "best-practices" / f"{stem}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    bullets = "\n".join(f"- {c}" for c in covers)
    p.write_text(
        f'---\ntitle: "{title}"\ndate: {written.isoformat()}\nsource_url: "internal://skilltest/scope/{stem}"\n'
        f"ingested_by: skilltest-fixture\ntier: self\nconfidence: medium\nlast_reviewed: {reviewed.isoformat()}\n"
        f"review_after: {(reviewed + timedelta(days=90)).isoformat()}\ntags: [agents, tools]\n---\n\n"
        f"# {title}\n\n## TL;DR\n\n{tldr}\n\n## What it covers\n\n{bullets}\n\n## Why it matters\n\n{why}\n",
        encoding="utf-8")
    ts = mtime.timestamp()
    os.utime(p, (ts, ts))
    return p.relative_to(nb).as_posix()


def _scope_prior_lint(ctx: dict, when) -> str:
    """An earlier run folder holding only a completed semantic-lint pair whose `timestamp` is `when`;
    returns the date folder's path relative to the sandbox."""
    cid = f"{when.strftime('%Y-%m-%d')}-01"
    rel = f"notebooks/{NOTEBOOK}/_inbox/reports/{cid[:10]}"
    run = ctx["sandbox"] / rel / cid
    run.mkdir(parents=True, exist_ok=True)
    step = {"skill": "wiki-lint", "cycle_id": cid, "step": "lint-semantic", "timestamp": when.isoformat(),
            "status": "completed", "summary": {"entries_in_scope": 0, "findings": 0}, "queued": [],
            "skipped": [], "deferred": [], "notes": "test fixture: an earlier semantic lint", "errors": []}
    (run / "lint-semantic.json").write_text(json.dumps(step, indent=2), encoding="utf-8")
    (run / "lint-semantic.md").write_text(
        f"# Semantic lint - {cid}\n\n**Status**: completed\n**Timestamp**: {when.isoformat()}\n", encoding="utf-8")
    return rel


def _scope_backdated_history(ctx: dict, when, paths: list) -> None:
    """'Added' is read from git history, and the case's ordinary fixture commit is made now, so every file it
    commits looks created after the cut-off. Start this case's history on a fresh orphan branch whose first
    commit, dated `when` (before the cut-off), holds `paths` (relative to the sandbox); the fixture commit then
    adds only what the case wrote afterwards. Earlier cases' commits stay on their own branch. The repo is
    initialised with the same config as _commit_fixture when .git is missing."""
    import time
    if not (ctx["sandbox"] / ".git").is_dir():
        for args in (["init", "-q"], ["config", "user.name", "skilltest"],
                     ["config", "user.email", "skilltest@example.com"], ["config", "core.autocrlf", "false"],
                     ["config", "core.longpaths", "true"]):
            _git(ctx, *args)
    env = {**os.environ, "GIT_AUTHOR_DATE": when.isoformat(), "GIT_COMMITTER_DATE": when.isoformat()}

    def g(*a, check=True):
        return subprocess.run(["git", "-C", str(ctx["sandbox"]), *a], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=env, check=check)
    g("checkout", "-q", "--orphan", f"scope-{int(time.time())}")
    g("rm", "-r", "-q", "--cached", "--ignore-unmatch", ".", check=False)
    g("add", "-A", "--", *paths)
    g("commit", "-q", "--allow-empty", "-m", "fixture: history before the cut-off")


def _prepare_scope(case: dict, ctx: dict, cycle_id: str) -> None:
    """The promote-setting fixture in its --full form (two staged entries, resume from the checker phase), the
    wiki aged to 8 days, then this case's few entries, with git history that matches the scope rules:
    - an entry meant to be old is created in a commit dated before the cut-off and keeps an old last_reviewed;
    - 'revised' is an old entry whose last_reviewed is rewritten to a day on or after the cut-off's day;
    - 'added' is created after the backdated commit (and carries a date after the cut-off).
    lint: cut-off = the timestamp of an earlier run folder's lint-semantic.json (72 h ago).
    claims: cut-off = when _inbox/claims-index.json was last written (48 h ago); the index holds claims for every
    older entry."""
    from datetime import timedelta
    _prepare_promote_setting({"mode": "full"}, ctx, cycle_id)
    nb, now = ctx["notebook"], _scope_now()
    at = lambda h: now - timedelta(hours=h)
    day = lambda h: at(h).date()
    lint = case["scope"] == "lint"
    cutoff = at(72) if lint else at(48)
    base = _scope_entry_stems(nb)  # the seed's entries, unchanged in every case
    for stem, rel in base.items():
        m = re.search(r'(?m)^last_reviewed:\s*"?(\d{4}-\d{2}-\d{2})', (nb / rel).read_text(encoding="utf-8"))
        if m and m.group(1) >= cutoff.date().isoformat():
            raise RuntimeError(f"seed entry {stem} has last_reviewed {m.group(1)}: it would count as revised")
    _scope_age(nb, at(24 * 8))
    sc = {"base": sorted(base), "rel": {}, "titles": {}}

    def put(key, stem, title, written, reviewed, tldr, covers, why, mtime):
        sc["rel"][stem] = _scope_entry(nb, stem, title, written, reviewed, tldr, covers, why, mtime)
        sc["titles"][stem] = title
        sc[key] = stem

    if lint:
        extra = [_scope_prior_lint(ctx, cutoff)]
        put("old", "session-ledger-retention-rules", "Session ledger retention rules", day(960), day(960),
            "Keep ledger entries for 30 days, then archive them.",
            ["**Retention**: ledger entries are deleted after 90 days and nothing is archived.",
             "**Review**: read the oldest entries before each deletion."],
            "A retention rule that contradicts itself leaves operators guessing which period applies.", at(24 * 8))
        rev = dict(key="revised", stem="retry-budget-guidelines", title="Retry budget guidelines", written=day(720),
                   tldr="Give every tool call a retry budget of three attempts, so a flaky tool cannot stall a session.",
                   covers=["**Budget size**: the budget is seven attempts per call, never fewer, because transient failures often need several tries.",
                           "**Scope**: count the budget per tool, not per task.",
                           "**Exhaustion**: return the error with the attempt count."],
                   why="A budget of three attempts keeps the session moving; the budget stops a loop from running unbounded.")
        put(reviewed=day(720), mtime=at(24 * 8), **rev)          # old: created before the cut-off
        _scope_backdated_history(ctx, cutoff - timedelta(days=5), [f"notebooks/{NOTEBOOK}/wiki", *extra])
        put(reviewed=day(60), mtime=at(60), **rev)               # revised after the cut-off (last_reviewed moves)
        put("added", "incident-handoff-checklist", "Incident handoff checklist", day(48), day(48),
            "Before handing an incident to another agent, write down what is known, what was tried and what is next.",
            ["**Known facts**: the symptoms and when they started.", "**Tried**: each fix and its result.",
             "**Next**: the one step the receiver should take first."],
            "A receiver that starts from a written state does not repeat the sender's work.", at(48))
        sc["in"] = [sc["revised"], sc["added"]]
        sc["unchanged"] = sc["base"] + [sc["old"]]
        sc["defect_out_tokens"] = r"\b90 days\b"
    else:
        rev = dict(key="revised", stem="prompt-caching-layout-rules", title="Prompt caching layout rules",
                   written=day(720),
                   tldr="Order the context from most stable to least stable so the cached prefix stays long.",
                   covers=["**Order**: stable blocks first, volatile blocks last.",
                           "**Clock**: put the current time after the cache breakpoint.",
                           "**Tools**: sort the tool list once, at session start."],
                   why="A cached prefix is only reused while its bytes do not change.")
        put(reviewed=day(720), mtime=at(24 * 8), **rev)          # has claims in the index, old when it was written
        claims = []
        for stem, rel in {**base, rev["stem"]: sc["rel"][rev["stem"]]}.items():
            for n in (1, 2):
                claims.append({"id": f"{stem}-{n}", "entry": rel, "source": rel, "source_entry": rel, "path": rel,
                               "subject": stem.replace("-", " "), "predicate": f"states point {n}",
                               "object": "as written when the index was built", "classification": "sourced"})
        idx = nb / "_inbox" / "claims-index.json"
        idx.parent.mkdir(parents=True, exist_ok=True)
        idx.write_text(json.dumps({"version": 1, "generated_at": cutoff.isoformat(), "written_at": cutoff.isoformat(),
                                   "updated": cutoff.isoformat(), "claims": claims}, indent=2), encoding="utf-8")
        os.utime(idx, (cutoff.timestamp(), cutoff.timestamp()))
        _scope_backdated_history(ctx, cutoff - timedelta(days=5),
                                 [f"notebooks/{NOTEBOOK}/wiki", f"notebooks/{NOTEBOOK}/_inbox/claims-index.json"])
        put(reviewed=day(36), mtime=at(36), **rev)               # revised after the index was written
        put("added", "eval-set-versioning", "Eval set versioning", day(24), day(24),
            "Version an eval set the way code is versioned, so a score always names the set that produced it.",
            ["**Versions**: give every eval set a version string.", "**Scores**: record the version beside each score.",
             "**Changes**: never edit a set in place; add a new version."],
            "A score without a set version cannot be compared with last month's.", at(24))
        sc["in"] = [sc["revised"], sc["added"]]
        sc["unchanged"] = sc["base"]
    ctx["scope"] = sc


def _scope_named(text: str, stem: str, title: str = "") -> bool:
    return bool(re.search(rf"(?<![\w-]){re.escape(stem)}(?![\w-])", text)) or (bool(title) and title.lower() in text)


def _check_scope(case: dict, add, res: list, ctx: dict, run_dir: Path) -> None:
    nb, sc, which = ctx["notebook"], ctx["scope"], case["scope"]
    # this is a --full run: the common "no --full-only step ran" contradicts the kind's premise
    res[:] = [x for x in res if x["name"] != "no --full-only step ran"]
    step = "lint-semantic" if which == "lint" else "claims"

    def step_ran() -> bool:
        for p in sorted(run_dir.glob(f"{step}*.json")) if run_dir.is_dir() else []:
            try:
                st = str(json.loads(p.read_text(encoding="utf-8")).get("status") or "")
            except (json.JSONDecodeError, OSError, AttributeError):
                continue
            if not st.lower().startswith("skipped"):
                return True
        return False

    add(f"premise: the {which} step ran and was not skipped", step_ran(),
        sorted(p.name for p in run_dir.glob("*.json")) if run_dir.is_dir() else "no run folder")
    f = run_dir / SCOPE_FILES[which]
    lines = f.read_text(encoding="utf-8", errors="replace").splitlines() if f.is_file() else []
    add(f"{f.name} written into the run folder, under a # header line",
        f.is_file() and bool(lines) and lines[0].lstrip().startswith("#"), lines[:2] or "no file")
    paths = [l.strip().replace("\\", "/") for l in lines if l.strip() and not l.lstrip().startswith("#")]
    stems = {p.rsplit("/", 1)[-1].removesuffix(".md") for p in paths}
    for stem in sc["in"]:
        add(f"{which} scope lists {stem} (added or revised after the cut-off)", sc["rel"][stem] in paths, paths[:12])
    if which == "lint":
        staged = sorted(ctx.get("promote_stems", set()))
        add("lint scope lists this run's staged entries (both)", len(staged) == 2 and all(s in stems for s in staged),
            {"staged": staged, "scope": paths[:12]})
    unchanged = [s for s in sc["unchanged"] if s in stems]
    add(f"{which} scope lists none of the unchanged entries", not unchanged, unchanged)

    if which == "lint":
        reports = [p for p in sorted(run_dir.glob("lint-semantic*")) if p.suffix in (".json", ".md")] if run_dir.is_dir() else []
        rtext = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in reports).lower()
        rv, old = sc["revised"], sc["old"]
        add("the semantic lint reports the planted defect in the revised entry", _scope_named(rtext, rv, sc["titles"][rv]),
            rtext[:300] or "no lint-semantic report")
        add("the semantic lint does not report the older, unchanged entry's defect (never read)",
            not (_scope_named(rtext, old, sc["titles"][old]) or re.search(sc["defect_out_tokens"], rtext)), rtext[:300])
    else:
        idx = nb / "_inbox" / "claims-index.json"
        itext = idx.read_text(encoding="utf-8", errors="replace").lower() if idx.is_file() else ""
        a = sc["added"]
        add("the claims index now holds claims for the entry that had none", _scope_named(itext, a, sc["titles"][a]),
            itext[:200] or "no claims-index.json")


# ---------- kind "lint-all": --full --lint-all puts every entry in the semantic lint's scope (task #179) ----------

LA_OLD_SLUG = "handoff-checklists-for-agent-sessions"
LA_NEW_SLUGS = ("tool-result-pointers-in-agent-context", "backoff-rules-for-agent-retries")
LA_SEED_OLD = "agent-tool-security-basics"  # extra-seed entry, dated 2026-01-12
LA_TITLES = {LA_OLD_SLUG: "Handoff checklists for agent sessions",
             LA_NEW_SLUGS[0]: "Tool result pointers in agent context",
             LA_NEW_SLUGS[1]: "Backoff rules for agent retries"}
LA_DIR = "wiki/research/best-practices"


def _la_entry(slug: str, day: str, tldr: str) -> str:
    return (f'---\ntitle: "{LA_TITLES[slug]}"\ndate: {day}\nsource_url: "internal://skilltest/seed/{slug}"\n'
            f'ingested_by: skilltest-fixture\ntier: self\nconfidence: medium\nlast_reviewed: {day}\n'
            f'review_after: 2099-01-01\ntags: [agents, tools, context-engineering]\n---\n\n'
            f'# {LA_TITLES[slug]}\n\n## TL;DR\n\n{tldr}\n\n## What it covers\n\n- One practice, stated briefly.\n\n'
            f'## Why it matters\n\nIt keeps long agent sessions predictable.\n')


def _prior_lint(ctx: dict, cycle_id: str, timestamp: str) -> None:
    """An earlier run folder holding only a completed semantic-lint pair."""
    run = ctx["notebook"] / "_inbox" / "reports" / cycle_id[:10] / cycle_id
    run.mkdir(parents=True, exist_ok=True)
    step = {"skill": "wiki-cycle", "cycle_id": cycle_id, "step": "lint-semantic", "timestamp": timestamp,
            "status": "completed", "summary": {"entries_in_scope": 0}, "queued": [], "skipped": [], "deferred": [],
            "notes": "test fixture: an earlier semantic lint", "errors": []}
    (run / "lint-semantic.json").write_text(json.dumps(step, indent=2), encoding="utf-8")
    (run / "lint-semantic.md").write_text(
        f"# Semantic lint - {cycle_id}\n\n**Status**: completed\n**Timestamp**: {timestamp}\n", encoding="utf-8")


def _prepare_lint_all(case: dict, ctx: dict) -> None:
    """A semantic lint 3 days ago (outside the 24 hours). The entries older than it are committed with a
    back-dated commit (the scope script reads git history), then two entries dated today are written, to be
    added by the fixture commit."""
    from datetime import datetime, timedelta
    nb, sb = ctx["notebook"], ctx["sandbox"]
    started = datetime.fromisoformat(ctx["started"])
    prior = started - timedelta(days=3)
    _prior_lint(ctx, f"{prior.date().isoformat()}-01", prior.isoformat())
    base = nb / LA_DIR
    old_when = started - timedelta(days=60)
    old_ts = old_when.timestamp()
    (base / f"{LA_OLD_SLUG}.md").write_text(_la_entry(LA_OLD_SLUG, "2026-03-02", "Hand a session over with a short checklist of open work."), encoding="utf-8")
    for slug in (LA_OLD_SLUG, LA_SEED_OLD):
        os.utime(base / f"{slug}.md", (old_ts, old_ts))
    if not (sb / ".git").is_dir():  # same init as _commit_fixture
        for args in (["init", "-q"], ["config", "user.name", "skilltest"],
                     ["config", "user.email", "skilltest@example.com"], ["config", "core.autocrlf", "false"],
                     ["config", "core.longpaths", "true"]):
            _git(ctx, *args)
    env = {**os.environ, "GIT_AUTHOR_DATE": old_when.isoformat(), "GIT_COMMITTER_DATE": old_when.isoformat()}
    for args in (["add", "-A"], ["commit", "-q", "--allow-empty", "-m", "fixture: older entries"]):
        subprocess.run(["git", "-C", str(sb), *args], capture_output=True, text=True, env=env, check=True)
    today = _today(ctx)
    for slug, tldr in ((LA_NEW_SLUGS[0], "Return a pointer to a large tool result, not the result."),
                       (LA_NEW_SLUGS[1], "Back off between retries and cap the attempts.")):
        (base / f"{slug}.md").write_text(_la_entry(slug, today, tldr), encoding="utf-8")
    ctx["lint_all"] = {"old": [LA_OLD_SLUG, LA_SEED_OLD], "new": list(LA_NEW_SLUGS)}


def _check_lint_all(case: dict, add, res: list, ctx: dict, run_dir: Path) -> None:
    # A --full run with discovery cannot be held to the staged-run counts of the common checks.
    res[:] = [x for x in res if not (x["name"].startswith(("quick steps all wrote", "no --full-only", "pending queue",
                                                         "both tickets", "0 ticket"))
                                     or x["name"].endswith(("in _inbox/proposed/", "in _inbox/done/")))]
    sj = run_dir / "lint-semantic.json"
    try:
        step = json.loads(sj.read_text(encoding="utf-8")) if sj.is_file() else {}
    except json.JSONDecodeError:
        step = {}
    add("the semantic lint ran (the earlier one was 3 days ago, outside the 24 hours)",
        bool(step) and not re.match(r"skipped", str(step.get("status") or ""), re.I), step.get("status") or "no lint-semantic.json")
    sf = run_dir / "semantic-scope.txt"
    add("semantic-scope.txt written in the run folder", sf.is_file(), [p.name for p in run_dir.iterdir()] if run_dir.is_dir() else "no run folder")
    lines = {l.strip().replace("\\", "/").lower() for l in sf.read_text(encoding="utf-8", errors="replace").splitlines()
             if l.strip() and not l.lstrip().startswith("#")} if sf.is_file() else set()
    la = ctx["lint_all"]
    path = lambda s: f"{LA_DIR}/{s}.md".lower()
    add("--lint-all: every entry older than the last lint is in the scope",
        sf.is_file() and all(path(s) in lines for s in la["old"]), [s for s in la["old"] if path(s) not in lines])
    add("--lint-all: every entry newer than the last lint is in the scope",
        sf.is_file() and all(path(s) in lines for s in la["new"]), [s for s in la["new"] if path(s) not in lines])


# ---------- kind "hub": a hub page behind its hub_tag gets one line per missing live entry ----------

HUB_TAG = "lantern-ops"
HUB_PATH = "wiki/project/hubs/lantern-hub.md"
# slug -> (folder, title, tldr, tags, section of the hub that fits)
HUB_ENTRIES = {
    "lantern-start-and-stop-order": ("wiki/research/best-practices", "Starting and stopping Lantern in order",
                                     "Start the lease store before the workers and stop them in the reverse order.",
                                     ["agents", HUB_TAG], "Running Lantern"),
    "lantern-lease-expiry-settings": ("wiki/project/components", "Lantern lease expiry settings",
                                      "Set the lease expiry to twice the longest task so no live task is reclaimed.",
                                      ["agents", HUB_TAG], "Troubleshooting"),
    "lantern-stuck-queue-diagnosis": ("wiki/research/best-practices", "Diagnosing a stuck Lantern queue",
                                      "When a Lantern queue stops draining, check the lease table first, then the worker heartbeat.",
                                      ["agents", HUB_TAG], "Troubleshooting"),
    "lantern-naming-notes": ("wiki/project/components", "Lantern naming notes",
                             "Name Lantern queues after the job they carry, not the team that owns them.",
                             ["agents", "lantern"], ""),  # decoy: a different tag, never on the hub
}
HUB_MISSING = "lantern-stuck-queue-diagnosis"
HUB_DECOY = "lantern-naming-notes"


def _hub_entry_text(title: str, tldr: str, tags: list, day: str, slug: str) -> str:
    return (f'---\ntitle: "{title}"\ndate: {day}\nsource_url: "internal://skilltest/seed/{slug}"\n'
            f'ingested_by: skilltest-fixture\ntier: self\nconfidence: medium\nlast_reviewed: {day}\n'
            f'review_after: 2099-01-01\ntags: [{", ".join(tags)}]\n---\n\n# {title}\n\n## TL;DR\n\n{tldr}\n\n'
            f'## What it covers\n\n- One practice, stated briefly.\n\n## Why it matters\n\nIt keeps Lantern predictable.\n')


def _hub_rel(slug: str) -> str:
    import posixpath
    return posixpath.relpath(f"{HUB_ENTRIES[slug][0]}/{slug}.md", posixpath.dirname(HUB_PATH))


def _prepare_hub(case: dict, ctx: dict, cycle_id: str) -> None:
    """The resume fixture (two staged entries, update pair), plus a live hub page declaring hub_tag, three live
    entries carrying the tag and one decoy carrying another tag. The hub links the first two and, when
    hub_complete, the third too."""
    _prepare_resume(ctx, cycle_id)
    nb, day = ctx["notebook"], _today(ctx)
    for slug, (folder, title, tldr, tags, _sec) in HUB_ENTRIES.items():
        (nb / folder).mkdir(parents=True, exist_ok=True)
        (nb / folder / f"{slug}.md").write_text(_hub_entry_text(title, tldr, tags, day, slug), encoding="utf-8")
    line = lambda s: f"- [{HUB_ENTRIES[s][1]}]({_hub_rel(s)}) — {HUB_ENTRIES[s][2]}"
    running = [line("lantern-start-and-stop-order")]
    trouble = [line("lantern-lease-expiry-settings")]
    if case.get("hub_complete"):
        trouble.append(line(HUB_MISSING))
    text = (f'---\ntitle: "Lantern hub"\ndate: {day}\nsource_url: "internal://skilltest/seed/lantern-hub"\n'
            f'ingested_by: skilltest-fixture\ntier: self\nconfidence: medium\nlast_reviewed: {day}\n'
            f'review_after: 2099-01-01\nhub_tag: {HUB_TAG}\ntags: [hub]\n---\n\n# Lantern hub\n\n'
            "Everything we know about running Lantern, gathered from across the wiki.\n\n"
            "## Running Lantern\n\n" + "\n".join(running) + "\n\n## Troubleshooting\n\n" + "\n".join(trouble) + "\n")
    (nb / HUB_PATH).parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    (nb / HUB_PATH).write_bytes(data)
    ctx["hub_before"] = data


def _check_hub(case: dict, add, ctx: dict, run_dir: Path) -> None:
    import posixpath
    nb, cid = ctx["notebook"], ctx["cycle_id"]
    hub = nb / HUB_PATH
    before_b = ctx["hub_before"]
    after_b = hub.read_bytes() if hub.is_file() else b""
    lint = run_dir / "lint-mechanical.json"
    try:
        lsum = json.loads(lint.read_text(encoding="utf-8")).get("summary", {}) if lint.is_file() else {}
    except json.JSONDecodeError:
        lsum = {}
    add("after the run the lint counts no hub entry missing (hub_entries_missing is 0)",
        lsum.get("hub_entries_missing") == 0, lsum.get("hub_entries_missing", "no hub_entries_missing in the summary"))
    after_t = after_b.decode("utf-8", errors="replace")
    add("the decoy entry (another tag) is not linked on the hub", f"{HUB_DECOY}.md" not in after_t)
    if case.get("hub_complete"):
        add("the hub already links every tagged entry: the hub file is byte-for-byte unchanged", after_b == before_b,
            "changed" if after_b != before_b else "")
        changed = _git(ctx, "diff", "--name-only", ctx["fixture_commit"], "HEAD").split("\n")
        add("the hub is not in the run's commit", f"notebooks/{NOTEBOOK}/{HUB_PATH}" not in changed,
            [x for x in changed if "hub" in x])
        return
    before = before_b.decode("utf-8").splitlines()
    after = after_t.splitlines()
    # the hub's own lines keep their text and their order
    it = iter(after)
    kept = all(any(l == a for a in it) for l in before if l.strip())
    add("the hub's original lines are all still there, unrewritten and in their order", kept, after_t[-400:])
    old = set(before)
    new = [l for l in after if l.strip() and l not in old]
    add("exactly one line was added to the hub", len(new) == 1, new)
    miss_target = posixpath.normpath(f"{HUB_ENTRIES[HUB_MISSING][0]}/{HUB_MISSING}.md")
    hit = [l for l in new
           if any(posixpath.normpath(posixpath.join(posixpath.dirname(HUB_PATH), t.strip())) == miss_target
                  for t in re.findall(r"\]\(([^)]+)\)", l))]
    add("the added line links the missing tagged entry (a path that resolves from the hub)", len(hit) == 1, new)
    if new:
        i = max(j for j, l in enumerate(after) if l == new[0])
        head = next((after[j] for j in range(i, -1, -1) if after[j].startswith("## ")), "")
        add("the line sits under the heading that fits (Troubleshooting)", head.strip() == "## Troubleshooting", head)
    rep = run_dir / f"{cid}-run-cycle-report.md"
    rtext = rep.read_text(encoding="utf-8", errors="replace").lower() if rep.is_file() else ""
    add("the cycle report names the line added (the entry's title or file name)",
        HUB_ENTRIES[HUB_MISSING][1].lower() in rtext or HUB_MISSING in rtext, rtext[-300:] or "no report")


# ---------- kind "youtube-batch": several videos in one batch go to one worker, fetched one at a time ----------

YT_ID = re.compile(r"(?:v=|youtu\.be/)([\w-]{11})")


def _prepare_youtube(case: dict, ctx: dict) -> None:
    """Queue the case's items; record, per video, its id and its ticket's file name (a worker's brief may name
    either)."""
    _prepare_quick(case, ctx)
    sources = _suite()["sources"]
    marks = {}
    for key in case["videos"]:
        url = sources[key]["url"]
        vid = YT_ID.search(url).group(1)
        names = [t.name for t in (ctx["notebook"] / "_inbox" / "pending").glob("*.md")
                 if vid in t.read_text(encoding="utf-8", errors="replace")]
        marks[key] = [vid, *names, *[Path(n).stem for n in names]]
    ctx["yt_marks"] = marks


def _check_youtube_batch(case: dict, add, ctx: dict, run: dict, proposed: list) -> None:
    nb, marks = ctx["notebook"], ctx["yt_marks"]
    sys.path.insert(0, str(ctx["scripts"]))
    from _entry_checks import check_entry_file, split_frontmatter
    spawns = [c for c in run["tool_calls"] if c["name"] in ("Agent", "Task")
              and str((c.get("input") or {}).get("subagent_type", "")) == "wiki-ingester"]

    def holds(c, ms):
        inp = c.get("input") or {}
        t = (str(inp.get("prompt", "")) + " " + str(inp.get("description", ""))).lower()
        return any(m.lower() in t for m in ms)

    holders = {k: [i for i, c in enumerate(spawns) if holds(c, ms)] for k, ms in marks.items()}
    add("every video was handed to a wiki-ingester worker", all(holders.values()), holders)
    used = {i for hs in holders.values() for i in hs}
    add("all the videos went to the same one worker (parallel workers would hit YouTube's rate limit)",
        all(holders.values()) and len(used) == 1, holders)
    if len(used) == 1:
        wid = spawns[next(iter(used))].get("id") or spawns[next(iter(used))].get("tool_use_id")
        kids = [c for c in run["tool_calls"] if wid and (c.get("parent_tool_use_id") or c.get("parent")) == wid]
        add("the video worker's own tool calls are identifiable in the run", bool(kids), f"{len(kids)} calls")
        bg = [c["name"] for c in kids if (c.get("input") or {}).get("run_in_background")
              or c["name"] in ("Agent", "Task")]
        add("the video worker started nothing in the background and spawned no sub-agent (one at a time)", not bg, bg)
    else:
        add("the video worker's own tool calls are identifiable in the run", False, "no single video worker")
    ids = {k: ms[0] for k, ms in marks.items()}
    got, gate_errs = [], []
    for k in proposed:
        path = nb / k
        fm, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        m = YT_ID.search(str(fm.get("source_url") or ""))
        got.append(m.group(1) if m else _norm_url(fm.get("source_url")))
        g = check_entry_file(path)
        if g.get("errors"):
            gate_errs.append(f"{k}: {g['errors']}")
    add("each video's entry staged exactly once", all(got.count(v) == 1 for v in ids.values()), got)
    ordinary = _norm_url(_suite()["sources"]["context-engineering"]["url"])
    add("the ordinary item staged too", ordinary in got, got)
    add("staged entries pass the gate", proposed and not gate_errs, gate_errs)


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    sys.path.insert(0, str(ctx["scripts"]))
    from _entry_checks import check_entry_file, split_frontmatter

    nb, res = ctx["notebook"], []

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    add_denials(add, run)

    now = snapshot(ctx)
    fixture = ctx.get("fixture_files", {})
    new = sorted(set(now) - set(fixture))
    cycle_id = ctx["cycle_id"]
    run_dir = nb / "_inbox" / "reports" / cycle_id[:10] / cycle_id

    # ---- the run folder and its scratchpad ----
    day = nb / "_inbox" / "reports" / cycle_id[:10]
    folders = sorted(p.name for p in day.iterdir() if p.is_dir()) if day.is_dir() else []
    add(f"one run folder, {cycle_id}", folders == [cycle_id], folders)
    scratch = run_dir / "scratchpad.md"
    stext = scratch.read_text(encoding="utf-8", errors="replace") if scratch.is_file() else ""
    add("scratchpad written", bool(stext))
    add("scratchpad status: completed", _scratch_status(stext) == "completed", _scratch_status(stext) or "none")

    # ---- the step contract ----
    # email-review.json is the session's judgment of the email candidates, input to a step, not a step
    # email-review.json, models.json (Step 0's model list, task #99) and cost.json (the cost marks) are not step results
    jsons = sorted(p for p in run_dir.glob("*.json")
                   if p.name not in ("email-review.json", "models.json", "cost.json")) if run_dir.is_dir() else []
    mds = {p.stem for p in run_dir.glob("*.md")} if run_dir.is_dir() else set()
    lonely = [p.name for p in jsons if p.stem not in mds]
    add("every step JSON has its .md", jsons and not lonely, lonely)
    bad = []
    for p in jsons:
        if p.name.endswith("-run-cycle-report.json"):
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            bad.append(f"{p.name}: {e}")
            continue
        miss = [f for f in STEP_FIELDS if f not in d] if isinstance(d, dict) else ["not an object"]
        if miss or d.get("cycle_id") != cycle_id:
            bad.append(f"{p.name}: missing {miss}, cycle_id {d.get('cycle_id') if isinstance(d, dict) else '?'}")
    add("every step JSON follows the contract (fields, cycle_id)", jsons and not bad, bad)
    present = {p.stem for p in jsons}
    discover_only = case["kind"] in ("email", "drive")
    if not discover_only:  # --discover-only stops before ingest and lint
        add("quick steps all wrote their pair", all(s in present for s in QUICK_STEPS),
            [s for s in QUICK_STEPS if s not in present])
    full = [s for s in present if s.startswith(FULL_ONLY)]
    add("no --full-only step ran", not full, full)
    add("cycle report written (.md + .json)", (run_dir / f"{cycle_id}-run-cycle-report.md").is_file()
        and (run_dir / f"{cycle_id}-run-cycle-report.json").is_file())
    # task #84 (Mark, 2026-10-06): he reads from the bottom up, so what waits on him is the last section
    rep = run_dir / f"{cycle_id}-run-cycle-report.md"
    heads = [l[3:].strip() for l in rep.read_text(encoding="utf-8", errors="replace").splitlines()
             if l.startswith("## ")] if rep.is_file() else []
    add("the cycle report's last section is Needs you", bool(heads) and "needs you" in heads[-1].lower(),
        heads[-1] if heads else "no report")
    lint = run_dir / "lint-mechanical.json"
    try:
        lsum = json.loads(lint.read_text(encoding="utf-8")).get("summary", {}) if lint.is_file() else {}
    except json.JSONDecodeError:
        lsum = {}
    if not discover_only:
        add("lint-mechanical.json counts broken links", isinstance(lsum.get("broken_links"), int), lsum)

    # ---- what landed ----
    proposed = sorted(k for k in now if k.startswith("_inbox/proposed/") and _is_entry(k))
    wiki_new = [k for k in new if k.startswith("wiki/") and _is_entry(k)]
    add("nothing filed straight into wiki/ (staged run)", not wiki_new, wiki_new)
    n_staged, n_done = case.get("staged", 2), case.get("done", 2)
    add({1: "one entry in _inbox/proposed/", 2: "two entries in _inbox/proposed/"}.get(
        n_staged, f"{n_staged} entries in _inbox/proposed/"), len(proposed) == n_staged, proposed)
    p = _script(ctx, "wiki-promote.py", "--topic", NOTEBOOK, "--check")
    add("wiki-promote --check passes", p.returncode == 0, (p.stdout + p.stderr)[-250:])
    if not discover_only:  # --discover-only leaves what it queued in pending/
        add("pending queue empty", not _tickets(nb / "_inbox" / "pending"), _tickets(nb / "_inbox" / "pending"))
    add("both tickets in _inbox/done/" if n_done == 2 else f"{n_done} ticket(s) in _inbox/done/",
        len(_tickets(nb / "_inbox" / "done")) == n_done, _tickets(nb / "_inbox" / "done"))
    temp = [k for k in new if k.startswith("_inbox/temp/")]
    add("temp files cleaned up", not temp, temp)

    workers = [a for a in _agent_calls(run) if str(a.get("subagent_type", "")) == "wiki-ingester"]
    log = nb / "_inbox" / "intake" / "triage-log.md"
    log_rows = [l for l in log.read_text(encoding="utf-8").splitlines()
                if l.startswith("| ") and not l.startswith("| Date")] if log.is_file() else []
    text = run["text"].lower()
    if case["kind"] in ("ingest-only", "triage"):
        add("triage ran: one log row per queued ticket", len(log_rows) == len(case["queue"]),
            f"{len(log_rows)} rows for {len(case['queue'])} tickets")
    if case["kind"] == "triage":
        mine = _norm_url(_suite()["sources"][case["mine"]]["url"])
        theirs = _norm_url(_suite()["sources"][case["theirs"]]["url"])
        other_dir = nb / "_inbox" / "intake" / "other"
        tix = sorted(other_dir.glob("*.md")) if other_dir.is_dir() else []
        fms = [split_frontmatter(x.read_text(encoding="utf-8"))[0] for x in tix]
        routed = [f for f in fms if _norm_url(f.get("source")) == theirs]
        add("the other reader's source routed to its bucket", bool(routed), [x.name for x in tix])
        rp = str((routed[0].get("raw_path") if routed else "") or "")
        add("its raw captured for the other reader", bool(rp) and (nb / rp).is_file(), rp or "no raw_path")
        staged_urls = {_norm_url(split_frontmatter((nb / k).read_text(encoding="utf-8"))[0].get("source_url"))
                       for k in proposed}
        add("only this session's source ingested", staged_urls == {mine}, sorted(staged_urls))
        add("the report names other-bot for telling", "other-bot" in text or "<@222>" in text)
    if case["kind"] == "checker":
        chk_calls = [a for a in _agent_calls(run) if str(a.get("subagent_type", "")) == "wiki-checker"]
        add("spawned a wiki-checker", bool(chk_calls), [a.get("subagent_type") for a in _agent_calls(run)])
        add("the checker on its config's model (opus)", chk_calls and all(
            str(a.get("model", "")).lower().startswith("opus") for a in chk_calls), [a.get("model") for a in chk_calls])
        reps = sorted((run_dir / "checker").glob("*.json")) if (run_dir / "checker").is_dir() else []
        report = {}
        try:
            report = json.loads(reps[0].read_text(encoding="utf-8")) if reps else {}
        except json.JSONDecodeError:
            pass
        add("a checker report in the run folder", bool(report), [x.name for x in reps])
        skipped = json.dumps(report.get("skipped_sections") or []).lower()
        add("the report names the skipped ninth technique", bool(re.search(r"ninth|rollback|snapshot", skipped)),
            skipped[:200])
        unsup = json.dumps(report.get("unsupported_claims") or []).lower()
        add("the report names the inflated 70%", "70" in unsup, unsup[:200])
        add("the report's verdict is fix", report.get("verdict") == "fix", report.get("verdict"))
        clog = nb / "_inbox" / "reports" / "checker-log.jsonl"
        rows = [json.loads(x) for x in clog.read_text(encoding="utf-8").splitlines() if x.strip()] \
            if clog.is_file() else []
        add("the check logged in checker-log.jsonl", len(rows) == 1 and rows[0].get("verdict") == "fix", rows)
        body = (nb / proposed[0]).read_text(encoding="utf-8") if proposed else ""
        corrected = "70%" not in body and bool(re.search(r"ninth|rollback", body, re.I))
        held = ctx.get("checker_slug", "~") in text and bool(re.search(r"held|hold", text))
        add("the flagged entry corrected, or held for the user", corrected or held,
            "corrected" if corrected else ("held" if held else "neither"))
        add("no ingest worker spawned (ingest was done)", not workers, [a.get("description") for a in workers])
    if case["kind"] == "ingest-only":
        # skipped on the 1.0 line itself ("Phases 1.0, 1, 1.1, 1.5: skipped (mode)") or within its section
        add("scratchpad records the Drive step as skipped",
            bool(re.search(r"1\.0[^\n]*skipped|1\.0[^\n]*\n(?:[^\n#]*\n){0,3}?[^\n]*skipped", stext, re.I)))
        add("spawned wiki-ingester workers", bool(workers), [a.get("subagent_type") for a in _agent_calls(run)])
        add("workers on model_default (sonnet): the run cannot ask",
            workers and all(str(a.get("model", "")).lower().startswith("sonnet") for a in workers),
            [a.get("model") for a in workers])
        urls = {_norm_url(_suite()["sources"][s]["url"]) for s in case["queue"]}
        got, gate_errs = set(), []
        for k in proposed:
            path = nb / k
            fm, _ = split_frontmatter(path.read_text(encoding="utf-8"))
            got.add(_norm_url(fm.get("source_url")))
            g = check_entry_file(path)
            if g.get("errors"):
                gate_errs.append(f"{k}: {g['errors']}")
        add("each queued source staged once", got == urls, sorted(got))
        add("staged entries pass the gate", proposed and not gate_errs, gate_errs)
        upd = run_dir / "update.json"
        try:
            u = json.loads(upd.read_text(encoding="utf-8")) if upd.is_file() else {}
        except json.JSONDecodeError:
            u = {}
        add("update.json covers the whole batch (both items)", len(u.get("queued") or []) == 2,
            f"{len(u.get('queued') or [])} queued")
    elif case["kind"] == "email":
        _check_email(case, add, ctx, run_dir, stext, text, workers)
    elif case["kind"] == "drive":
        _check_drive(add, ctx, run_dir, text, workers)
    elif case["kind"] == "scratch":
        import posixpath
        import shlex
        import tempfile

        def slash(p):
            return str(p).replace("\\", "/")

        def drive(p):
            m = re.match(r"^/([A-Za-z])/(.*)$", p)
            return f"{m.group(1)}:/{m.group(2)}" if m and os.name == "nt" else p

        def norm(p):
            p = drive(slash(p).strip().strip("\"'"))
            if not p:
                return ""
            p = posixpath.normpath(p).rstrip("/")  # resolves "." and ".." segments
            return p.lower() if os.name == "nt" else p

        # the folder each worker's brief names: <cycle_id>-worker-<N>
        pat = re.compile(r"([^\s\"'`<>(),;|]*" + re.escape(cycle_id) + r"-worker-\d+)")
        spawns = [c for c in run["tool_calls"] if c["name"] in ("Agent", "Task")
                  and str((c.get("input") or {}).get("subagent_type", "")) == "wiki-ingester"]
        briefs = [sorted({slash(m).rstrip("/") for m in pat.findall(str((c.get("input") or {}).get("prompt", "")))})
                  for c in spawns]
        folders = [b[0] for b in briefs if len(b) == 1]
        owner = {}  # id of the call that spawned a worker -> that worker's folder
        for c, b in zip(spawns, briefs):
            cid = c.get("id") or c.get("tool_use_id")
            if cid and len(b) == 1:
                owner[cid] = b[0]
        need = case.get("workers", 1)
        add(f"spawned at least {need} wiki-ingester worker(s)", len(spawns) >= need, len(spawns))
        add("every worker's brief names one scratch folder, <cycle_id>-worker-<N>",
            bool(spawns) and all(len(b) == 1 for b in briefs), briefs)
        add("no two workers share a scratch folder", bool(folders) and len(set(folders)) == len(folders), folders)
        add("no scratch folder inside the notebook (raw/ and _inbox/ are not scratch)",
            bool(folders) and not [f for f in folders if norm(f).startswith(norm(nb) + "/")], folders)

        # where each worker's own temp files went, from its own tool calls
        def resolve(p, cwd):
            p = p.strip().strip("\"'")
            if cwd and not re.match(r"^(/|[A-Za-z]:|~|\$)", p):
                return slash(cwd).rstrip("/") + "/" + p
            return p

        def drop_heredocs(cmd):
            """The command without heredoc bodies (the line with <<WORD stays, the body up to the terminator goes)."""
            kept, term = [], None
            for ln in cmd.split("\n"):
                if term is not None:
                    if ln.strip() == term:
                        term = None
                    continue
                kept.append(ln)
                m = re.search(r"(?<!<)<<(?!<)-?\s*(?:'([^']+)'|\"([^\"]+)\"|\\?([A-Za-z_][A-Za-z0-9_]*))", ln)
                if m:
                    term = next(g for g in m.groups() if g)
            return "\n".join(kept)

        def mask_quotes(s):
            """Same length as s, with the inside of every quoted string replaced by '_'."""
            out, q, esc = [], None, False
            for ch in s:
                if q:
                    if esc:
                        out.append("_")
                        esc = False
                    elif ch == "\\" and q == '"':
                        out.append("_")
                        esc = True
                    elif ch == q:
                        q = None
                        out.append(ch)
                    else:
                        out.append("_")
                else:
                    if ch in "'\"":
                        q = ch
                    out.append(ch)
            return "".join(out)

        def temp_targets(c):
            inp, out = c.get("input") or {}, []
            if c["name"] == "Write":
                out.append(str(inp.get("file_path", "")))
            elif c["name"] == "Bash":
                cwd = None
                cmd = drop_heredocs(str(inp.get("command", "")))
                masked = mask_quotes(cmd)
                spans, start = [], 0
                for m in re.finditer(r"&&|\|\||;|\n|\|", masked):
                    spans.append((start, m.start()))
                    start = m.end()
                spans.append((start, len(masked)))
                for a, b in spans:
                    oseg, mseg = cmd[a:b], masked[a:b]
                    for m in re.finditer(r"(?<![<>&])\d?>>?\s*(?!&)([^\s<>()&|;]+)", mseg):
                        out.append(resolve(oseg[m.start(1):m.end(1)], cwd))
                    try:
                        t = shlex.split(oseg.strip())
                    except ValueError:
                        t = oseg.split()
                    if not t:
                        continue
                    if t[0] == "cd" and len(t) > 1:
                        cwd = t[1]
                    elif t[0] == "curl":
                        for i, x in enumerate(t):
                            if x in ("-o", "--output") and i + 1 < len(t):
                                out.append(resolve(t[i + 1], cwd))
                            elif x in ("-O", "--remote-name"):
                                out.append(resolve(t[-1].split("?")[0].rstrip("/").split("/")[-1], cwd))
                    elif t[0] == "wget":
                        for i, x in enumerate(t):
                            if x == "-O" and i + 1 < len(t):
                                out.append(resolve(t[i + 1], cwd))
                            elif x == "-P" and i + 1 < len(t):
                                out.append(resolve(t[i + 1], cwd) + "/download")
                    elif t[0] == "git" and len(t) > 2 and t[1] == "clone":
                        skip = {"--depth", "-b", "--branch", "-o", "--origin", "-c", "--config", "--filter", "--reference"}
                        pos, i = [], 2
                        while i < len(t):
                            if t[i] in skip:
                                i += 2
                                continue
                            if not t[i].startswith("-"):
                                pos.append(t[i])
                            i += 1
                        if pos:
                            out.append(resolve(pos[1] if len(pos) > 1 else pos[0].rstrip("/").split("/")[-1].removesuffix(".git"), cwd))
                    elif t[0] == "mktemp":
                        args = [x for x in t[1:] if not x.startswith("-")]
                        tmpd = [x.split("=", 1)[1] for x in t[1:] if x.startswith("--tmpdir=")]
                        if args or tmpd:
                            out.extend(resolve(x, cwd) for x in (args or tmpd))
                        else:
                            out.append("<system-temp>/mktemp")
                    elif t[0] == "tee":
                        out.extend(resolve(x, cwd) for x in t[1:] if not x.startswith("-"))
            return out

        nbn, bad, seen, identified = norm(nb), [], 0, 0
        for c in run["tool_calls"]:
            pid = c.get("parent_tool_use_id") or c.get("parent")
            if pid not in owner:
                continue
            identified += 1
            mine = norm(owner[pid])
            for p in temp_targets(c):
                n = norm(p) if p else ""
                if not n or "$" in n or "`" in n or n in ("/dev/null", "/dev/stdout", "/dev/stderr", "-", "nul"):
                    continue
                seen += 1
                if n.startswith("<system-temp>"):
                    ok = False
                elif re.match(r"^(/|[a-z]:/|~)", n, re.I):
                    ok = n == mine or n.startswith(mine + "/") or n.startswith(nbn + "/")
                else:
                    ok = n.split("/")[0] in ("raw", "_inbox", "wiki")
                if not ok:
                    bad.append(f"{mine.rsplit('/', 1)[-1]}: {p}")
        add("workers' own tool calls are identifiable in the run (spawn id and parent id)", identified > 0,
            f"{identified} worker calls, {len(owner)} workers")
        add("every temp file a worker itself created is inside its own folder, none elsewhere (a worker that made none passes)",
            not bad, bad[:8] or f"{seen} temp targets, all inside the owner's folder or the notebook's raw/ and _inbox/")

        # each worker deleted its folder when its batch was done
        left = {f for f in folders if Path(drive(f)).exists()}
        tmp = Path(tempfile.gettempdir())
        for base, pats in ((ctx["sandbox"], [f"**/{cycle_id}-worker-*"]),
                           (tmp, [f"{cycle_id}-worker-*", f"*/{cycle_id}-worker-*"])):
            for pt in pats:
                try:
                    left.update(slash(x) for x in base.glob(pt))
                except OSError:
                    pass
        add("each worker deleted its scratch folder", bool(folders) and not left, sorted(left))

        # on disk: loose files at the sandbox root, in the project folder, or in _inbox/ outside its queue folders
        top_ok = {".git", ".gitignore", ".claude", "notebooks", "linked-notebooks.json", "skill", "agents",
                  "mail", "mail-resolve.json", "drive", "project", "global-toolset"}
        sb, proj, stray = ctx["sandbox"], ctx["project"], []
        for q in sb.iterdir():
            if q.name not in top_ok:
                stray += [slash(x.relative_to(sb)) for x in ([q] if q.is_file() else q.rglob("*")) if x.is_file()]
        for x in proj.rglob("*"):
            rel = x.relative_to(proj).parts
            if x.is_file() and rel[0] != ".claude" and "__pycache__" not in rel:
                stray.append(slash(x.relative_to(sb)))
        stray += [k for k in new if k.startswith("_inbox/")
                  and k.split("/")[1] not in ("proposed", "pending", "done", "reports", "intake")]
        stray = [s for s in stray if "-worker-" not in s]
        add("no loose temp file left at the sandbox root, in the project folder, or in _inbox/", not stray, stray[:10])

        urls = {_norm_url(_suite()["sources"][s]["url"]) for s in case["queue"]}
        got = {_norm_url(split_frontmatter((nb / k).read_text(encoding="utf-8"))[0].get("source_url")) for k in proposed}
        if case.get("pdf"):
            add("the PDF source was ingested", any("arxiv.org" in g for g in got), sorted(got))
        else:
            add("each queued source staged once", got == urls, sorted(got))
    elif case["kind"] == "resume":
        add("no ingest worker spawned (ingest was done)", not workers, [a.get("description") for a in workers])
        add("nothing ingested twice", len(proposed) == 2 and not [k for k in new if k in proposed], proposed)
        add("scratchpad: mechanical lint phase done",
            bool(re.search(r"Mechanical lint[^\n]*\n\s*-\s*\*\*Status\*\*:\s*done", stext, re.I)))
    elif case["kind"] == "models":
        mf = run_dir / "models.json"
        mtext = mf.read_text(encoding="utf-8", errors="replace") if mf.is_file() else ""
        try:
            json.loads(mtext)
            mjson = True
        except json.JSONDecodeError:
            mjson = False
        add("models.json written in the run folder", bool(mtext.strip()), mf.name)
        add("models.json is JSON", mjson, mtext[:120])
        if case.get("models_json_has"):
            add(f"models.json names {case['models_json_has']}", case["models_json_has"] in mtext.lower(), mtext[:200])
        add("spawned wiki-ingester workers", bool(workers), [a.get("subagent_type") for a in _agent_calls(run)])
        want = case["worker_model"]
        add(f"every ingest worker spawned on {want}",
            workers and all(want in str(a.get("model", "")).lower() for a in workers),
            [a.get("model") for a in workers])
        if case.get("report_names"):
            rp = run_dir / f"{cycle_id}-run-cycle-report.md"
            rt = rp.read_text(encoding="utf-8", errors="replace") if rp.is_file() else ""
            add("the cycle report names the unreadable setting file",
                bool(re.search(case["report_names"], rt, re.I)), rt[:200] or "no report")
        urls = {_norm_url(_suite()["sources"][s]["url"]) for s in case["queue"]}
        got = {_norm_url(split_frontmatter((nb / k).read_text(encoding="utf-8"))[0].get("source_url")) for k in proposed}
        add("the queued source was still staged", got == urls, sorted(got))
    elif case["kind"] == "retry":
        _check_retry(case, add, ctx, run_dir, text)
    elif case["kind"] == "bigraw":
        _check_bigraw(case, add, ctx, run, run_dir, proposed)
    elif case["kind"] == "synthesis":
        _check_synthesis(case, add, res, ctx, run, run_dir, proposed, workers)
    elif case["kind"] == "promote-setting":
        _check_promote_setting(case, add, res, ctx, run_dir)
    elif case["kind"] in ("model-mix", "model-ask"):
        _check_model_choice(case, add, res, ctx, run_dir, proposed, workers, text)
    elif case["kind"] == "checker-promote":
        _check_checker_promote(case, add, res, ctx, run, run_dir)
    elif case["kind"] == "scope":
        _check_scope(case, add, res, ctx, run_dir)
    elif case["kind"] == "hub":
        _check_hub(case, add, ctx, run_dir)
    elif case["kind"] == "checker-gate":
        _check_checker_gate(case, add, ctx, run, run_dir)
    elif case["kind"] == "lint-all":
        _check_lint_all(case, add, res, ctx, run_dir)
    elif case["kind"] == "youtube-batch":
        _check_youtube_batch(case, add, ctx, run, proposed)

    # ---- the commit ----
    commits = _git(ctx, "rev-list", f"{ctx['fixture_commit']}..HEAD").split()
    add("committed at the end (one commit)", len(commits) == 1, f"{len(commits)} commits")
    if commits:
        paths = _git(ctx, "diff", "--name-only", ctx["fixture_commit"], "HEAD").split("\n")
        outside = [x for x in paths if x and not x.startswith(f"notebooks/{NOTEBOOK}/")]
        add("commit scoped to the notebook", not outside, outside)
    dirty = _git(ctx, "status", "--porcelain", f"notebooks/{NOTEBOOK}").strip()
    add("nothing left uncommitted in the notebook", not dirty, dirty[:250])
    strays = [q.name for q in ctx["sandbox"].rglob("*") if q.is_file() and q.stat().st_size == 0
              and ".git" not in q.parts and q.name != ".gitkeep"]
    add("no zero-byte stray files", not strays, strays)
    return res
