"""new-wiki test suite: sandbox, prompts and checks for run_skill_test.py.

/new-wiki is an interview, and a headless session has no AskUserQuestion tool (probed
2026-09-18: the tool is not offered at all under `claude -p`). So the prompt tells the
session to write the skill's questions in its final reply, and each case supplies the
answers the user "gave" up to the point the case stops: before round 1 (ask-first),
at the plan summary (plan-only), or through "go" (the scaffold cases).

The machine's global tooling is the real one. A fake home folder cannot be used:
Claude Code then needs CLAUDE_CONFIG_DIR for its login, and with it set it writes a
fresh `.claude.json` into the real ~/.claude (found by the 2026-09-18 probe). So the
suite tests the branches this machine is in (tooling installed, Drive off) and leaves
the partial / missing / Drive-on branches untested; see PENDING.md.

Everything a session writes lands in a sandbox under the system temp folder, outside
any git repo (inside one, Phase B skips `git init` by design). The vault and registry
are the sandbox's; the prompt says so. Safety checks on every case compare the real
registry, the real ~/.claude/wiki-config.json and the real default paths for the test
slug before and after, so a session that writes outside the sandbox fails loudly.

Every case is reset by prompt(): the working folder is emptied (or seeded with a
CLAUDE.md), the sandbox vault emptied and its registry rewritten, so no case depends on
another's leftovers or order. The checks read what the session left on disk and what
it wrote in its reply, never the commands it chose — with one exception, the state
check (`--mode status` writes nothing, so its call is the only evidence it ran).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLUG = "harbor-log"
OTHER = "other-notes"
PROJECT_STUBS = ("components", "decisions", "architecture", "patterns", "troubleshooting")
RESEARCH_STUBS = ("active", "long-term", "tooling", "best-practices", "interesting-docs")
FRAMEWORK_DOCS = 6
CLAUDE_MD_SEED = "# harbor-log\n\nHand-written project notes. Keep this file exactly as it is.\n"
REAL_GLOBAL = Path.home() / ".claude" / "wiki-config.json"

SKILLS_QUESTION = re.compile(r"bundle (the )?skills|install the global tooling|bundled? into (this|the) project", re.I)
DRIVE_QUESTION = re.compile(r"drive[^\n]*\?", re.I)
PLAN_LABELS = ("tool:", "target folder:", "wiki content:", "folders:", "skills:", "drive:", "review gate:")
POINTS_AT_DOCS = re.compile(r"commands\.md|getting-started", re.I)
ROUND2_OPTIONS = re.compile(r"with the default stubs|yes, empty|notebook in the vault|inside the project", re.I)
ROUND2_TOPICS = re.compile(r"research folder|project folder|where (does |should )?the wiki live|description", re.I)


def _rmtree(path) -> None:
    """Delete a tree that may hold a git repo (Windows marks git objects read-only)."""
    def onexc(func, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass

    if Path(path).exists():
        shutil.rmtree(path, onexc=onexc)


def _real_paths() -> dict:
    """The machine's real registry and the real places a stray scaffold would land."""
    reg = None
    try:
        reg = json.loads(REAL_GLOBAL.read_text(encoding="utf-8")).get("registry")
    except (OSError, json.JSONDecodeError):
        pass
    reg = Path(reg) if reg else Path("C:/github.com/project-notebooks/linked-notebooks.json")
    return {"global": REAL_GLOBAL, "registry": reg,
            "vault_notebook": reg.parent / "notebooks" / SLUG,
            "default_target": Path("C:/github.com") / SLUG}


