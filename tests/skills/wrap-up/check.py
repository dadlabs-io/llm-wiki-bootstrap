"""wrap-up test suite: fixtures, sandbox, prompts and checks for run_skill_test.py.

A headless session has no real conversation to distill, so each case's prompt carries
the session's work as narrative (cases.json `work`) over a made-up project, `beacon`,
whose files are really on disk in the sandbox. Nothing a model already knows can
answer for it.

What the cases cover, one of each input the skill handles: a first wrap-up with no
dashboards and a repo with no commits (the git-128 path), an incremental one that must
APPEND to this session's existing journal, a `none` answer at the proposal table, a
`task.md` carrying the /task-list block, `confirm_before_create: false`,
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
    "Bash(python:*)", "Bash(python3:*)", "Bash(git:*)", "Bash(date:*)", "Bash(mkdir:*)",
    "Bash(cd:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(grep:*)", "Bash(head:*)", "Bash(tail:*)",
    "Bash(wc:*)", "Bash(find:*)", "Bash(sort:*)", "Bash(echo:*)", "Bash(pwd:*)", "Bash(sed:*)",
]
POINTS_AT_UPDATE = re.compile(r"/?wiki-update|/?wiki-cycle", re.I)
DECLINES = re.compile(
    r"nothing (here )?(merits|warrants|worth|that merits)|no (durable|wiki|entry|entries)|"
    r"not worth (a|an) (wiki )?entry|too (trivial|small|thin)|doesn'?t merit|"
    r"no candidates|nothing to file|nothing durable", re.I)
ASKS_REMOVE = re.compile(r"remove", re.I)
CLOSING = {None: "✅ WRAP-UP COMPLETE: nothing committed ✅",
           "commit": "✅ WRAP-UP COMPLETE: committed, not pushed ✅",
           "push": "✅ WRAP-UP COMPLETE: committed and pushed ✅"}
SESSION_EDIT = "\n\ndef budget_left_seconds(budget):\n    return max(0.0, budget.remaining())\n"


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
    project = sandbox / "project"
    project.mkdir(parents=True)
    cfg_dir = project / ".claude"
    cfg_dir.mkdir()
    return {"sandbox": sandbox, "project": project, "notebook": nb,
            "registry": sandbox / "linked-notebooks.json",
            "wiki": nb / "wiki", "proposed": nb / "_inbox" / "proposed",
            "skill_dir": sandbox / "skill" / "wrap-up",
            "scripts": repo / "bootstrap" / "scripts",
            "env": {"PYTHONIOENCODING": "utf-8"}}


def teardown(ctx: dict) -> None:
    try:
        _rmtree(ctx["sandbox"])
    except OSError:
        pass


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
    _git(project, "init", "-q")
    _git(project, "config", "user.email", "test@example.invalid")
    _git(project, "config", "user.name", "Skill Test")
    if case.get("git") in ("commits", "session-changes"):
        _git(project, "add", "-A")
        _git(project, "commit", "-q", "-m", "beacon: retry budget draft and the network seam")
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

    flags = case.get("flags") or {}
    ctx["registry"].write_text(json.dumps(
        {"notebooks": {NOTEBOOK: {"root": f"notebooks/{NOTEBOOK}", **flags}}}, indent=2), encoding="utf-8")
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


HEADER = """You are running an automated test of the wrap-up skill. The skill under test is at {skill}/SKILL.md. Read it and follow it exactly, as if this were the end of a real session in this project. Do not use any installed copy of the skill.

You are in the `beacon` project at {project}; its notebook is `{notebook}` at {nb}, and this session's persona is `{persona}`. This session's id is `{sid}` — use it where the skill asks for a session id. Write only inside {sandbox}, and run scripts as `python <path> ...` with no environment-variable prefix.

The user cannot reply while this runs. Where the skill says to wait for the user, take the answers given below as already spoken; where it says to offer or ask something with no answer given, say in your final message what you would offer or ask, and do not act on an answer you do not have.

{work}

