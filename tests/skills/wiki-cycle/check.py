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
    "Bash(python:*)", "Bash(python3:*)", "Bash(node:*)", "Bash(cd:*)", "Bash(ls:*)",
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
FULL_ONLY = ("lint-semantic", "claims", "synthesis", "promote")


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
    fw = nb / "wiki" / "project" / "best-practices" / "framework"
    fw.mkdir(parents=True, exist_ok=True)
    for doc in (repo / "bootstrap" / "topic-template" / "wiki" / "best-practices" / "framework").glob("*.md"):
        shutil.copy2(doc, fw / doc.name)


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
    scripts = repo / "bootstrap" / "scripts"
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
    cfg = json.dumps({"tool": "claude-code", "project_name": NOTEBOOK, "notebook": NOTEBOOK,
                      "persona": "main", "registry": ctx["registry"].as_posix()}, indent=2)
    for d in (project, sandbox):
        (d / ".claude").mkdir(parents=True, exist_ok=True)
        (d / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")

    # the wiki-ingester and wiki-checker agents and their sidecars, from this repo, install paths -> sandbox
    repl = render_replacements(ctx)
    src = repo / "bootstrap" / "agents" / "wiki-ingester"
    chk = repo / "bootstrap" / "agents" / "wiki-checker"
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

    (sandbox / ".gitignore").write_text("project/\nskill/\nagents/\n.claude/\n", encoding="utf-8")

    index = f"cycletest-{model}-{sandbox.parent.name}"  # one per run, so two runs never share an index
    _qmd_index_file(index).unlink(missing_ok=True)
    for args in (["collection", "add", str(nb / "wiki")], ["embed"]):
        subprocess.run([*_qmd(), "--index", index, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    ctx["index"] = index
    ctx["env"] = {"WIKI_QMD_INDEX": index, "WIKI_QMD_CALLER": f"cycletest-{model}-{sandbox.parent.name}",
                  "PYTHONIOENCODING": "utf-8"}
    return ctx


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


RESUME_ITEMS = [
    ("resume-one", "Handoff files between agent sessions", "agents,memory,handoff"),
    ("resume-two", "Trimming tool results before they re-enter the context", "context-engineering,tools"),
]


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

The notebook is `{notebook}`, this project's notebook, at {nb}. The notebooks repository (git) is {sandbox}. Run scripts as `python <path> ...` or `node <path> ...`, with no environment-variable prefix, and write only inside {sandbox}. The user started this run and will read your report, but cannot answer questions while it runs: where the skill says to ask or confirm, make the choice the skill gives for a session that cannot ask, and say what you chose.

The user typed: """


def prompt(case: dict, ctx: dict) -> str:
    sys.path.insert(0, str(ctx["scripts"]))
    from _wiki_config import now_stamp
    _seed(ctx)
    ctx["started"] = now_stamp()
    cycle_id = f"{_today(ctx)}-01"
    ctx["cycle_id"] = cycle_id
    if case["kind"] == "ingest-only":
        _prepare_quick(case, ctx)
    elif case["kind"] == "triage":
        _prepare_triage(case, ctx)
    elif case["kind"] == "resume":
        _prepare_resume(ctx, cycle_id)
    elif case["kind"] == "checker":
        _prepare_checker(ctx, cycle_id)
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
    return rel.startswith("wiki/") and not rel.startswith("wiki/sessions/") and "/framework/" not in rel


def _norm_url(u) -> str:
    return str(u or "").strip().strip('"').strip("'").rstrip("/").lower().replace("://www.", "://")


def _tickets(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.glob("*.md") if not p.name.startswith(("_", "README")))


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
    jsons = sorted(p for p in run_dir.glob("*.json")) if run_dir.is_dir() else []
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
    add("quick steps all wrote their pair", all(s in present for s in QUICK_STEPS),
        [s for s in QUICK_STEPS if s not in present])
    full = [s for s in present if s.startswith(FULL_ONLY)]
    add("no --full-only step ran", not full, full)
    add("cycle report written (.md + .json)", (run_dir / f"{cycle_id}-run-cycle-report.md").is_file()
        and (run_dir / f"{cycle_id}-run-cycle-report.json").is_file())
    lint = run_dir / "lint-mechanical.json"
    try:
        lsum = json.loads(lint.read_text(encoding="utf-8")).get("summary", {}) if lint.is_file() else {}
    except json.JSONDecodeError:
        lsum = {}
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
        add("scratchpad records the Drive step as skipped",
            bool(re.search(r"1\.0[^\n]*\n(?:[^\n#]*\n){0,3}?[^\n]*skipped", stext, re.I)))
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
    elif case["kind"] == "resume":
        add("no ingest worker spawned (ingest was done)", not workers, [a.get("description") for a in workers])
        add("nothing ingested twice", len(proposed) == 2 and not [k for k in new if k in proposed], proposed)
        add("scratchpad: mechanical lint phase done",
            bool(re.search(r"Mechanical lint[^\n]*\n\s*-\s*\*\*Status\*\*:\s*done", stext, re.I)))

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
