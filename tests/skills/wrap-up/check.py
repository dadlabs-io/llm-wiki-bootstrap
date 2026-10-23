"""wrap-up test suite: fixtures, sandbox, prompts and checks for run_skill_test.py.

A headless session has no real conversation to distill, so each case's prompt carries
the session's work as narrative (cases.json `work`) over a made-up project, `beacon`,
whose files are really on disk in the sandbox. Nothing a model already knows can
answer for it.

What the cases cover, one of each input the skill handles: a first wrap-up with no
dashboards and a repo with no commits (the git-128 path), an incremental one that must
APPEND to this session's existing journal, a `none` answer at the proposal table,
projects on task cards (kinds "cards", "cards-stack", "cards-full", "cards-first"), `confirm_before_create: false`,
`confirm_before_promote: false`, a research-only session and a trivial one (the last
three tagged `complex`), and `--auto-push` (task #51, 2026-09-24): the project repo and
the notebooks repo each get a local bare remote, the session changed `beacon/retry.py`,
and an unrelated `scratch-notes.txt` of the user's sits untracked and must stay so.
Every case checks the closing line that now ends each wrap-up.

Every case is reset by prompt(): the seeds, the registry flags and the project repo are
rebuilt before the session starts, so no case depends on another's leftovers or order.

The checks read what the session left behind, never the commands it chose. The staged
entries go through the real gate (`_entry_checks.py`) and the real sidecar reader
(`wiki-promote.py --check`), so an entry that would be HELD at promote time fails here.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = "skilltest-wrap"
PERSONA = "main"
SID = "f71a2c90-wrapup-test"
CATEGORIES = ("components", "decisions", "architecture", "patterns", "troubleshooting")
HANDOFF_SECTIONS = ("GOAL", "WORK COMPLETED", "CURRENT STATE", "PENDING", "KEY FILES",
                    "CONTEXT FOR CONTINUATION")
ALLOWED_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep",
    "Bash(python:*)", "Bash(python3:*)", "Bash(uv:*)", "Bash(git:*)", "Bash(date:*)", "Bash(mkdir:*)",
    "Bash(cd:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(grep:*)", "Bash(head:*)", "Bash(tail:*)",
    "Bash(wc:*)", "Bash(find:*)", "Bash(sort:*)", "Bash(echo:*)", "Bash(pwd:*)", "Bash(sed:*)",
]
POINTS_AT_UPDATE = re.compile(r"/?wiki-update|/?wiki-cycle", re.I)
DECLINES = re.compile(
    r"nothing (here )?(merits|warrants|worth|that merits)|no (durable|wiki|entry|entries)|"
    r"not worth (a|an) (wiki )?entry|too (trivial|small|thin)|doesn'?t merit|"
    r"no candidates|nothing to file|nothing durable", re.I)
ASKS_REMOVE = re.compile(r"remove", re.I)
OFFER = re.compile(r"\?|let me know|tell me|say the word|if you(?:'d)? (?:want|like)|would you like|shall i|should i|want me to",
                   re.I)
REMOVED = re.compile(r"\bremoved\b|\bdeleted\b|\btook\b.{0,30}\boff\b|\btaken off\b|off the (task )?list|\bdropped\b|\bcleared\b", re.I)
BASE_REMOVAL = re.compile(r"\b(remove|delete)\b|take (it|that|this|them) off|drop it|clear it", re.I)
OFFER_WORDS = ("let me know", "tell me", "say the word", "if you want", "if you'd like", "would you like",
               "shall i", "should i", "want me to")


def _asks_about_removing(raw: str, task_id: int, name_pattern: str | None = None) -> bool:
    """True when a question or open offer about removing is about THIS task: its number or its name pattern.

    Sentences are cut at . ! ? ; and newlines. A sentence that names another task's number is not about this
    task, because a session-finished task is rightly asked about (requirement A).
    """
    own = re.compile(rf"(?:task|card|#)\s*0?{task_id}\b", re.I)
    for m in re.finditer(r"[^.!?;\n]+[.!?;]?", raw):
        s = m.group().strip()
        if not (BASE_REMOVAL.search(s) and (s.endswith("?") or any(o in s.lower() for o in OFFER_WORDS))):
            continue
        about_own = bool(own.search(s) or (name_pattern and re.search(name_pattern, s, re.I)))
        names_other = any(int(n) != task_id for n in re.findall(r"(?:task|card|#)\s*0?(\d+)\b", s, re.I))
        if about_own and not names_other:
            return True
    return False
CARD_LISTS = ("current", "backlog", "done")
CARD_STATUSES = ("ready", "doing", "waiting", "done")
CARD_REQUIRED = ("id", "title", "owner", "list", "status", "created", "updated")
EMPTY_VALUES = ("", "null", "~")
SEED_CARD_IDS = {1, 2, 3, 4, 5}
SEED_STATE = {1: {"list": "current", "status": "doing", "owner": "main", "waiting_on": ""},
              2: {"list": "current", "status": "doing", "owner": "main", "waiting_on": ""},
              3: {"list": "current", "status": "waiting", "owner": "dana", "waiting_on": "vendor reply"},
              4: {"list": "backlog", "status": "ready", "owner": "main", "waiting_on": ""},
              5: {"list": "done", "status": "done", "owner": "main", "waiting_on": ""}}
SEED_LOG = {1: "- 2026-10-07: Opened the task; found the seam is only described in code comments.",
            2: "- 2026-10-06: Drafted RetryBudget as an elapsed-time allowance in beacon/retry.py."}
CLOSING = {None: "✅ WRAP-UP COMPLETE: nothing committed ✅",
           "commit": "✅ WRAP-UP COMPLETE: committed, not pushed ✅",
           "push": "✅ WRAP-UP COMPLETE: committed and pushed ✅"}
SESSION_EDIT = "\n\ndef budget_left_seconds(budget):\n    return max(0.0, budget.remaining())\n"
AGENT_BUILDER_ID, LLM_WIKI_ID = "1548481349009154138", "1548485551076671538"
OWNER_WORD = re.compile(r"agent-builder|llm-wiki", re.I)
UNKNOWN_OWNER = re.compile(
    r"unknown|not sure|can'?t tell|cannot tell|no usage page|no (how-to )?page|whose|where (should|does) (it|this)|"
    r"which (project|owner)|neither|not (ours|one of ours|owned)|third.party|plugin", re.I)
WAITING = re.compile(r"wait|pick.?up|already sent|collect", re.I)
FILED = re.compile(r"\bfiled\b|received/|\breceived\b|improver", re.I)
SENT_TO_SELF = re.compile(r"send (it |this )?to llm-wiki|sent to llm-wiki", re.I)


def _owner_after(text: str, name: str, span: int = 600) -> set[str]:
    """The owner word first named after each mention of a skill, within `span` characters.

    A report may name the skill in a table row, a bullet or a sentence; the owner it proposes
    for that skill comes next, before the next suggestion's owner does.
    """
    found = set()
    for m in re.finditer(re.escape(name), text):
        w = OWNER_WORD.search(text, m.end(), m.end() + span)
        if w:
            found.add(w.group(0).lower())
    return found


def _near(text: str, name: str, pattern: re.Pattern, span: int = 600) -> bool:
    return any(pattern.search(text, m.end(), m.end() + span) for m in re.finditer(re.escape(name), text))


def _near_or_same_line(text: str, name: str, pattern: re.Pattern, span: int = 600) -> bool:
    """The pattern on a line that names the skill, or within `span` characters after any mention of it."""
    if any(pattern.search(line) for line in text.splitlines() if name in line):
        return True
    return _near(text, name, pattern, span)


def _rmtree(path) -> None:
    """Delete a tree that may hold a git repo.

    Windows marks git object files read-only, so a plain rmtree raises
    PermissionError on `.git` — which would abort the second case of every run.
    """
    def onexc(func, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass

    shutil.rmtree(path, onexc=onexc)


def _load(scripts: Path, name: str, mod_name: str):
    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(mod_name, scripts / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prepare_fixtures(repo: Path, refresh: bool = False) -> list[dict]:
    return []  # no third-party sources: every fixture is written for the test


def setup(model: str, sandbox: Path, repo: Path) -> dict:
    if sandbox.exists():
        _rmtree(sandbox)
    nb = sandbox / "notebooks" / NOTEBOOK
    shutil.copytree(HERE / "fixtures" / "seed-notebook", nb)
    # the usage pages Step 5.5's owner rule reads live in the global toolset, not the notebook
    toolset = sandbox / "global-toolset"
    shutil.copytree(HERE / "fixtures" / "toolset", toolset)
    project = sandbox / "project"
    project.mkdir(parents=True)
    cfg_dir = project / ".claude"
    cfg_dir.mkdir()
    return {"sandbox": sandbox, "project": project, "notebook": nb,
            "registry": sandbox / "linked-notebooks.json",
            "wiki": nb / "wiki", "proposed": nb / "_inbox" / "proposed",
            "skill_dir": sandbox / "skill" / "wrap-up", "toolset": toolset,
            "scripts": repo / "scripts", "repo": repo,
            # Promotion re-indexes the search (task #81 P1): an index of its own per run, so a
            # wrap-up case never updates or embeds the real one.
            "index": f"wrapuptest-{model}-{sandbox.parent.name}",
            "env": {"PYTHONIOENCODING": "utf-8", "WIKI_QMD_INDEX": f"wrapuptest-{model}-{sandbox.parent.name}"}}


SUGGESTIONS_INSTALLED = "~/.claude/skills/improving-skills-from-suggestions/scripts/suggestions.py"


def render_replacements(ctx: dict) -> dict:
    """Step 5.5 files a note that is already home with the improver's `receive`: the repo's copy, never the installed one."""
    return {SUGGESTIONS_INSTALLED:
            (ctx["repo"] / "skills" / "improving-skills-from-suggestions" / "scripts" / "suggestions.py").as_posix()}


def teardown(ctx: dict) -> None:
    try:
        _rmtree(ctx["sandbox"])
    except OSError:
        pass
    (Path.home() / ".cache" / "qmd" / f"{ctx['index']}.sqlite").unlink(missing_ok=True)


def snapshot(ctx: dict) -> dict:
    nb = ctx["notebook"]
    return {p.relative_to(nb).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in nb.rglob("*") if p.is_file()}


def _git(project: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=project, capture_output=True, text=True, timeout=60).stdout


def _bare(ctx: dict, name: str) -> Path:
    """A local bare repository standing in for a remote (no network)."""
    remote = ctx["sandbox"] / "remotes" / f"{name}.git"
    if remote.exists():
        _rmtree(remote)
    remote.mkdir(parents=True)
    _git(remote, "init", "-q", "--bare")
    return remote


def _reset_project(case: dict, ctx: dict) -> None:
    """The code repo the session worked in: beacon's files, with or without commits."""
    project = ctx["project"]
    for child in project.iterdir():
        if child.name != ".claude":
            _rmtree(child) if child.is_dir() else child.unlink()
    for src in (HERE / "fixtures" / "project-files").rglob("*"):
        if src.is_file():
            dest = project / src.relative_to(HERE / "fixtures" / "project-files")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    overlay = case.get("project_overlay")  # files only some cases get (task #130: a doc and the code it describes)
    if overlay:
        base = HERE / "fixtures" / "project-overlays" / overlay
        for src in base.rglob("*"):
            if src.is_file():
                dest = project / src.relative_to(base)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
    _git(project, "init", "-q")
    _git(project, "config", "user.email", "test@example.invalid")
    _git(project, "config", "user.name", "Skill Test")
    if case.get("git") in ("commits", "session-changes", "pinned-committed", "pinned-uncommitted"):
        _git(project, "add", "-A")
        _git(project, "commit", "-q", "-m", "beacon: retry budget draft and the network seam")
        ctx["base_commit"] = _git(project, "rev-parse", "HEAD").strip()
    if case.get("git") in ("pinned-committed", "pinned-uncommitted"):
        # the session's own change to the file a pinned living page describes (R2, 2026-10-22)
        with open(project / "beacon" / "manifest.py", "a", encoding="utf-8") as f:
            f.write(MANIFEST_SESSION_EDIT)
        if case["git"] == "pinned-committed":
            _git(project, "add", "beacon/manifest.py")
            _git(project, "commit", "-q", "-m", "beacon: manifest records only confirmed uploads")
    if case.get("git") == "session-changes":
        # the session's own change, uncommitted, and one file of the user's it never touched
        with open(project / "beacon" / "retry.py", "a", encoding="utf-8") as f:
            f.write(SESSION_EDIT)
        (project / "scratch-notes.txt").write_text("the user's own notes; not part of the session\n", encoding="utf-8")
        remote = _bare(ctx, "project")
        _git(project, "remote", "add", "origin", remote.as_posix())
        _git(project, "push", "-q", "-u", "origin", "HEAD")
    ctx["project_head"] = _git(project, "rev-parse", "HEAD").strip()


