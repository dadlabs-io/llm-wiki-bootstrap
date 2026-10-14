#!/usr/bin/env python3
"""Checks for task #123: an install records what it wrote; an uninstall removes exactly that. Never shipped.

    python tests/scripts/test_install_manifest.py    # exit 0 = every check passed

From the Ruflo deep dive (2026-10-13): claude-flow's leftovers sat in ~/.claude for five months because nothing
knew what it installed. The install writes install-manifest.json beside the scripts (every file with a hash of
what it wrote, the .venv, the hook entries); `new-wiki.py --mode uninstall` removes those, leaves a file someone
edited since, and never touches anything else. The install runs into temporary folders, with the slow parts
(the uv environment, Chromium) replaced by stand-ins and the agents folder pointed at a temporary one.
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import _install_tooling as it  # noqa: E402

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


with tempfile.TemporaryDirectory() as tmp:
    td = Path(tmp)
    skills, scripts, agents = td / "skills", td / "wiki-scripts", td / "agents"
    real = (it.build_tooling_env, it.install_page_browser, it.CC_GLOBAL_AGENTS_DIR)

    def fake_env(pkg, dest, dry_run=False, extras=None):
        for n in it.ENV_FILES:
            (Path(dest) / n).write_bytes((Path(pkg) / n).read_bytes())
        (Path(dest) / ".venv" / "lib").mkdir(parents=True, exist_ok=True)
        (Path(dest) / ".venv" / "lib" / "site.py").write_text("x", encoding="utf-8")
        return "stand-in environment"

    it.build_tooling_env, it.install_page_browser, it.CC_GLOBAL_AGENTS_DIR = fake_env, lambda *a, **k: "skipped", agents
    try:
        with redirect_stdout(io.StringIO()):
            summary = it.install_tooling(ROOT, skills_dest=skills, scripts_dest=scripts)
    finally:
        it.build_tooling_env, it.install_page_browser, it.CC_GLOBAL_AGENTS_DIR = real

    mpath = scripts / it.MANIFEST_NAME
    check("the install writes install-manifest.json beside the scripts", mpath.is_file() and summary.get("manifest") == mpath)
    data = json.loads(mpath.read_text(encoding="utf-8")) if mpath.is_file() else {}
    listed = {e["path"] for e in data.get("files", [])}
    on_disk = {p.resolve().as_posix() for root in (skills, agents) for p in root.rglob("*") if p.is_file()}
    on_disk |= {p.resolve().as_posix() for p in scripts.iterdir() if p.is_file() and p.name != it.MANIFEST_NAME}
    check("it lists every file the install wrote: scripts, env files, skills, agents", on_disk == listed,
          (len(on_disk), len(listed), sorted(on_disk ^ listed)[:5]))
    check("each file carries a sha256", all(len(e.get("sha256", "")) == 64 for e in data.get("files", [])))
    check("it lists the .venv folder", (scripts / ".venv").resolve().as_posix() in data.get("dirs", []))
    check("no hook entries for a non-global install", data.get("hooks") == [], data.get("hooks"))
    check("it names what an uninstall never touches", any("toolset" in x for x in data.get("left_on_uninstall", [])))

    # a skill retired since: listed by the old manifest and still unchanged, so still removed later
    retired = skills / "old-retired-skill" / "SKILL.md"
    retired.parent.mkdir(parents=True)
    retired.write_text("# retired\n", encoding="utf-8")
    data["files"].append({"path": retired.resolve().as_posix(), "sha256": it._sha256(retired)})
    mpath.write_text(json.dumps(data), encoding="utf-8")
    it.write_manifest(scripts, [scripts / "wiki-tasks.py"], [scripts / ".venv"], [], ROOT)
    kept = {e["path"] for e in json.loads(mpath.read_text(encoding="utf-8"))["files"]}
    check("a reinstall keeps an earlier, unchanged file it did not write again (a retired skill)",
          retired.resolve().as_posix() in kept and len(kept) == len(listed) + 1, len(kept))
    it.write_manifest(scripts, [p for p in map(Path, listed)] + [retired], [scripts / ".venv"], [], ROOT)

    # someone edits one installed file, and keeps a file of their own beside the skills
    edited = skills / "wiki-lint" / "SKILL.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nmy own note\n", encoding="utf-8")
    mine = skills / "my-own-skill" / "SKILL.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("# mine\n", encoding="utf-8")

    dry = it.uninstall_tooling(scripts, dry_run=True)
    check("a dry run removes nothing", mpath.is_file() and (scripts / "wiki-tasks.py").is_file() and dry["dry_run"])
    out = it.uninstall_tooling(scripts)
    check("uninstall removes every listed, unchanged file", len(out["removed"]) == len(listed), (len(out["removed"]), len(listed)))
    check("... including the retired skill", not retired.exists())
    check("an edited file is left and named", edited.is_file() and edited.resolve().as_posix() in out["edited_left"],
          out["edited_left"])
    check("a file the install never wrote is untouched", mine.is_file())
    check("the .venv is removed", not (scripts / ".venv").exists() and out["dirs_removed"])
    check("the manifest goes last", not mpath.exists())
    check("empty skill folders go; one holding a kept file stays",
          not (skills / "wiki-cycle").exists() and (skills / "wiki-lint").is_dir() and (skills / "my-own-skill").is_dir())
    check("agents are removed", not any(agents.glob("*.md")) if agents.exists() else True)
    try:
        it.uninstall_tooling(scripts)
        check("a second uninstall with no manifest refuses", False)
    except FileNotFoundError:
        check("a second uninstall with no manifest refuses", True)

    # hook entries: only ours come out of settings.json
    settings = td / "settings.json"
    settings.write_text(json.dumps({"model": "x", "hooks": {
        "SessionStart": [{"matcher": "startup|clear", "hooks": [{"type": "command", "command": "py",
                                                                  "args": ["-c", "g", "/s/wiki-session-start.py"]}]}],
        "PreToolUse": [{"matcher": "Read|Bash|PowerShell", "hooks": [
            {"type": "command", "command": "py", "args": ["-c", "g", "/s/read-guard.py"]},
            {"type": "command", "command": "node other-tool.js"}]}],
        "Stop": [{"hooks": [{"type": "command", "command": "py", "args": ["/s/read-guard.py"]}]}]}}), encoding="utf-8")
    n = it.remove_hooks(settings, [it.SESSION_HOOK_SCRIPT, it.READ_GUARD_SCRIPT])
    s = json.loads(settings.read_text(encoding="utf-8"))
    check("remove_hooks takes out our three entries", n == 3, n)
    check("... keeps another tool's hook and every other setting",
          s.get("model") == "x" and s["hooks"].get("PreToolUse", [{}])[0].get("hooks") == [{"type": "command", "command": "node other-tool.js"}],
          s)
    check("... drops an event left empty", "SessionStart" not in s["hooks"] and "Stop" not in s["hooks"], list(s["hooks"]))
    check("... and backs the file up first", (td / "settings.json.bak-wiki").is_file())

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
raise SystemExit(1 if failed else 0)
