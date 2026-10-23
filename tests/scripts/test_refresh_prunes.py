#!/usr/bin/env python3
"""Checks for task #180: a refresh removes what a retired skill, script or agent left installed. Never shipped.

    uv run python tests/scripts/test_refresh_prunes.py    # exit 0 = every check passed

The "no dead skills" rule (Mark, 2026-09-15) and the prune decision ("the prune has to live in the refresh") were
met only by `--mode uninstall`: the install manifest kept a retired skill's files listed, but a refresh left them
in ~/.claude, so every retirement was a hand delete. Now a refresh removes each file the previous manifest lists
for an artifact that no longer ships, when it is unchanged since install; an edited one is left and named. A
skill that failed this install's frontmatter gate still ships, so its earlier copy stays. The toolset drops
retired top-level pack pages as it already drops retired skill pages. Temporary folders, stand-ins for the slow
parts, as in test_install_manifest.py.
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


def fake_env(pkg, dest, dry_run=False, extras=None):
    for n in it.ENV_FILES:
        (Path(dest) / n).write_bytes((Path(pkg) / n).read_bytes())
    (Path(dest) / ".venv").mkdir(parents=True, exist_ok=True)
    return "stand-in environment"


with tempfile.TemporaryDirectory() as tmp:
    td = Path(tmp)
    skills, scripts, agents = td / "skills", td / "wiki-scripts", td / "agents"
    real = (it.build_tooling_env, it.install_page_browser, it.CC_GLOBAL_AGENTS_DIR, it._load_frontmatter_checker)
    it.build_tooling_env, it.install_page_browser, it.CC_GLOBAL_AGENTS_DIR = fake_env, lambda *a, **k: "skipped", agents

    def install(**kw):
        with redirect_stdout(io.StringIO()):
            return it.install_tooling(ROOT, skills_dest=skills, scripts_dest=scripts, **kw)

    try:
        install()
        mpath = scripts / it.MANIFEST_NAME

        # what earlier installs left: a retired skill (two files, one in a subfolder), a retired script, a retired
        # agent with its sidecar, and a retired skill file someone edited since
        def plant(path: Path, text: str, edit_after: str = "") -> Path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            data = json.loads(mpath.read_text(encoding="utf-8"))
            data["files"].append({"path": path.resolve().as_posix(), "sha256": it._sha256(path)})
            mpath.write_text(json.dumps(data), encoding="utf-8")
            if edit_after:
                path.write_text(text + edit_after, encoding="utf-8")
            return path

        r_skill = plant(skills / "old-retired" / "SKILL.md", "# retired\n")
        r_ref = plant(skills / "old-retired" / "scripts" / "helper.py", "x = 1\n")
        r_script = plant(scripts / "wiki-old-thing.py", "print('old')\n")
        r_agent = plant(agents / "old-agent.md", "# old agent\n")
        r_side = plant(agents / "old-agent-config.json", "{}\n")
        r_edited = plant(skills / "old-edited" / "SKILL.md", "# retired\n", edit_after="my own note\n")
        mine = skills / "my-own-skill" / "SKILL.md"
        mine.parent.mkdir(parents=True)
        mine.write_text("# mine\n", encoding="utf-8")

        dry = install(dry_run=True)
        check("a dry run lists what it would remove and removes nothing",
              r_skill.is_file() and r_script.is_file() and len((dry.get("pruned") or {}).get("removed", [])) == 5,
              dry.get("pruned"))

        # this install's frontmatter gate fails one shipped skill: its earlier copy must stay
        failing = "wiki-lint"
        kept_file = skills / failing / "SKILL.md"
        check_real = real[3]

        def gate(scripts_src):
            fn = check_real(scripts_src)
            return lambda text: (fn(text) + [("ERROR", "test", "forced")]) if "name: wiki-lint" in text else fn(text)

        it._load_frontmatter_checker = gate
        out = install()
        pr = out.get("pruned") or {}
        check("the refresh removes the retired skill's files, script and agent",
              not any(p.exists() for p in (r_skill, r_ref, r_script, r_agent, r_side)), pr)
        check("... and says so", len(pr.get("removed", [])) == 5, pr.get("removed"))
        check("... and the retired skill's folders, once empty", not (skills / "old-retired").exists())
        check("an edited retired file is left and named", r_edited.is_file()
              and r_edited.resolve().as_posix() in pr.get("edited_left", []), pr.get("edited_left"))
        check("a file no install wrote is untouched", mine.is_file())
        check("a shipped skill that failed this install's gate keeps its earlier copy", kept_file.is_file()
              and "wiki-lint" in out.get("skills_failed", []), out.get("skills_failed"))
        listed = {e["path"] for e in json.loads(mpath.read_text(encoding="utf-8"))["files"]}
        check("the removed files leave the manifest; the failed skill's earlier files stay in it",
              r_skill.resolve().as_posix() not in listed and kept_file.resolve().as_posix() in listed)
        check("every shipped skill is still installed", all((skills / s / "SKILL.md").is_file() for s in it.TRAVEL_SKILLS))
    finally:
        it.build_tooling_env, it.install_page_browser, it.CC_GLOBAL_AGENTS_DIR, it._load_frontmatter_checker = real

    # the toolset: a retired top-level pack page goes, like a retired skill page; another pack's page stays
    root = td / "toolset"
    for rel in it.toolset_files(ROOT):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(it.toolset_files(ROOT)[rel].read_bytes())
    old_page = root / it.TOOLSET_PACK / "old-retired-page.md"
    old_page.write_text("# gone\n", encoding="utf-8")
    other = root / "how-to" / "agent-builder" / "something.md"
    other.parent.mkdir(parents=True)
    other.write_text("# theirs\n", encoding="utf-8")
    st = it.toolset_status(ROOT, root)
    check("toolset: a top-level pack page that no longer ships is listed to remove",
          (it.TOOLSET_PACK / "old-retired-page.md").as_posix() in st["remove"], st["remove"])
    check("toolset: another pack's page is never listed", not any("agent-builder" in r for r in st["remove"]), st["remove"])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
raise SystemExit(1 if failed else 0)