def _reset_notebook(case: dict, ctx: dict) -> None:
    """Dashboards, journal, staging and promoted entries, back to this case's seed."""
    nb, wiki = ctx["notebook"], ctx["wiki"]
    cfgmod = _load(ctx["scripts"], "_wiki_config.py", "wiki_config")
    today, future = cfgmod.today_label(), cfgmod.future_label(90)

    if (wiki / "sessions").exists():
        _rmtree(wiki / "sessions")
    for p in ctx["proposed"].glob("*"):
        p.unlink()
    ctx["proposed"].mkdir(parents=True, exist_ok=True)
    for cat in CATEGORIES:
        for p in (wiki / "project" / cat).glob("*"):
            if p.name != "README.md":
                p.unlink()
    if (nb / "raw" / "sessions").exists():
        _rmtree(nb / "raw" / "sessions")
    (nb / "raw" / "sessions").mkdir(parents=True, exist_ok=True)

    seeds = case.get("seeds") or {}
    persona_dir = wiki / "sessions" / PERSONA
    if seeds:
        persona_dir.mkdir(parents=True, exist_ok=True)

    def seed(name: str, dest: Path) -> None:
        text = (HERE / "fixtures" / "seeds" / name).read_text(encoding="utf-8")
        text = text.replace("{DATE}", today).replace("{FUTURE}", future).replace("{SID}", SID)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")

    if "journal" in seeds:
        seed(seeds["journal"], persona_dir / today[:7] / f"{today}-{SID}.md")
    if "handoff" in seeds:
        seed(seeds["handoff"], persona_dir / "handoff.md")
    if "task" in seeds:
        seed(seeds["task"], persona_dir / "task.md")
    if "active" in seeds:
        seed(seeds["active"], wiki / "sessions" / "active-context.md")

    # the skill-suggestion box (2026-09-26): top-level suggestions and an archive/ the skill must not read
    box = nb / "_inbox" / "skill-suggestions"
    if box.exists():
        _rmtree(box)
    sug = case.get("suggestions") or {}
    for name, body in (sug.get("box") or {}).items():
        box.mkdir(parents=True, exist_ok=True)
        (box / name).write_text(body, encoding="utf-8")
    for name, body in (sug.get("archive") or {}).items():
        (box / "archive").mkdir(parents=True, exist_ok=True)
        (box / "archive" / name).write_text(body, encoding="utf-8")

    flags = case.get("flags") or {}
    # the two owners' bots, as the real registry carries them: a sent suggestion is tagged to one.
    # `own_library` (2026-10-02, task #62) makes the test notebook that library's own notebook, as
    # llm-wiki-bootstrap is llm-wiki's: its entry carries the library's bot, and no other entry does
    own = case.get("own_library")
    owners = {name: {"root": f"notebooks/{name}", "discord": {"bot_name": bot, "user_id": uid}}
              for name, bot, uid in (("agent-builder-bootstrap", "agent-builder", AGENT_BUILDER_ID),
                                     ("llm-wiki-bootstrap", "llm-wiki", LLM_WIKI_ID)) if bot != own}
    entry = {"root": f"notebooks/{NOTEBOOK}", **flags}
    if case.get("registry_project_root"):  # the lint's code-drift check needs the repo (relative to the registry)
        entry["project_root"] = "project"
    if own:
        entry["discord"] = {"bot_name": own, "user_id": {"llm-wiki": LLM_WIKI_ID,
                                                         "agent-builder": AGENT_BUILDER_ID}[own]}
    ctx["registry"].write_text(json.dumps({"notebooks": {NOTEBOOK: entry, **owners}}, indent=2),
                               encoding="utf-8")
    cfg = json.dumps({"tool": "claude-code", "project_name": NOTEBOOK, "notebook": NOTEBOOK,
                      "persona": PERSONA, "registry": ctx["registry"].as_posix(),
                      "scripts_installed_at": ctx["scripts"].as_posix()}, indent=2)
    (ctx["project"] / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")
    (ctx["sandbox"] / ".claude").mkdir(exist_ok=True)
    (ctx["sandbox"] / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")

    # the notebooks repository (project-notebooks' stand-in): only for a commit case
    nbrepo = ctx["sandbox"] / "notebooks"
    if (nbrepo / ".git").exists():
        _rmtree(nbrepo / ".git")
    ctx["notebook_head"] = ""
    if case.get("git") == "session-changes":
        _git(nbrepo, "init", "-q")
        _git(nbrepo, "config", "user.email", "test@example.invalid")
        _git(nbrepo, "config", "user.name", "Skill Test")
        _git(nbrepo, "config", "core.longpaths", "true")
        _git(nbrepo, "add", "-A")
        _git(nbrepo, "commit", "-q", "-m", "notebook before the wrap-up")
        remote = _bare(ctx, "notebooks")
        _git(nbrepo, "remote", "add", "origin", remote.as_posix())
        _git(nbrepo, "push", "-q", "-u", "origin", "HEAD")
        ctx["notebook_head"] = _git(nbrepo, "rev-parse", "HEAD").strip()


def _reset_cards(case: dict, ctx: dict) -> None:
    """wiki/tasks/ back to this case's card seed, or gone: a project is on cards exactly when it has tasks/ORDER.md."""
    tasks = ctx["wiki"] / "tasks"
    if tasks.exists():
        _rmtree(tasks)
    seed = case.get("cards")
    if seed:
        shutil.copytree(HERE / "fixtures" / "cards" / seed, tasks)


HEADER = """You are running an automated test of the wrap-up skill. The skill under test is at {skill}/SKILL.md. Read it and follow it exactly, as if this were the end of a real session in this project. Do not use any installed copy of the skill.

You are in the `beacon` project at {project}; its notebook is `{notebook}` at {nb}, and this session's persona is `{persona}`. This session's id is `{sid}` — use it where the skill asks for a session id. Write only inside {sandbox}, and run scripts as the skill writes them, `uv run --project <scripts dir> python <path> ...`, with no environment-variable prefix.

The user cannot reply while this runs. Where the skill says to wait for the user, take the answers given below as already spoken; where it says to offer or ask something with no answer given, say in your final message what you would offer or ask, and do not act on an answer you do not have.

{work}

{answers}The user said: {say}"""


def prompt(case: dict, ctx: dict) -> str:
    _reset_project(case, ctx)
    _reset_cards(case, ctx)  # before the notebook reset: its git commit must not carry the last case's cards
    _reset_notebook(case, ctx)
    if case.get("living_seed"):
        dest = ctx["wiki"] / "project" / "architecture" / LIVING_NAME
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text((HERE / "fixtures" / "seeds" / case["living_seed"]).read_text(encoding="utf-8")
                        .replace("{BASE_COMMIT}", ctx.get("base_commit", "")), encoding="utf-8")
    for rel, name in (case.get("notebook_files") or {}).items():  # after the reset, which empties the category folders
        dest = ctx["wiki"] / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text((HERE / "fixtures" / "seeds" / name).read_text(encoding="utf-8"), encoding="utf-8")
    answers = []
    if case.get("answer"):
        answers.append(f"At the proposal table (Step 2), the user answers: `{case['answer']}`.")
    if case.get("promote_answer"):
        answers.append(f"At the promotion prompt (Step 6), the user answers: `{case['promote_answer']}`.")
    if case.get("suggestion_answer"):
        answers.append(f"Shown the skill suggestions, the user (Mark) answers: {case['suggestion_answer']}.")
    block = ("\n".join(answers) + "\n\n") if answers else ""
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), project=ctx["project"].as_posix(),
                         notebook=NOTEBOOK, nb=ctx["notebook"].as_posix(), persona=PERSONA, sid=SID,
                         sandbox=ctx["sandbox"].as_posix(), work=case["work"], answers=block,
                         say=case.get("say", "wrap up this session."))


def _journals(ctx: dict) -> list[Path]:
    root = ctx["wiki"] / "sessions" / PERSONA
    return sorted(p for p in root.rglob("*.md") if p.parent.name != PERSONA) if root.is_dir() else []


def _staged(ctx: dict) -> list[Path]:
    return sorted(ctx["proposed"].glob("*.md"))


def _promoted(ctx: dict) -> list[Path]:
    out = []
    for cat in CATEGORIES:
        out += [p for p in (ctx["wiki"] / "project" / cat).glob("*.md")
                if p.name not in ("README.md", "_INDEX.md")]
    return sorted(out)