def _digest(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def prepare_fixtures(repo: Path, refresh: bool = False) -> list[dict]:
    return []  # nothing third-party: the sandbox is generated


def setup(model: str, sandbox: Path, repo: Path) -> dict:
    # The runner's sandbox sits inside this repo; Phase B would skip `git init` there.
    # Use a folder under the system temp instead (the runner's path is left unused).
    box = Path(tempfile.gettempdir()) / "llm-wiki-skilltest" / f"new-wiki-{model}"
    _rmtree(box)
    vault = box / "vault"
    (vault / "notebooks").mkdir(parents=True)
    project = box / "work" / SLUG
    project.mkdir(parents=True)
    return {"sandbox": box, "project": project, "vault": vault,
            "registry": vault / "linked-notebooks.json",
            "skill_dir": box / "skill" / "new-wiki", "repo": repo,
            "scripts": repo / "bootstrap" / "scripts", "real": _real_paths(),
            "env": {"PYTHONIOENCODING": "utf-8"}}


def teardown(ctx: dict) -> None:
    try:
        _rmtree(ctx["sandbox"])
    except OSError:
        pass


def snapshot(ctx: dict) -> dict:
    real = ctx["real"]
    files = {}
    for root in (ctx["sandbox"] / "work", ctx["vault"]):
        if root.exists():
            for p in root.rglob("*"):
                if ".git" in p.relative_to(ctx["sandbox"]).parts:
                    continue
                files[p.relative_to(ctx["sandbox"]).as_posix()] = p.is_dir()
    return {"files": files,
            "real_global": _digest(real["global"]), "real_registry": _digest(real["registry"]),
            "real_vault_notebook": real["vault_notebook"].exists(),
            "real_default_target": real["default_target"].exists()}


def _reset(case: dict, ctx: dict) -> None:
    _rmtree(ctx["sandbox"] / "work")
    _rmtree(ctx["vault"] / "notebooks")
    (ctx["vault"] / "notebooks").mkdir(parents=True)
    ctx["registry"].write_text(json.dumps(
        {"notebooks": {OTHER: {"root": f"notebooks/{OTHER}"}}}, indent=2), encoding="utf-8")
    ctx["project"].mkdir(parents=True)
    if case.get("seed_claude_md"):
        (ctx["project"] / "CLAUDE.md").write_text(CLAUDE_MD_SEED, encoding="utf-8")
    # The runner snapshots BEFORE it builds the prompt, and building the prompt is what
    # resets the sandbox; "what the session created" is measured from here instead.
    ctx["reset_files"] = snapshot(ctx)["files"]


HEADER = """You are running an automated test of the new-wiki skill. The skill under test is at {skill}/SKILL.md. Read it and follow it exactly, as if the user had said the message below in this folder ({project}). Do not use any installed copy of the skill.

This is a test machine. Its notebook vault is {vault}/notebooks and its registry is {vault}/linked-notebooks.json: wherever the skill names C:\\github.com\\project-notebooks (its notebooks folder or its linked-notebooks.json), use these instead. Write only inside {sandbox}.

AskUserQuestion is not available in this session, and the user cannot reply while it runs. Where the skill says to ask with AskUserQuestion, write the same questions, each with its options, in your final reply. Where the skill says to wait for an answer, take the answers given below as already given; where no answer is given, stop there and do not act on an answer you do not have.

{answers}The user said: {say}"""


def prompt(case: dict, ctx: dict) -> str:
    _reset(case, ctx)
    a = case.get("answers") or {}
    lines = []
    if a.get("round1"):
        lines.append(f"Round 1 answers: {a['round1']}.")
    if a.get("round2"):
        lines.append(f"Round 2 answers: {a['round2']}.")
    if a.get("plan"):
        lines.append(f"At the plan summary the user says: `{a['plan']}`.")
    block = ("\n".join(lines) + "\n\n") if lines else ""
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), project=ctx["project"].as_posix(),
                         vault=ctx["vault"].as_posix(), sandbox=ctx["sandbox"].as_posix(),
                         answers=block, say=case["say"])