{answers}The user said: {say}"""


def prompt(case: dict, ctx: dict) -> str:
    _reset_project(case, ctx)
    _reset_notebook(case, ctx)
    answers = []
    if case.get("answer"):
        answers.append(f"At the proposal table (Step 2), the user answers: `{case['answer']}`.")
    if case.get("promote_answer"):
        answers.append(f"At the promotion prompt (Step 6), the user answers: `{case['promote_answer']}`.")
    if case.get("finished_task"):
        answers.append(f"For the task list: task {case['finished_task']} was finished in this session.")
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


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    gate = _load(ctx["scripts"], "_entry_checks.py", "entry_checks")
    cfgmod = _load(ctx["scripts"], "_wiki_config.py", "wiki_config")
    today = cfgmod.today_label()
    res: list[dict] = []
    exp = case.get("expect") or {}
    text = run["text"]

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

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

    # ---- Step 0.5: the three dashboards
    persona_dir = ctx["wiki"] / "sessions" / PERSONA
    handoff, task_md = persona_dir / "handoff.md", persona_dir / "task.md"
    active = ctx["wiki"] / "sessions" / "active-context.md"
    add("handoff.md written", handoff.is_file())
    if handoff.is_file():
        htext = handoff.read_text(encoding="utf-8")
        missing = [s for s in HANDOFF_SECTIONS if s not in htext]
        add("handoff.md has every section", not missing, missing)
        add("handoff.md reflects this session, not the seed",
            "RetryBudget" in htext or "retry" in htext.lower())
    add("task.md written", task_md.is_file())
    if task_md.is_file():
        ttext = task_md.read_text(encoding="utf-8")
        if exp.get("task_block"):
            add("At a glance block kept", ttext.lstrip().startswith("## At a glance"), ttext[:60])
            board = _load(ctx["scripts"], "wiki-tasks.py", "wiki_tasks").Board(ttext)
            rows = {r["id"]: r for s in board.sections for r in s["rows"]}
            # nothing REMOVED; adding a task is required of a wrap-up, so the set may grow
            add("no task removed", {1, 2, 3, 4} <= set(rows), sorted(rows))
            fin = case.get("finished_task")
            add(f"task {fin} marked done", rows.get(fin, {}).get("status") == "done", rows.get(fin))
            add("asks before removing a done task", bool(ASKS_REMOVE.search(text)))
            add("other owner's task untouched", rows.get(3, {}).get("status") == "waiting", rows.get(3))
            add("NOW and QUEUE kept below the block", "## NOW" in ttext and "## QUEUE" in ttext)
        else:
            add("task.md has NOW and QUEUE", "## NOW" in ttext and "## QUEUE" in ttext, ttext[:80])
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
        add("first run created all three dashboards",
            handoff.is_file() and task_md.is_file() and active.is_file())

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
        if exp["commit"] == "push":
            for label, repo_dir in (("project", project), ("notebook", nbrepo)):
                local = _git(repo_dir, "rev-parse", "HEAD").strip()
                remote = _git(repo_dir, "ls-remote", "origin", "HEAD").split()
                remote_head = remote[0] if remote else ""
                if not remote_head:
                    branch = _git(repo_dir, "rev-parse", "--abbrev-ref", "HEAD").strip()
                    rb = _git(repo_dir, "ls-remote", "origin", f"refs/heads/{branch}").split()
                    remote_head = rb[0] if rb else ""
                add(f"{label}: pushed (the remote has the local HEAD)", local and remote_head == local,
                    f"local {local[:8]} remote {remote_head[:8]}")

    # ---- staging discipline: nothing hand-written into project/ or the wiki root
    wiki_rel = {k for k in set(before) | set(after)
                if before.get(k) != after.get(k) and k.startswith("wiki/")}
    stray = sorted(k for k in wiki_rel
                   if not k.startswith("wiki/sessions/")
                   and not (exp.get("promoted") and k.startswith("wiki/project/")))
    add("wrote nothing into wiki/ but sessions/ (and promotes)", not stray, stray)
    return res