def _read_cards(tasks: Path) -> tuple[dict, str]:
    """Every card under wiki/tasks (not ORDER.md) as file name -> {"fm", "body"}, and ORDER.md's text."""
    cards = {}
    for p in sorted(tasks.glob("*.md")):
        if p.name == "ORDER.md":
            continue
        text = p.read_text(encoding="utf-8")
        fm, body = {}, text
        m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", text, re.S)
        if m:
            body = m.group(2)
            for line in m.group(1).splitlines():
                k = re.match(r"([A-Za-z_]+):\s*(.*?)\s*$", line)
                if k and not line.startswith((" ", "\t")):
                    fm[k.group(1)] = k.group(2)
        cards[p.name] = {"fm": fm, "body": body}
    order_file = tasks / "ORDER.md"
    return cards, (order_file.read_text(encoding="utf-8") if order_file.is_file() else "")


def _cval(card: dict, key: str) -> str:
    v = str(card["fm"].get(key, "")).strip().strip("\"'").strip()
    return "" if v in EMPTY_VALUES else v


def _card_rule_problems(cards: dict, order: str) -> list[str]:
    """The six rules of a card project, each read from the files alone."""
    problems, ids = [], {}
    for name, c in cards.items():
        missing = [k for k in CARD_REQUIRED if not _cval(c, k)]
        if missing:
            problems.append(f"{name}: required field missing {missing}")
        cid = _cval(c, "id")
        if cid.isdigit():
            ids.setdefault(int(cid), []).append(name)
            if not re.match(rf"0*{int(cid)}-", name):
                problems.append(f"{name}: file name does not start with its id {cid}")
        else:
            problems.append(f"{name}: id {cid!r} is not a number")
        if _cval(c, "list") not in CARD_LISTS:
            problems.append(f"{name}: list {_cval(c, 'list')!r}")
        if _cval(c, "status") not in CARD_STATUSES:
            problems.append(f"{name}: status {_cval(c, 'status')!r}")
        if (_cval(c, "status") == "waiting") != bool(_cval(c, "waiting_on")):
            problems.append(f"{name}: waiting_on must be filled exactly when status is waiting")
    problems += [f"id {i} on several cards {n}" for i, n in ids.items() if len(n) > 1]
    order_ids = [int(i) for i in re.findall(r"^-\s*(\d+)\b", order, re.M)]
    problems += [f"id {i} listed twice in ORDER.md" for i in set(order_ids) if order_ids.count(i) > 1]
    current = {i for i, n in ids.items() if _cval(cards[n[0]], "list") == "current"}
    if current - set(order_ids):
        problems.append(f"current cards missing from ORDER.md: {sorted(current - set(order_ids))}")
    if set(order_ids) - current:
        problems.append(f"ORDER.md ids with no current card: {sorted(set(order_ids) - current)}")
    nxt = re.search(r"<!--\s*next-id:\s*(\d+)\s*-->", order)
    if not nxt:
        problems.append("ORDER.md has no next-id comment")
    elif ids and int(nxt.group(1)) <= max(ids):
        problems.append(f"next-id {nxt.group(1)} is not above the highest id {max(ids)}")
    return problems


def _log_lines(body: str):
    """The dated bullet lines under a `**Log**` heading, or None when the card has no such heading."""
    m = re.search(r"^\*\*Log\*\*:?\s*$", body, re.M)
    if not m:
        return None
    return [ln for ln in body[m.end():].splitlines() if re.match(r"-\s+\d{4}-\d{2}-\d{2}:\s*\S", ln)]


def _check_cards(case: dict, before: dict, after: dict, run: dict, ctx: dict, add) -> None:
    """kind "cards": a project on the task stack (wiki/tasks/ORDER.md exists). Reads the cards, never the commands."""
    from datetime import date
    exp = case.get("expect") or {}
    text = run["text"]
    today = date.today().isoformat()
    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    errs = run.get("error_texts") or {}
    denials = [d for d in (r.get("permission_denials") or [])
               if not (isinstance(d, dict) and "read-guard:" in str(errs.get(d.get("tool_use_id"), "")))]
    add("no permission denials", not denials,
        [d.get("tool_name") if isinstance(d, dict) else d for d in denials])

    wiki = ctx["wiki"]
    tasks = wiki / "tasks"
    cards, order = _read_cards(tasks)
    add("tasks/ORDER.md is still there", (tasks / "ORDER.md").is_file())
    problems = _card_rule_problems(cards, order)
    add("the six card rules hold", bool(cards) and not problems, problems or "no cards found")
    by_id = {int(_cval(c, "id")): c for c in cards.values() if _cval(c, "id").isdigit()}
    order_ids = [int(i) for i in re.findall(r"^-\s*(\d+)\b", order, re.M)]
    nxt = re.search(r"<!--\s*next-id:\s*(\d+)\s*-->", order)
    nxt = int(nxt.group(1)) if nxt else None

    user_done = {int(i) for i in (exp.get("user_done") or [])}
    # a task leaves the list only on the user's word: nothing deleted, list: done only for what the user said is done
    add("no card deleted (every seeded id still has a card)", SEED_CARD_IDS <= set(by_id),
        sorted(SEED_CARD_IDS - set(by_id)))
    done_list = {i for i, c in by_id.items() if _cval(c, "list") == "done"}
    add("no card moved to list: done except the user's own", done_list == {5} | user_done, sorted(done_list))

    touched = {int(k): v for k, v in (exp.get("touched") or {}).items()}
    for cid, want in touched.items():
        c = by_id.get(cid)
        add(f"touched card has the expected status, is still list current and still in ORDER.md ({cid})",
            c is not None and _cval(c, "status") == want and _cval(c, "list") == "current" and cid in order_ids,
            {k: _cval(c, k) for k in ("status", "list")} if c else "no such card")
        lines = _log_lines(c["body"]) if c else None
        add(f"touched card has exactly one Log line dated today under **Log** ({cid})",
            lines is not None and sum(1 for ln in lines if re.match(rf"-\s+{today}:\s*\S", ln)) == 1,
            lines if lines is not None else "no **Log** heading")
        add(f"touched card keeps its earlier Log line ({cid})", bool(c) and SEED_LOG[cid] in c["body"])
    seed_order_txt = _read_cards(HERE / "fixtures" / "cards" / case["cards"])[1]
    seed_order = [int(i) for i in re.findall(r"^-\s*(\d+)\b", seed_order_txt, re.M)]
    for cid in sorted(user_done):  # the user said it is done: done, list: done, off ORDER.md, card kept, Log, updated
        c = by_id.get(cid)
        add(f"the user's done task is status done and list: done ({cid})",
            c is not None and _cval(c, "status") == "done" and _cval(c, "list") == "done",
            {k: _cval(c, k) for k in ("status", "list")} if c else "no such card")
        add(f"it is out of ORDER.md and the other cards keep their order ({cid})",
            cid not in order_ids and [i for i in order_ids if i in seed_order] == [i for i in seed_order if i not in user_done],
            order_ids)
        lines = _log_lines(c["body"]) if c else None
        add(f"it has a Log line dated today under **Log** ({cid})",
            lines is not None and any(re.match(rf"-\s+{today}:\s*\S", ln) for ln in lines),
            lines if lines is not None else "no **Log** heading")
        add(f"it keeps its earlier Log line ({cid})", bool(c) and SEED_LOG[cid] in c["body"])
        add(f"its updated date is today ({cid})", c is not None and _cval(c, "updated") == today,
            _cval(c, "updated") if c else "no such card")
    # Mark's rule (2026-10-12): a card is rough notes; test for LOSS, never for how or where a thing was written
    seed_by_id_keep = {int(_cval(c, "id")): c for c in _read_cards(HERE / "fixtures" / "cards" / case["cards"])[0].values()
                       if _cval(c, "id").isdigit()}
    for k, spec in (exp.get("keeps") or {}).items():
        cid = int(k)
        c = by_id.get(cid)
        lost_fields = [f for f in spec.get("fields", [])
                       if c is None or _cval(c, f) != _cval(seed_by_id_keep[cid], f)]
        add(f"card {cid} lost none of its fields", not lost_fields, lost_fields or "")
        lost_body = [s for s in spec.get("body", []) if c is None or s not in c["body"]]
        add(f"card {cid} lost none of its details or Steps", not lost_body, lost_body or "")
    changed = []
    for cid, want in SEED_STATE.items():
        if cid in touched or cid in user_done:
            continue
        c = by_id.get(cid)
        got = {k: _cval(c, k) for k in want} if c else None
        if got != want:
            changed.append((cid, got))
    add("no other card changed its list, status, owner or waiting_on", not changed, changed)

    if exp.get("names"):
        add("the summary names the finished task", bool(re.search(exp["names"], text, re.I)))
    if exp.get("asks_remove"):  # a task the session finished itself: marked done, stays, the summary asks
        add("the summary asks whether to remove it", bool(ASKS_REMOVE.search(text)))
    if user_done:  # a task the user said is done: the summary says it was removed and does not ask
        add("the summary says the task was removed", bool(REMOVED.search(text)), text[-300:])
        add("the summary does not ask whether to remove the user's done task",
            not any(_asks_about_removing(text, cid, exp.get("names")) for cid in user_done), text[-300:])
    if exp.get("new_card"):
        new = sorted(i for i in by_id if i not in SEED_CARD_IDS)
        add("exactly one new card", len(new) == 1, new)
        if len(new) == 1:
            nc = by_id[new[0]]
            add("new card is list current and the last line of ORDER.md",
                _cval(nc, "list") == "current" and order_ids[-1:] == [new[0]], order_ids)
            add("next-id advanced past the seed's 6 and above the new id",
                nxt is not None and nxt > 6 and nxt > new[0], nxt)
            add("new card is about the manifest rotation",
                exp["new_card"] in (nc["body"] + _cval(nc, "title")).lower(), _cval(nc, "title"))

    # task.md on a card project is a pointer: no NOW/QUEUE section, no 'Earlier —' history
    persona_dir = wiki / "sessions" / PERSONA
    task_md = persona_dir / "task.md"
    if task_md.is_file():
        tt = task_md.read_text(encoding="utf-8")
        add("task.md carries no NOW or QUEUE section and no Earlier history",
            not re.search(r"(?m)^\s*(?:#{1,6}\s*|\*\*)?(?:NOW|QUEUE)\b", tt)
            and not re.search(r"Earlier\s*[—–-]", tt), tt[:120])

    # the handoff, the journal and active-context are written as on any project
    handoff = persona_dir / "handoff.md"
    add("handoff.md written with every section", handoff.is_file() and
        not [s for s in HANDOFF_SECTIONS if s not in handoff.read_text(encoding="utf-8")])
    journals = _journals(ctx)
    add("exactly one journal for this session, named with the session id",
        len(journals) == 1 and SID in journals[0].name, [p.name for p in journals])
    active = wiki / "sessions" / "active-context.md"
    add("active-context.md written with this persona's section",
        active.is_file() and f"## {PERSONA}" in active.read_text(encoding="utf-8"))
    final = str(run["result"].get("result") or "").strip().splitlines()
    last = final[-1].strip() if final else ""
    add("ends on the closing line", last == CLOSING[None], f"last line: {last[:120]!r}")
    wiki_rel = {k for k in set(before) | set(after) if before.get(k) != after.get(k) and k.startswith("wiki/")}
    stray = sorted(k for k in wiki_rel if not k.startswith(("wiki/sessions/", "wiki/tasks/")))
    add("wrote nothing into wiki/ but sessions/ and tasks/", not stray, stray)