def _tooling_state(ctx: dict) -> str:
    proc = subprocess.run([sys.executable, str(ctx["scripts"] / "new-wiki.py"), "--mode", "status"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    try:
        return json.loads(proc.stdout).get("state", "unknown")
    except json.JSONDecodeError:
        return "unknown"


def _ran_status(run: dict) -> bool:
    return any(re.search(r"--mode['\",\s]+status", json.dumps(c.get("input") or {}))
               for c in run["tool_calls"])


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    res: list[dict] = []
    text = run["text"]
    norm = text.replace("\\\\", "/").replace("\\", "/").lower()

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    denials = r.get("permission_denials") or []
    add("no permission denials", not denials,
        [d.get("tool_name") if isinstance(d, dict) else d for d in denials])

    # ---- safety: nothing outside the sandbox, on every case
    add("real registry untouched", before["real_registry"] == after["real_registry"])
    add("real ~/.claude/wiki-config.json untouched", before["real_global"] == after["real_global"])
    add("nothing created at the real default paths",
        not after["real_vault_notebook"] and not after["real_default_target"],
        {k: after[k] for k in ("real_vault_notebook", "real_default_target")})

    # ---- Step 0.0: the state check before anything else, and the questions it rules out
    add("ran the state check (--mode status)", _ran_status(run))
    state = _tooling_state(ctx)
    if state in ("installed", "stale"):
        add(f"no skills question (tooling is {state})", not SKILLS_QUESTION.search(text),
            (SKILLS_QUESTION.search(text) or [""])[0])
    add("no project-type question", "project type" not in norm)

    kind = case["kind"]
    base = ctx.get("reset_files", before["files"])
    created = sorted(k for k in after["files"] if k not in base)

    if kind == "ask":
        add("offers the slug harbor-log", SLUG in norm)
        add("asks the review-gate question", "review" in norm)
        # round 2's options offered, not its topics named: saying "round 2 covers the
        # research folder" while waiting is right (sonnet, 2026-09-18)
        early = ROUND2_OPTIONS.search(text) or next(
            (m for ln in text.splitlines() if "?" in ln for m in [ROUND2_TOPICS.search(ln)] if m), None)
        add("round 1 only: no round-2 question or option yet", not early, early[0] if early else "")
        # saying "Drive is off, so no Drive question" is right; only a question fails (both models, 2026-09-18)
        add("no Drive question (Drive is off)", not DRIVE_QUESTION.search(text),
            (DRIVE_QUESTION.search(text) or [""])[0])
        add("nothing scaffolded before the answers", not created, created[:8])
        return res

    if kind == "plan":
        found = [lbl for lbl in PLAN_LABELS if lbl in norm]
        add("shows the plan summary (at least 5 of its 7 lines)", len(found) >= 5, found)
        add("wiki content is the sandbox vault notebook", f"vault/notebooks/{SLUG}" in norm)
        add("target folder is the current folder", f"work/{SLUG}" in norm)
        add("skills line: installed, nothing to install", "installed" in norm and "will be installed" not in norm)
        add("no Drive question (Drive is off)", not DRIVE_QUESTION.search(text))
        add("waits for the go: nothing scaffolded", not created, created[:8])
        return res

    if kind == "force":
        # Phase B refuses a folder with files in it; --force needs the user's explicit OK,
        # and "go" on a plan that never mentioned the existing folder is not that OK.
        now = (ctx["project"] / "CLAUDE.md").read_text(encoding="utf-8") \
            if (ctx["project"] / "CLAUDE.md").is_file() else ""
        add("existing CLAUDE.md kept word for word", now == CLAUDE_MD_SEED, now[:120])
        wiki = ctx["vault"] / "notebooks" / SLUG / "wiki"
        add("no wiki created without the user's OK for --force", not wiki.exists())
        add("asks about --force", "force" in norm and "?" in text)
        return res

    # ---- scaffold cases
    exp = case["expect"]
    project = ctx["project"]
    wiki_root = (ctx["vault"] / "notebooks" / SLUG) if exp["where"] == "vault" else (project / "llm-wiki")
    wiki = wiki_root / "wiki"
    add(f"wiki created {'in the vault' if exp['where'] == 'vault' else 'inside the project'}", wiki.is_dir(),
        wiki)
    other_root = (project / "llm-wiki") if exp["where"] == "vault" else (ctx["vault"] / "notebooks" / SLUG)
    add("no wiki at the other location", not other_root.exists(), other_root)
    add("sessions/ created", (wiki / "sessions").is_dir())

    pdir, fw = wiki / "project", wiki / "project" / "best-practices" / "framework"
    stubs_present = [s for s in PROJECT_STUBS if (pdir / s).is_dir()]
    fw_docs = len(list(fw.glob("*.md"))) if fw.is_dir() else 0
    if exp["project"] == "none":
        add("no project/ folder", not pdir.exists())
    else:
        add(f"the {FRAMEWORK_DOCS} framework-contract docs", fw_docs == FRAMEWORK_DOCS, fw_docs)
        if exp["project"] == "stubs":
            add("project/ stub folders", len(stubs_present) == len(PROJECT_STUBS), stubs_present)
        else:
            add("project/ empty: no stub folders", not stubs_present, stubs_present)

    rdir = wiki / "research"
    r_present = [s for s in RESEARCH_STUBS if (rdir / s).is_dir()]
    if exp["research"] == "none":
        add("no research/ folder", not rdir.exists())
    elif exp["research"] == "stubs":
        add("research/ stub folders", len(r_present) == len(RESEARCH_STUBS), r_present)
    else:
        add("research/ empty: no stub folders", rdir.is_dir() and not r_present, r_present)

    cfg_path = project / ".claude" / "wiki-config.json"
    cfg = {}
    if cfg_path.is_file():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    add("project config written", bool(cfg), cfg_path)
    add("description passed through", cfg.get("project_description") == exp["description"],
        cfg.get("project_description"))
    add("global mode: no per-project skills copy", not (project / ".claude" / "skills").exists())
    for name in ("CLAUDE.md", "README.md", ".gitignore"):
        add(f"{name} in the project", (project / name).is_file())
    add("git repo initialised", (project / ".git").exists())

    reg = json.loads(ctx["registry"].read_text(encoding="utf-8")).get("notebooks", {})
    add("registry keeps the other notebook", OTHER in reg, sorted(reg))
    if exp["where"] == "vault":
        entry = reg.get(SLUG)
        entry = entry if isinstance(entry, dict) else {}
        add("registered in the sandbox registry", bool(entry), sorted(reg))
        add(f"review gate {'on' if exp['gate'] else 'off'} in the registry",
            entry.get("confirm_before_create") is exp["gate"] and entry.get("confirm_before_promote") is exp["gate"],
            {k: entry.get(k) for k in ("confirm_before_create", "confirm_before_promote")})
        add("project_root recorded", bool(entry.get("project_root")), entry.get("project_root"))
        add("config points at the notebook and the sandbox registry",
            cfg.get("notebook") == SLUG
            and Path(str(cfg.get("registry", ""))).resolve() == ctx["registry"].resolve(),
            {k: cfg.get(k) for k in ("notebook", "registry")})
    else:
        add("not registered (in-project wiki)", SLUG not in reg, sorted(reg))
        add(f"review gate {'on' if exp['gate'] else 'off'} in the project config",
            cfg.get("confirm_before_create") is exp["gate"] and cfg.get("confirm_before_promote") is exp["gate"],
            {k: cfg.get(k) for k in ("confirm_before_create", "confirm_before_promote")})

    add("points at the command reference or getting-started", bool(POINTS_AT_DOCS.search(text)))
    return res