def _asks_to_remove(text: str) -> bool:
    """The summary offers to remove the task: it says 'remove' and asks (a question mark or an open offer)."""
    return bool(ASKS_REMOVE.search(text) and OFFER.search(text))


def _preamble(run: dict, add) -> None:
    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    errs = run.get("error_texts") or {}
    denials = [d for d in (r.get("permission_denials") or [])
               if not (isinstance(d, dict) and "read-guard:" in str(errs.get(d.get("tool_use_id"), "")))]
    add("no permission denials", not denials,
        [d.get("tool_name") if isinstance(d, dict) else d for d in denials])


def _closing_line(run: dict, add) -> None:
    final = str(run["result"].get("result") or "").strip().splitlines()
    last = final[-1].strip() if final else ""
    add("ends on the closing line", last == CLOSING[None], f"last line: {last[:120]!r}")


def _check_cards_stack(case: dict, before: dict, after: dict, run: dict, ctx: dict, add) -> None:
    """kind "cards-stack": cards seeded from a fixture whose card `progressed` has no **Log** heading.
    The session finished card `finished` itself, progressed another, and was asked for a new task and a backlog task."""
    from datetime import date
    today = date.today().isoformat()
    exp, text = case["expect"], run["text"]
    _preamble(run, add)
    wiki = ctx["wiki"]
    tasks = wiki / "tasks"
    cards, order = _read_cards(tasks)
    seed_cards, seed_order = _read_cards(HERE / "fixtures" / "cards" / case["cards"])
    add("tasks/ORDER.md is still there", (tasks / "ORDER.md").is_file())
    problems = _card_rule_problems(cards, order)
    add("the six card rules hold", bool(cards) and not problems, problems or "no cards found")

    def by_id_of(cs):
        return {int(_cval(c, "id")): c for c in cs.values() if _cval(c, "id").isdigit()}

    def same(a, b):
        return a["fm"] == b["fm"] and a["body"].strip() == b["body"].strip()

    def core(c):  # a card without its updated date
        return ({k: v for k, v in c["fm"].items() if k != "updated"}, c["body"].strip())

    by_id, seed_by_id = by_id_of(cards), by_id_of(seed_cards)
    order_ids = [int(i) for i in re.findall(r"^-\s*(\d+)\b", order, re.M)]
    seed_order_ids = [int(i) for i in re.findall(r"^-\s*(\d+)\b", seed_order, re.M)]
    fid, pid = exp["finished"], exp["progressed"]

    add("no card deleted", set(seed_by_id) <= set(by_id), sorted(set(seed_by_id) - set(by_id)))
    done_now = {i for i, c in by_id.items() if _cval(c, "list") == "done"}
    done_seed = {i for i, c in seed_by_id.items() if _cval(c, "list") == "done"}
    add("no card moved to list: done (the user called none of them done)", done_now == done_seed, sorted(done_now))

    # A: the session finished card `fid` itself: marked done, stays, position kept, the summary asks
    fc = by_id.get(fid)
    add(f"card {fid} (finished by the session) is status done and still list current",
        fc is not None and _cval(fc, "status") == "done" and _cval(fc, "list") == "current",
        {k: _cval(fc, k) for k in ("status", "list")} if fc else "no such card")
    add(f"card {fid} keeps its position in ORDER.md",
        [i for i in order_ids if i in seed_by_id] == seed_order_ids, order_ids)
    add(f"card {fid}: id, title, owner, priority and created unchanged",
        fc is not None and all(_cval(fc, k) == _cval(seed_by_id[fid], k)
                               for k in ("id", "title", "owner", "priority", "created")))
    add("the summary names the finished task by its words", bool(re.search(exp["names"], text, re.I)))
    add("the summary asks whether to remove it", _asks_to_remove(text), text[-300:])

    # 7: card `pid` had no Log heading; logging to it creates one
    pc = by_id.get(pid)
    lines = _log_lines(pc["body"]) if pc else None
    add(f"card {pid} had no Log heading and now has one with a line dated today",
        lines is not None and any(re.match(rf"-\s+{today}:", ln) for ln in lines),
        lines if lines is not None else "no **Log** heading")
    add(f"card {pid} is still list current and not done",
        pc is not None and _cval(pc, "list") == "current" and _cval(pc, "status") != "done",
        {k: _cval(pc, k) for k in ("status", "list")} if pc else "no such card")

    # 8: every card the wrap-up touches has updated = today; the cards it did not touch are exactly as seeded
    stale = [i for i, sc in seed_by_id.items()
             if i in by_id and core(by_id[i]) != core(sc) and _cval(by_id[i], "updated") != today]
    add("every seeded card the wrap-up changed has updated = today", not stale, stale)
    add(f"cards {fid} and {pid} both have updated = today",
        all(c is not None and _cval(c, "updated") == today for c in (fc, pc)),
        [_cval(c, "updated") if c else None for c in (fc, pc)])
    moved = [i for i in seed_by_id if i not in (fid, pid) and (i not in by_id or not same(by_id[i], seed_by_id[i]))]
    add("the other seeded cards are exactly as they were", not moved, moved)

    # 10 and 11: the two new cards
    new = sorted(set(by_id) - set(seed_by_id))
    cur = [i for i in new if _cval(by_id[i], "list") == "current"]
    bak = [i for i in new if _cval(by_id[i], "list") == "backlog"]
    add("exactly two new cards: one current, one backlog", len(new) == 2 and len(cur) == 1 and len(bak) == 1,
        {i: _cval(by_id[i], "list") for i in new})
    if len(cur) == 1:
        nc = by_id[cur[0]]
        add("new current card: status ready, owner is this session's persona, in ORDER.md once",
            _cval(nc, "status") == "ready" and _cval(nc, "owner").lower() == PERSONA and order_ids.count(cur[0]) == 1,
            {k: _cval(nc, k) for k in ("status", "owner")})
        add("new current card is about the manifest rotation",
            "manifest" in (_cval(nc, "title") + nc["body"]).lower(), _cval(nc, "title"))
        add("new current card has created and updated = today",
            _cval(nc, "created") == today and _cval(nc, "updated") == today,
            (_cval(nc, "created"), _cval(nc, "updated")))
    if len(bak) == 1:
        nb_ = by_id[bak[0]]
        add("new backlog card: list backlog, status ready, owner is the user (Mark), not in ORDER.md",
            _cval(nb_, "status") == "ready" and _cval(nb_, "owner").lower() == "mark" and bak[0] not in order_ids,
            {k: _cval(nb_, k) for k in ("list", "status", "owner")} | {"in_order": bak[0] in order_ids})
        add("new backlog card is about the vendor's sandbox keys",
            bool(re.search(r"sandbox|vendor|account manager", (_cval(nb_, "title") + nb_["body"]).lower())),
            _cval(nb_, "title"))
        add("new backlog card has created and updated = today",
            _cval(nb_, "created") == today and _cval(nb_, "updated") == today,
            (_cval(nb_, "created"), _cval(nb_, "updated")))

    # 9: the task.md pointer is left exactly as it was
    ptr = wiki / "sessions" / PERSONA / "task.md"
    seed_ptr = (HERE / "fixtures" / "seeds" / "task-pointer.md").read_text(encoding="utf-8")
    add("task.md pointer left exactly as it was",
        ptr.is_file() and ptr.read_text(encoding="utf-8").replace("\r\n", "\n") == seed_ptr.replace("\r\n", "\n"),
        ptr.read_text(encoding="utf-8")[:120] if ptr.is_file() else "task.md is gone")

    _closing_line(run, add)
    wiki_rel = {k for k in set(before) | set(after) if before.get(k) != after.get(k) and k.startswith("wiki/")}
    stray = sorted(k for k in wiki_rel if not k.startswith(("wiki/sessions/", "wiki/tasks/")))
    add("wrote nothing into wiki/ but sessions/ and tasks/", not stray, stray)


def _check_staged_entries(case: dict, ctx: dict, add, living: str | None = None) -> None:
    """Entries staged by a full wrap-up on a card project: the same gate, front matter and sidecar rules as kind "full"."""
    gate = _load(ctx["scripts"], "_entry_checks.py", "entry_checks")
    staged = _staged(ctx)
    promoted = [p for p in _promoted(ctx) if p.name != living]  # the in-place living page is not a promotion
    add(f"at least {case['expect']['min_staged']} entries staged", len(staged) >= case["expect"]["min_staged"],
        [p.name for p in staged])
    add("nothing promoted without the user's yes", not promoted, [p.name for p in promoted])
    bad_gate, bad_fm, bad_src, missing, bad_target = [], [], [], [], []
    for p in staged:
        etext = p.read_text(encoding="utf-8")
        fm, _ = gate.split_frontmatter(etext)
        errs = gate.check_entry_text(etext)["errors"]
        if errs:
            bad_gate.append(f"{p.stem}: {errs[:2]}")
        if not (str(fm.get("tier")) == "self" and str(fm.get("origin")) == "wrap-up"
                and str(fm.get("category")) in ("component", "decision", "architecture", "pattern", "troubleshooting")):
            bad_fm.append(f"{p.stem}: tier={fm.get('tier')} origin={fm.get('origin')} category={fm.get('category')}")
        if not str(fm.get("source_url", "")).startswith("internal://"):
            bad_src.append(f"{p.stem}: {fm.get('source_url')}")
        side = p.with_name(f"{p.stem}.proposed_metadata.json")
        try:
            tf = str(json.loads(side.read_text(encoding="utf-8")).get("target_folder", ""))
        except (OSError, json.JSONDecodeError):
            missing.append(p.stem)
            continue
        if not (tf.startswith("project/") and tf.split("/")[-1] in CATEGORIES):
            bad_target.append(f"{p.stem}: {tf!r}")
    add(f"all {len(staged)} entries pass the entry gate", staged and not bad_gate, bad_gate)
    add("every entry: tier self, origin wrap-up, a real category", staged and not bad_fm, bad_fm)
    add("every entry: source_url is internal://", staged and not bad_src, bad_src)
    add("every entry has a readable sidecar", staged and not missing, missing)
    add("every sidecar names project/<plural folder>", staged and not bad_target, bad_target)
    proc = subprocess.run(
        [sys.executable, str(ctx["scripts"] / "wiki-promote.py"), "--topic", NOTEBOOK, "--check"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}, cwd=str(ctx["project"]))
    add("every staged entry would promote (wiki-promote --check)", proc.returncode == 0,
        (proc.stdout or "")[-260:] + (proc.stderr or "")[-120:])


def _check_cards_full(case: dict, before: dict, after: dict, run: dict, ctx: dict, add) -> None:
    """kind "cards-full": a full wrap-up (table go, promotion no) on a card project where the user said a task
    is done: the entries are staged as in kind "full" AND the card checks of kind "cards" hold (task off the list
    without a question, card kept whole, Log line today, no task.md written)."""
    _check_cards(case, before, after, run, ctx, add)
    _check_staged_entries(case, ctx, add)


def _check_cards_first(case: dict, before: dict, after: dict, run: dict, ctx: dict, add) -> None:
    """kind "cards-first": a project with NO wiki/tasks/ yet. The user asks for a task; the wrap-up starts the list
    (tasks/ORDER.md with one current card), the six rules hold, and no task.md is written."""
    from datetime import date
    today = date.today().isoformat()
    exp = case["expect"]
    _preamble(run, add)
    wiki = ctx["wiki"]
    tasks = wiki / "tasks"
    add("tasks/ORDER.md was created", (tasks / "ORDER.md").is_file())
    cards, order = _read_cards(tasks) if tasks.is_dir() else ({}, "")
    problems = _card_rule_problems(cards, order)
    add("the six card rules hold", bool(cards) and not problems, problems or "no cards found")
    add("exactly one card", len(cards) == 1, sorted(cards))
    if len(cards) == 1:
        c = next(iter(cards.values()))
        cid = _cval(c, "id")
        order_ids = [int(i) for i in re.findall(r"^-\s*(\d+)\b", order, re.M)]
        add("the card is list current, not done, and the only line of ORDER.md",
            _cval(c, "list") == "current" and _cval(c, "status") != "done"
            and cid.isdigit() and order_ids == [int(cid)],
            {"list": _cval(c, "list"), "status": _cval(c, "status"), "order": order_ids})
        add("the card is about the manifest rotation",
            exp["new_card"] in (_cval(c, "title") + c["body"]).lower(), _cval(c, "title"))
        add("the card has created and updated = today",
            _cval(c, "created") == today and _cval(c, "updated") == today,
            (_cval(c, "created"), _cval(c, "updated")))
    persona_dir = wiki / "sessions" / PERSONA
    add("no task.md written", not (persona_dir / "task.md").exists())
    handoff = persona_dir / "handoff.md"
    add("handoff.md written with every section", handoff.is_file() and
        not [s for s in HANDOFF_SECTIONS if s not in handoff.read_text(encoding="utf-8")])
    journals = _journals(ctx)
    add("exactly one journal for this session, named with the session id",
        len(journals) == 1 and SID in journals[0].name, [p.name for p in journals])
    active = wiki / "sessions" / "active-context.md"
    add("active-context.md written with this persona's section",
        active.is_file() and f"## {PERSONA}" in active.read_text(encoding="utf-8"))
    add("nothing staged (the user answered none)", not _staged(ctx), [p.name for p in _staged(ctx)])
    _closing_line(run, add)
    wiki_rel = {k for k in set(before) | set(after) if before.get(k) != after.get(k) and k.startswith("wiki/")}
    stray = sorted(k for k in wiki_rel if not k.startswith(("wiki/sessions/", "wiki/tasks/")))
    add("wrote nothing into wiki/ but sessions/ and tasks/", not stray, stray)


LIVING_NAME = "20-upload-sync.md"
LIVING_DESCRIBES = "beacon/manifest.py"
LIVING_OLD = "written when its upload starts, before any bytes are sent"
LIVING_KEEP = "Chunk size is 8 MiB"
LIVING_SEED_DATE = "2026-08-01"
LIVING_HEADINGS = ("How it works", "Rules and settings", "Known gaps and bugs", "History")


def _arch_files(ctx: dict) -> list[Path]:
    d = ctx["wiki"] / "project" / "architecture"
    return sorted(p for p in d.glob("*.md") if p.name != "README.md") if d.is_dir() else []


def _staged_architecture(ctx: dict, gate) -> list[str]:
    out = []
    for p in _staged(ctx):
        fm, _ = gate.split_frontmatter(p.read_text(encoding="utf-8"))
        tf = ""
        try:
            tf = str(json.loads(p.with_name(f"{p.stem}.proposed_metadata.json").read_text(encoding="utf-8"))
                     .get("target_folder", ""))
        except (OSError, json.JSONDecodeError):
            pass
        if tf.rstrip("/").endswith("architecture") or str(fm.get("category")) == "architecture":
            out.append(p.name)
    return out


def _section(body: str, name: str) -> str:
    m = re.search(rf"(?im)^#{{1,6}}\s*{re.escape(name)}\s*$", body)
    if not m:
        return ""
    rest = body[m.end():]
    n = re.search(r"(?m)^#{1,6}\s", rest)
    return rest[:n.start()] if n else rest


def _check_living(case: dict, before: dict, after: dict, run: dict, ctx: dict, add) -> None:
    """kinds "living-revise" and "living-none" (task #172): the wrap-up's living-page step.
    Reads the architecture folder, the page's frontmatter and body, the staged sidecars and the reply."""
    gate = _load(ctx["scripts"], "_entry_checks.py", "entry_checks")
    today = _load(ctx["scripts"], "_wiki_config.py", "wiki_config").today_label()
    exp, text = case["expect"], run["text"]
    _preamble(run, add)
    arch = _arch_files(ctx)
    page = ctx["wiki"] / "project" / "architecture" / LIVING_NAME
    staged_arch = _staged_architecture(ctx, gate)
    journals = _journals(ctx)
    add("exactly one journal for this session, named with the session id",
        len(journals) == 1 and SID in journals[0].name, [p.name for p in journals])
    handoff = ctx["wiki"] / "sessions" / PERSONA / "handoff.md"
    add("handoff.md written with every section", handoff.is_file() and
        not [s for s in HANDOFF_SECTIONS if s not in handoff.read_text(encoding="utf-8")])
    _check_staged_entries(case, ctx, add, living=LIVING_NAME)
    _closing_line(run, add)
    wiki_rel = {k for k in set(before) | set(after) if before.get(k) != after.get(k) and k.startswith("wiki/")}
    living_key = "wiki/project/architecture/" + LIVING_NAME
    allowed = living_key if exp["living"] == "revised" else None
    # a path the previous case left and the prompt-time reset removed shows as changed (gone from `after`):
    # that is the harness, not the session
    stray = sorted(k for k in wiki_rel
                   if not k.startswith("wiki/sessions/") and k != allowed
                   and not (k == living_key and k not in after))
    add("wrote nothing into wiki/ but sessions/ (and the living page, when there is one)", not stray, stray)

    if exp["living"] == "revised":
        seed = (HERE / "fixtures" / "seeds" / case["living_seed"]).read_text(encoding="utf-8")
        ptext = page.read_text(encoding="utf-8") if page.is_file() else ""
        fm, body = gate.split_frontmatter(ptext)
        add("the living page is edited in place: it is still there and is the only architecture page",
            page.is_file() and arch == [page], [p.name for p in arch])
        add("frontmatter keeps kind: living and describes:",
            str(fm.get("kind")) == "living" and str(fm.get("describes")) == LIVING_DESCRIBES,
            {k: fm.get(k) for k in ("kind", "describes")})
        add("last_reviewed is the session's date", str(fm.get("last_reviewed")) == today,
            f"last_reviewed {fm.get('last_reviewed')!r}, today {today}")
        add("the page was changed and the old claim is gone",
            ptext.replace("\r\n", "\n") != seed.replace("\r\n", "\n") and LIVING_OLD not in ptext, ptext[:300])
        add("the page now says the new behaviour (written after the etag / confirmation)",
            bool(re.search(r"etag|confirm", body, re.I)), body[:300])
        add("content the change did not touch is kept", LIVING_KEEP in ptext)
        add("the four sections are still there", all(re.search(rf"(?im)^#{{1,6}}\s*{h}\s*$", body) for h in LIVING_HEADINGS),
            [h for h in LIVING_HEADINGS if not re.search(rf"(?im)^#{{1,6}}\s*{h}\s*$", body)])
        seed_hist = _section(gate.split_frontmatter(seed)[1], "History")
        hist = _section(body, "History")
        add("History gained a line that links the session's note",
            len(hist.strip().splitlines()) > len(seed_hist.strip().splitlines()) and bool(re.search(r"\[\[|\]\(|\.md", hist)),
            hist[-200:])
        add("no new entry is staged for wiki/project/architecture/", not staged_arch, staged_arch)
        names_page = re.compile(r"20-upload-sync|upload[- ]sync", re.I)
        add("the proposal table has a row for the living page",
            any(ln.lstrip().startswith("|") and names_page.search(ln) for ln in text.splitlines()))
        tail = text.splitlines()[-40:]
        add("the summary reports the living page revised",
            any(names_page.search(ln) and re.search(r"revis|updat|correct|edit|chang|rewr", ln, re.I) for ln in tail),
            tail[-6:])
    else:
        add("no architecture page was created", not arch, [p.name for p in arch])
        add("no entry is staged for wiki/project/architecture/", not staged_arch, staged_arch)
        neg = re.compile(r"\b(no|not|none|nothing|without|skipp\w*|n/a)\b|n't", re.I)
        claims = [ln for ln in text.splitlines()
                  if re.search(r"(living|architecture) page", ln, re.I)
                  and re.search(r"revised|updated|edited|corrected", ln, re.I) and not neg.search(ln)]
        add("the summary does not claim a living-page revision", not claims, claims[:2])


# ---- R1/R2 (2026-10-22): the final staleness check on living pages, and the pin that moves with a revision
RETRY_NAME = "30-retry-policy.md"
RETRY_NOTE = "retry-budget-replaces-attempt-cap.md"
RETRY_SEED_PAGE = "living-retry-policy.md"
RETRY_SEED_NOTE = "decision-retry-budget.md"
RETRY_OLD = "capped at 5 attempts per file"
RETRY_KEEP = "Per-request timeout is 30 seconds"
RETRY_NOTE_TITLE = "Retry budget replaces the attempt cap"
MANIFEST_SESSION_EDIT = (
    "\n\ndef uploaded_keys(manifest: Path) -> set[str]:\n"
    "    \"\"\"Keys the remote has confirmed; a resumed sync skips exactly these.\"\"\"\n"
    "    if not manifest.is_file():\n"
    "        return set()\n"
    "    return {row[\"key\"] for row in json.loads(manifest.read_text(encoding=\"utf-8\"))}\n")


def _norm_nl(s: str) -> str:
    return s.replace("\r\n", "\n").strip()


def _wiki_stray(before: dict, after: dict, allowed: set) -> list[str]:
    """wiki/ paths the session changed outside sessions/ and `allowed`. A path gone from `after` is the
    prompt-time reset removing the previous case's leftover: the harness, not the session."""
    changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k) and k.startswith("wiki/")}
    return sorted(k for k in changed
                  if not k.startswith("wiki/sessions/") and k not in allowed and k in after)


def _check_living_stale(case: dict, before: dict, after: dict, run: dict, ctx: dict, add) -> None:
    """kind "living-stale" (R1): a living page the session never touched is behind a later decision note.
    The wrap-up's final check must leave it revised in place or named in the handoff's WAITING ON YOU with a
    reason, and the report must say so. Either outcome passes; silence fails."""
    gate = _load(ctx["scripts"], "_entry_checks.py", "entry_checks")
    today = _load(ctx["scripts"], "_wiki_config.py", "wiki_config").today_label()
    wiki = ctx["wiki"]
    seeds = HERE / "fixtures" / "seeds"
    _preamble(run, add)
    journals = _journals(ctx)
    add("exactly one journal for this session, named with the session id",
        len(journals) == 1 and SID in journals[0].name, [p.name for p in journals])
    handoff = wiki / "sessions" / PERSONA / "handoff.md"
    htext = handoff.read_text(encoding="utf-8") if handoff.is_file() else ""
    add("handoff.md written with every section",
        handoff.is_file() and not [s for s in HANDOFF_SECTIONS if s not in htext])
    add("nothing staged (the user answered none)", not _staged(ctx), [p.name for p in _staged(ctx)])
    _closing_line(run, add)

    page_rel = "wiki/project/architecture/" + RETRY_NAME
    note_rel = "wiki/project/decisions/" + RETRY_NOTE
    add("wrote nothing into wiki/ but sessions/ and the seeded retry page and note",
        not _wiki_stray(before, after, {page_rel, note_rel}), _wiki_stray(before, after, {page_rel, note_rel}))
    note_p = wiki / "project" / "decisions" / RETRY_NOTE
    seed_note = (seeds / RETRY_SEED_NOTE).read_text(encoding="utf-8")
    add("the decision note is left as it was",
        note_p.is_file() and _norm_nl(note_p.read_text(encoding="utf-8")) == _norm_nl(seed_note))
    add("no other architecture page was created",
        [p.name for p in _arch_files(ctx)] == [RETRY_NAME], [p.name for p in _arch_files(ctx)])

    page_p = wiki / "project" / "architecture" / RETRY_NAME
    seed_page = (seeds / RETRY_SEED_PAGE).read_text(encoding="utf-8")
    ptext = page_p.read_text(encoding="utf-8") if page_p.is_file() else ""
    revised = _norm_nl(ptext) != _norm_nl(seed_page)
    wait_at = htext.rfind("WAITING ON YOU")
    wait = htext[wait_at:] if wait_at >= 0 else ""
    named_lines = [ln for ln in wait.splitlines() if "30-retry-policy" in ln]
    reason = any(len(re.findall(r"[A-Za-z]{3,}", ln.replace("30-retry-policy.md", "").replace("30-retry-policy", ""))) >= 5
                 for ln in named_lines)
    add("the flagged living page is revised in place, or named in WAITING ON YOU with its path and a reason",
        revised or (bool(named_lines) and reason),
        {"revised": revised, "named_lines": named_lines[:2], "reason_given": reason})

    if revised:  # the same rules as the living-page step
        fm, body = gate.split_frontmatter(ptext)
        hist = _section(body, "History")
        seed_hist = _section(gate.split_frontmatter(seed_page)[1], "History")
        rest = body.replace(hist, "") if hist else body
        add("the revised page keeps kind: living", str(fm.get("kind")) == "living", fm.get("kind"))
        add("last_reviewed is the session's date", str(fm.get("last_reviewed")) == today,
            f"last_reviewed {fm.get('last_reviewed')!r}, today {today}")
        add("the old claim (an attempt cap) is gone from the page body", RETRY_OLD not in rest, rest[:300])
        add("the page now says the retry budget (elapsed time) rule",
            bool(re.search(r"120|elapsed|budget", rest, re.I)), rest[:300])
        add("content the note did not change is kept", RETRY_KEEP in ptext)
        add("History gained a line that links the note",
            len(hist.strip().splitlines()) > len(seed_hist.strip().splitlines())
            and ("retry-budget-replaces-attempt-cap" in hist or RETRY_NOTE_TITLE.lower() in hist.lower()), hist[-200:])

    report = str(run["result"].get("result") or "") or run["text"]
    rlines = report.splitlines()
    page_lines = [ln for ln in rlines if re.search(r"30-retry-policy|retry[- ]policy", ln, re.I)]
    add("the report names the retry page", bool(page_lines), report[-300:])
    add("the report says what happened to it",
        any(re.search(r"revis|updat|correct|edit|rewr|chang|fix|waiting|flag|decid|needs|unable|can.?t|cannot|left", ln, re.I)
            for ln in page_lines), page_lines[:3])
    add("the report says how many living pages the final check flagged (one)",
        any(re.search(r"flag|stale|lint|final check|behind", ln, re.I) and re.search(r"\b(1|one)\b", ln, re.I)
            for ln in rlines), rlines[-12:])


def _check_living_pin(case: dict, before: dict, after: dict, run: dict, ctx: dict, add) -> None:
    """kind "living-pin" (R2): the page the session's change touched is revised, and its pinned `describes:`
    moves to the path's latest commit (expect.pin "latest"), or to the bare path while the path has uncommitted
    changes (expect.pin "bare"). kind: living and the path are kept."""
    gate = _load(ctx["scripts"], "_entry_checks.py", "entry_checks")
    today = _load(ctx["scripts"], "_wiki_config.py", "wiki_config").today_label()
    exp = case["expect"]
    wiki = ctx["wiki"]
    project = ctx["project"]
    _preamble(run, add)
    journals = _journals(ctx)
    add("exactly one journal for this session, named with the session id",
        len(journals) == 1 and SID in journals[0].name, [p.name for p in journals])
    handoff = wiki / "sessions" / PERSONA / "handoff.md"
    add("handoff.md written with every section", handoff.is_file() and
        not [s for s in HANDOFF_SECTIONS if s not in handoff.read_text(encoding="utf-8")])
    _check_staged_entries(case, ctx, add, living=LIVING_NAME)
    _closing_line(run, add)
    living_key = "wiki/project/architecture/" + LIVING_NAME
    add("wrote nothing into wiki/ but sessions/ and the living page",
        not _wiki_stray(before, after, {living_key}), _wiki_stray(before, after, {living_key}))

    page = wiki / "project" / "architecture" / LIVING_NAME
    arch = _arch_files(ctx)
    ptext = page.read_text(encoding="utf-8") if page.is_file() else ""
    fm, body = gate.split_frontmatter(ptext)
    seed = (HERE / "fixtures" / "seeds" / case["living_seed"]).read_text(encoding="utf-8")
    add("the living page is edited in place: still there and the only architecture page",
        page.is_file() and arch == [page], [p.name for p in arch])
    add("frontmatter keeps kind: living", str(fm.get("kind")) == "living", fm.get("kind"))
    add("last_reviewed is the session's date", str(fm.get("last_reviewed")) == today,
        f"last_reviewed {fm.get('last_reviewed')!r}, today {today}")
    add("the page was changed and the old claim is gone",
        _norm_nl(ptext) != _norm_nl(seed.replace("{BASE_COMMIT}", "")) and LIVING_OLD not in ptext, ptext[:300])
    add("the page now says the new behaviour (written after the etag / confirmation)",
        bool(re.search(r"etag|confirm", body, re.I)), body[:300])
    add("content the change did not touch is kept", LIVING_KEEP in ptext)
    hist = _section(body, "History")
    seed_hist = _section(gate.split_frontmatter(seed)[1], "History")
    add("History gained a line that links the session's note",
        len(hist.strip().splitlines()) > len(seed_hist.strip().splitlines()) and bool(re.search(r"\[\[|\]\(|\.md", hist)),
        hist[-200:])

    desc = str(fm.get("describes") or "").strip()
    path, sep, pin = desc.partition("@")
    if exp["pin"] == "latest":
        want = _git(project, "log", "-1", "--format=%H", "--", LIVING_DESCRIBES).strip()
        got = (_git(project, "rev-parse", "--verify", "-q", f"{pin}^{{commit}}").strip()
               if re.fullmatch(r"[0-9a-f]{7,40}", pin) else "")
        add("describes is the path pinned at the path's latest commit (short or full hash)",
            path == LIVING_DESCRIBES and bool(sep) and bool(want) and got == want,
            {"describes": desc, "latest_commit": want[:12], "pin_resolves_to": got[:12]})
        add("code drift would clear: the path is identical between the pin and the working tree",
            bool(got) and not _git(project, "diff", "--name-only", got, "--", LIVING_DESCRIBES).strip(), desc)
    else:
        add("describes is the bare path (the path still has uncommitted changes), no pin",
            desc == LIVING_DESCRIBES, desc)


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    gate = _load(ctx["scripts"], "_entry_checks.py", "entry_checks")
    cfgmod = _load(ctx["scripts"], "_wiki_config.py", "wiki_config")
    today = cfgmod.today_label()
    res: list[dict] = []
    exp = case.get("expect") or {}
    text = run["text"]

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    if case.get("kind") == "cost-none":
        # task #182 row 34: with no running total for the session, the report's cost line says the cost was
        # not checked and why, and carries no dollar figure (never a guessed or zero one)
        _preamble(run, add)
        cost_lines = [ln.strip() for ln in text.splitlines() if re.search(r"\bcost", ln, re.I)]
        not_checked = re.compile(r"not\s+checked|unchecked|not\s+available|unavailable|no\s+(running\s+)?(total|cost)|"
                                 r"could\s*n[o']t|couldn'?t|unable|not\s+(been\s+)?(read|found|recorded|reported)", re.I)
        add("the report has a line about the session's cost", bool(cost_lines), text[-300:])
        nc = [ln for ln in cost_lines if not_checked.search(ln)]
        add("the cost line says the cost was not checked", bool(nc), cost_lines[:3])
        figures = [ln for ln in cost_lines
                   if re.search(r"\$\s*\d|\b\d+(?:\.\d+)?\s*(?:usd|dollars)\b", ln, re.I)]
        add("no cost line carries a dollar figure (no guessed or zero cost)", not figures, figures[:2])
        add("the not-checked line gives a reason",
            any(len(re.findall(r"[A-Za-z]{3,}",
                               re.sub(r"(?i)cost|not\s+checked|unchecked", "", ln))) >= 3 for ln in nc),
            nc[:2])
        _closing_line(run, add)
        return res

    if case.get("kind") == "cards":
        _check_cards(case, before, after, run, ctx, add)
        return res
    if case.get("kind") == "cards-stack":
        _check_cards_stack(case, before, after, run, ctx, add)
        return res
    if case.get("kind") == "cards-full":
        _check_cards_full(case, before, after, run, ctx, add)
        return res
    if case.get("kind") == "cards-first":
        _check_cards_first(case, before, after, run, ctx, add)
        return res
    if case.get("kind") == "docs-check":
        # task #130: a docs check in wrap-up. Reads the project's docs/usage.md and the report, never the commands.
        _preamble(run, add)
        proj_files = HERE / "fixtures" / "project-files"

        def _norm(s):
            return s.replace("\r\n", "\n").strip()

        usage_p = ctx["project"] / "docs" / "usage.md"
        usage = usage_p.read_text(encoding="utf-8") if usage_p.is_file() else ""
        overlay = HERE / "fixtures" / "project-overlays" / case.get("project_overlay", "docs-resume")
        seed_usage = (overlay / "docs" / "usage.md").read_text(encoding="utf-8")
        cli_p = ctx["project"] / "beacon" / "cli.py"
        seed_cli = (overlay / "beacon" / "cli.py").read_text(encoding="utf-8")
        add("beacon/cli.py left as the session made it",
            cli_p.is_file() and _norm(cli_p.read_text(encoding="utf-8")) == _norm(seed_cli))
        doc_word = re.compile(r"read\s*me|usage|\bdocs?\b|documentation", re.I)
        sents = [s.strip() for s in re.split(r"(?<=[.!?;])\s+|\n+", text) if s.strip() and doc_word.search(s)]
        neg = re.compile(r"\b(nothing|none|no|not|never|without|didn'?t|wasn'?t|weren'?t|isn'?t|n/a)\b|n't", re.I)
        clean = re.compile(r"\b(clean|up[- ]to[- ]date|still (true|accurate|correct|current)|all accurate|"
                           r"all correct|no stale|verified|checked|audited)\b", re.I)
        if exp.get("docs") == "fixed":
            add("usage page now describes the new default: names --no-resume",
                "--no-resume" in usage, usage[:200])
            add("usage page no longer says resuming is off by default or tells the reader to pass --resume",
                not re.search(r"off by default|pass\s+`?--resume", usage, re.I), usage[:200])
            add("usage page was edited (differs from the stale seed)", _norm(usage) != _norm(seed_usage))
            doc_lines = [ln.strip() for ln in text.splitlines() if ln.strip() and doc_word.search(ln)]
            add("the report says the docs check found and fixed the stale claim",
                any(re.search(r"fix|updat|correct|chang|stale|out[- ]of[- ]date|untrue|no longer true|rewr", ln, re.I)
                    for ln in doc_lines), doc_lines[:3])
        else:
            add("usage page unchanged", _norm(usage) == _norm(seed_usage), usage[:200])
            readme_p = ctx["project"] / "README.md"
            add("README unchanged",
                readme_p.is_file() and _norm(readme_p.read_text(encoding="utf-8"))
                == _norm((proj_files / "README.md").read_text(encoding="utf-8")))
            add("the report says there was nothing for the docs check to check",
                any(re.search(r"nothing\b[^.;\n]{0,60}\b(to check|to audit|to verify|for the (docs? )?check|chang|describ|touch|affect|appl)|"
                              r"no (code|script|command|flag|behaviou?r|doc)[^.;\n]{0,40}(chang|touch|affect|describ)|"
                              r"none of|not (needed|applicable|run)|n/a|skipp|did not (check|run|audit)|"
                              r"didn'?t (check|run|audit)|not checked|no docs? check", s, re.I)
                    for s in sents), sents[:3])
            claims = [s for s in sents if clean.search(s) and not neg.search(s)]
            add("the report does not claim a clean docs check it did not make", not claims, claims[:2])
        persona_dir = ctx["wiki"] / "sessions" / PERSONA
        journals = _journals(ctx)
        add("exactly one journal for this session, named with the session id",
            len(journals) == 1 and SID in journals[0].name, [p.name for p in journals])
        handoff = persona_dir / "handoff.md"
        add("handoff.md written with every section", handoff.is_file() and
            not [s for s in HANDOFF_SECTIONS if s not in handoff.read_text(encoding="utf-8")])
        _closing_line(run, add)
        wiki_rel = {k for k in set(before) | set(after) if before.get(k) != after.get(k) and k.startswith("wiki/")}
        stray = sorted(k for k in wiki_rel if not k.startswith(("wiki/sessions/", "wiki/tasks/")))
        add("wrote nothing into wiki/ but sessions/ and tasks/", not stray, stray)
        return res

    if case.get("kind") in ("living-revise", "living-none"):
        _check_living(case, before, after, run, ctx, add)
        return res
    if case.get("kind") == "living-stale":
        _check_living_stale(case, before, after, run, ctx, add)
        return res
    if case.get("kind") == "living-pin":
        _check_living_pin(case, before, after, run, ctx, add)
        return res
    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    # the machine's global read-guard hook refusing a partial read is not harness friction:
    # the session reads the file whole and goes on (2026-09-24, as in the wiki-cycle suite)
    errs = run.get("error_texts") or {}
    denials = [d for d in (r.get("permission_denials") or [])
               if not (isinstance(d, dict) and "read-guard:" in str(errs.get(d.get("tool_use_id"), "")))]
    add("no permission denials", not denials,
        [d.get("tool_name") if isinstance(d, dict) else d for d in denials])

    # ---- Step 0: the session journal, one per session, appended not rewritten
    journals = _journals(ctx)
    add("exactly one journal for this session", len(journals) == 1, [p.name for p in journals])
    if len(journals) == 1:
        j = journals[0]
        jtext = j.read_text(encoding="utf-8")
        fm, body = gate.split_frontmatter(jtext)
        add("journal is in sessions/<persona>/<YYYY-MM>/", j.parent.name == today[:7], j.parent.name)
        add("journal filename carries the session id", SID in j.name, j.name)
        add("journal frontmatter: session_id, type, tier",
            str(fm.get("session_id")) == SID and fm.get("type") == "session-journal"
            and str(fm.get("tier")) == "self",
            {k: fm.get(k) for k in ("session_id", "type", "tier")})
        add("journal has Goal and Next", "**Goal:**" in body and "**Next:**" in body)
        # the Next block, not its first physical line: models wrap it, and the file names
        # routinely land on line two (opus, 2026-09-17)
        blines, nxt = body.splitlines(), []
        for i, ln in enumerate(blines):
            if ln.startswith("**Next:**"):
                nxt.append(ln)
                for cont in blines[i + 1:]:
                    if not cont.strip() or cont.startswith(("#", "**", "- ")):
                        break
                    nxt.append(cont)
                break
        nxt = " ".join(nxt)
        add("Next names a file for a cold start", bool(re.search(r"[\w./\\-]+\.(py|md|json)", nxt)), nxt[:200])
        updates = re.findall(r"^### Update\s*(\d+)", body, re.M)
        if exp.get("journal") == "append":
            add("appended a second update block", len(updates) >= 2, updates)
            add("Update 1 kept word for word", "Sketched `RetryBudget` as an elapsed-time allowance" in body)
            add("original Goal line preserved or refreshed, not dropped", "**Goal:**" in body)
        else:
            add("seeded the first update block", len(updates) >= 1, updates)

    # ---- Step 0.5: the dashboards (these cases have no task cards and no task to record)
    persona_dir = ctx["wiki"] / "sessions" / PERSONA
    handoff, task_md = persona_dir / "handoff.md", persona_dir / "task.md"
    active = ctx["wiki"] / "sessions" / "active-context.md"
    add("handoff.md written", handoff.is_file())
    if handoff.is_file():
        htext = handoff.read_text(encoding="utf-8")
        missing = [s for s in HANDOFF_SECTIONS if s not in htext]
        add("handoff.md has every section", not missing, missing)
        # task #84 (Mark, 2026-10-06): he reads from the bottom up, so what waits on him is the last section
        wait_at = htext.rfind("WAITING ON YOU")
        add("handoff.md ends on the WAITING ON YOU section",
            wait_at >= 0 and all(htext.rfind(s) < wait_at for s in HANDOFF_SECTIONS),
            htext[wait_at:wait_at + 120] if wait_at >= 0 else "no WAITING ON YOU section")
        add("handoff.md reflects this session, not the seed",
            "RetryBudget" in htext or "retry" in htext.lower())
    add("no task.md written (the task list is the cards)", not task_md.exists())
    add("active-context.md written", active.is_file())
    if active.is_file():
        atext = active.read_text(encoding="utf-8")
        add("active-context has this persona's section", f"## {PERSONA}" in atext)
        if exp.get("keeps_other_persona") or (case.get("seeds") or {}).get("active"):
            add("other persona's section untouched",
                "Waiting on the vendor about etag semantics" in atext)

    # ---- Steps 1-3: staging
    staged, promoted = _staged(ctx), _promoted(ctx)
    if exp.get("promoted"):
        add("entries promoted into project/", len(promoted) >= exp.get("min_staged", 1),
            [p.name for p in promoted])
        add("staging emptied by the promote", not staged, [p.name for p in staged])
        entries = promoted
    elif "staged" in exp:
        add(f"nothing staged ({exp['staged']} expected)", len(staged) == exp["staged"],
            [p.name for p in staged])
        add("nothing filed into project/", not promoted, [p.name for p in promoted])
        entries = []
    else:
        add(f"at least {exp['min_staged']} entries staged", len(staged) >= exp["min_staged"],
            [p.name for p in staged])
        add("nothing promoted without the user's yes", not promoted, [p.name for p in promoted])
        entries = staged

    # Aggregate, one check per RULE across every entry: a per-entry name would carry the
    # model's own slug, which changes run to run, so the baseline could never match it and
    # a regression in these checks would be invisible in the "regressions" column.
    if entries:
        bad_gate, bad_fm, bad_src, bad_raw = [], [], [], []
        snapshots = bool(list((ctx["notebook"] / "raw" / "sessions").glob("*.md")))
        for p in entries:
            etext = p.read_text(encoding="utf-8")
            fm, _ = gate.split_frontmatter(etext)
            errs = gate.check_entry_text(etext)["errors"]
            if errs:
                bad_gate.append(f"{p.stem}: {errs[:2]}")
            if not (str(fm.get("tier")) == "self" and str(fm.get("origin")) == "wrap-up"
                    and str(fm.get("category")) in
                    ("component", "decision", "architecture", "pattern", "troubleshooting")):
                bad_fm.append(f"{p.stem}: tier={fm.get('tier')} origin={fm.get('origin')} "
                              f"category={fm.get('category')}")
            if not str(fm.get("source_url", "")).startswith("internal://"):
                bad_src.append(f"{p.stem}: {fm.get('source_url')}")
            if "raw_path" in fm and not snapshots:
                bad_raw.append(f"{p.stem}: {fm.get('raw_path')}")
        add(f"all {len(entries)} entries pass the entry gate", not bad_gate, bad_gate)
        add("every entry: tier self, origin wrap-up, a real category", not bad_fm, bad_fm)
        add("every entry: source_url is internal://", not bad_src, bad_src)
        add("no entry claims a raw_path without a snapshot", not bad_raw, bad_raw)

    if entries and not exp.get("promoted"):
        missing, unreadable, bad_target = [], [], []
        for p in entries:
            side = p.with_name(f"{p.stem}.proposed_metadata.json")
            if not side.is_file():
                missing.append(p.stem)
                continue
            try:
                meta = json.loads(side.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                unreadable.append(f"{p.stem}: {e}")
                continue
            tf = str(meta.get("target_folder", ""))
            if not (tf.startswith("project/") and tf.split("/")[-1] in CATEGORIES):
                bad_target.append(f"{p.stem}: {tf!r}")
        add("every entry has a sidecar", not missing, missing)
        add("every sidecar is valid JSON", not unreadable, unreadable)
        add("every sidecar names project/<plural folder>", not bad_target, bad_target)
        # cwd is the sandbox project, so --topic resolves through its wiki-config's registry pointer
        proc = subprocess.run(
            [sys.executable, str(ctx["scripts"] / "wiki-promote.py"), "--topic", NOTEBOOK, "--check"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}, cwd=str(ctx["project"]))
        add("every staged entry would promote (wiki-promote --check)", proc.returncode == 0,
            (proc.stdout or "")[-260:] + (proc.stderr or "")[-120:])

    # ---- the reply, and the rules that only show there
    if exp.get("prints_table"):
        add("printed the proposal table even unattended",
            all(w in text.lower() for w in ("category", "|")) and "proposed" in text.lower())
    if exp.get("points_at"):
        add("points at wiki-update for research work", bool(POINTS_AT_UPDATE.search(text)))
    if exp.get("declines"):
        add("says nothing merits an entry", bool(DECLINES.search(text)))
    if exp.get("creates_dashboards"):
        add("first run created both dashboards", handoff.is_file() and active.is_file())

    # ---- Step 5.5: the skill-suggestion box (2026-09-26)
    sug = case.get("suggestions") or {}
    if exp.get("suggestions"):
        box = ctx["notebook"] / "_inbox" / "skill-suggestions"
        top = sorted(p.name for p in box.glob("*.md")) if box.is_dir() else []
        low = text.lower()
        old_archive = {n: (box / "archive" / n).read_text(encoding="utf-8")
                       if (box / "archive" / n).is_file() else None for n in sug.get("archive", {})}
        add("archive/ entries untouched", all(old_archive[n] == b for n, b in sug["archive"].items()),
            [n for n, b in sug["archive"].items() if old_archive[n] != b])
        add("archive/ not read into the report (its wiki-refresh suggestion not shown)", "wiki-refresh" not in low)
        # a file already marked Sent waits for its owner to collect it: never re-asked, never touched
        pre_sent = "tdd-implementation--doubt-log-order.md"
        add("the already-sent suggestion left as it was",
            (box / pre_sent).is_file() and (box / pre_sent).read_text(encoding="utf-8") == sug["box"][pre_sent])
        add("the already-sent one listed as waiting for its owner, not asked about",
            _near_or_same_line(text, "tdd-implementation", WAITING))
        if exp["suggestions"] == "ask":
            add("lists every suggestion in the box",
                all(s in low for s in ("verifying-before-done", "wiki-lint", "frontend-design")))
            # the owner comes from the skill's usage page (2026-09-29, the user's rule)
            add("proposes agent-builder for verifying-before-done (a do-code-change page)",
                "agent-builder" in _owner_after(text, "verifying-before-done"),
                _owner_after(text, "verifying-before-done"))
            add("proposes llm-wiki for wiki-lint (an llm-wiki page)",
                "llm-wiki" in _owner_after(text, "wiki-lint"), _owner_after(text, "wiki-lint"))
            add("says frontend-design's owner is unknown and asks (no usage page)",
                _near(text, "frontend-design", UNKNOWN_OWNER))
            add("offers send, keep and drop", all(w in low for w in ("send", "keep", "drop")))
            unchanged = top == sorted(sug["box"]) and all(
                (box / n).read_text(encoding="utf-8") == b for n, b in sug["box"].items())
            add("nothing moved or changed without an answer", unchanged, top)
        elif exp["suggestions"] == "own":
            # task #62 (the user, 2026-10-01): in the owning library's own notebook a note about one of its skills is
            # already home, so it is filed into received/ with no question; a note for another owner is still asked
            # about, even with confirm_before_create: false
            own_name = "wiki-lint--flags-quotes-in-code.md"
            got = box / "received" / own_name
            gt = got.read_text(encoding="utf-8") if got.is_file() else ""
            lines = gt.splitlines()
            add("the own library's note filed in received/", got.is_file(),
                sorted(p.relative_to(box).as_posix() for p in box.rglob("*.md")))
            add("filed by receive: From this notebook first, the four lines, Received from",
                lines[:1] == [f"From: {NOTEBOOK}"] and all(l in lines for l in sug["box"][own_name].splitlines())
                and any(l.startswith("Received from:") for l in lines), gt[:300])
            add("the own library's note gone from the box's top level", own_name not in top, top)
            add("the report says it was filed for the next improver pass", _near(text, "wiki-lint", FILED))
            add("not offered or sent to its own library (no send to llm-wiki, no tag of its bot)",
                not SENT_TO_SELF.search(text) and f"<@{LLM_WIKI_ID}>" not in text,
                (SENT_TO_SELF.search(text) or [""])[0])
            other = "verifying-before-done--freeze-step-takes-only-a-number.md"
            add("the agent-builder note left in the box unchanged (no send without the user's word)",
                (box / other).is_file() and (box / other).read_text(encoding="utf-8") == sug["box"][other], top)
            add("still asks about the agent-builder note in an automatic notebook",
                "agent-builder" in _owner_after(text, "verifying-before-done")
                and all(w in low for w in ("send", "keep", "drop")), _owner_after(text, "verifying-before-done"))
        else:
            name = "verifying-before-done--freeze-step-takes-only-a-number.md"
            sent = box / name
            dropped = box / "archive" / "wiki-lint--flags-quotes-in-code-2.md"
            st = sent.read_text(encoding="utf-8") if sent.is_file() else ""
            dt = dropped.read_text(encoding="utf-8") if dropped.is_file() else ""
            add("the sent one stays in the box for its owner to collect", sent.is_file() and
                not (box / "archive" / name).exists(), sorted(p.name for p in box.rglob("*.md")))
            add("the sent one: its four lines kept, a Sent line naming agent-builder, no Decision line",
                st.startswith(sug["box"][name]) and re.search(r"^Sent \(.*agent-builder", st, re.M | re.I)
                and "Decision (" not in st, st[-160:])
            add("the tagged line names the sent file's path, for agent-builder's bot",
                name in text.replace("\\", "/") and f"<@{AGENT_BUILDER_ID}>" in text)
            add("dropped one archived as -2 (the name was taken) with its decision line",
                "Decision (" in dt and "dropped" in dt.lower(), dt[-160:] or sorted(
                    p.name for p in (box / "archive").glob("*")))
            add("the dropped one gone from the box's top level", "wiki-lint--flags-quotes-in-code.md" not in top, top)

    # ---- Step 7: the closing line ends every wrap-up; the commit and push only with a flag
    final = str(run["result"].get("result") or "").strip().splitlines()
    last = final[-1].strip() if final else ""
    want = CLOSING[exp.get("commit")]
    add("ends on the closing line", last == want, f"last line: {last[:120]!r}; want {want!r}")
    if exp.get("commit"):
        project, nbrepo = ctx["project"], ctx["sandbox"] / "notebooks"
        new_commits = _git(project, "rev-list", f"{ctx['project_head']}..HEAD").split()
        add("project: the session's work committed", bool(new_commits), f"{len(new_commits)} new commits")
        changed = _git(project, "diff", "--name-only", ctx["project_head"], "HEAD").split()
        add("project: the commit holds the session's file", "beacon/retry.py" in changed, changed)
        add("project: the user's untouched file left out and uncommitted",
            "scratch-notes.txt" not in changed and "?? scratch-notes.txt" in _git(project, "status", "--porcelain"),
            _git(project, "status", "--porcelain")[:200])
        nb_commits = _git(nbrepo, "rev-list", f"{ctx['notebook_head']}..HEAD").split()
        add("notebook: the wrap-up committed", bool(nb_commits), f"{len(nb_commits)} new commits")
        dirty = _git(nbrepo, "status", "--porcelain", "--", NOTEBOOK).strip()
        add("notebook: nothing of the notebook left uncommitted", not dirty, dirty[:200])
        for label, repo_dir in (("project", project), ("notebook", nbrepo)):
            local = _git(repo_dir, "rev-parse", "HEAD").strip()
            remote = _git(repo_dir, "ls-remote", "origin", "HEAD").split()
            remote_head = remote[0] if remote else ""
            if not remote_head:
                branch = _git(repo_dir, "rev-parse", "--abbrev-ref", "HEAD").strip()
                rb = _git(repo_dir, "ls-remote", "origin", f"refs/heads/{branch}").split()
                remote_head = rb[0] if rb else ""
            if exp["commit"] == "push":
                add(f"{label}: pushed (the remote has the local HEAD)", local and remote_head == local,
                    f"local {local[:8]} remote {remote_head[:8]}")
            elif remote_head:   # commit only: a remote exists (the git fixture), and it must not have moved
                add(f"{label}: not pushed (the remote is behind the local HEAD)", local and remote_head != local,
                    f"local {local[:8]} remote {remote_head[:8]}")

    # ---- staging discipline: nothing hand-written into project/ or the wiki root
    wiki_rel = {k for k in set(before) | set(after)
                if before.get(k) != after.get(k) and k.startswith("wiki/")}
    stray = sorted(k for k in wiki_rel
                   if not k.startswith("wiki/sessions/")
                   and not (exp.get("promoted") and k.startswith("wiki/project/")))
    add("wrote nothing into wiki/ but sessions/ (and promotes)", not stray, stray)
    return res
