#!/usr/bin/env python3
"""Checks for the global toolset (task #25, 2026-10-04). Never shipped.

    uv run python tests/scripts/test_global_toolset.py    # exit 0 = every check passed

The usage docs and the six framework-contract docs live once, in the `global-toolset` notebook, not in
every project wiki. These checks hold the pieces a mistake would break quietly: where the toolset is found
(registry entry, the vault beside the registry, the home folder), what a refresh writes, replaces and removes
(and that it never touches another pack's folder), the registration, `{{TOOLSET_DIR}}` filled in an installed
skill and agent, and `--phase docs --check`'s exit codes. Everything runs in a temp folder, through
$WIKI_GLOBAL_CONFIG; the machine's own config, registry and toolset are never read or written.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # the install prints arrows, as new-wiki.py does
sys.path.insert(0, str(ROOT / "scripts"))

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    cfg = tmp / "wiki-config.json"
    os.environ["WIKI_GLOBAL_CONFIG"] = str(cfg)  # read by _wiki_config.global_config_path()
    import _install_tooling as it
    import _wiki_config as wc

    # --- where the toolset is
    cfg.write_text(json.dumps({}), encoding="utf-8")
    root, reg, registered = wc.toolset_location()
    check("no registry: ~/.claude/global-toolset, unregistered",
          root == (Path.home() / ".claude" / "global-toolset").resolve() and reg is None and not registered, root)

    vault = tmp / "vault"
    (vault / "notebooks").mkdir(parents=True)
    registry = vault / "linked-notebooks.json"
    registry.write_text(json.dumps({"_comment": "x", "notebooks": {"other": {"root": "notebooks/other"}}}),
                        encoding="utf-8")
    cfg.write_text(json.dumps({"registry": registry.as_posix()}), encoding="utf-8")
    root, reg, registered = wc.toolset_location()
    check("a registry without the entry: <registry folder>/notebooks/global-toolset",
          root == (vault / "notebooks" / "global-toolset").resolve() and not registered, root)

    # --- a dry run writes nothing
    status = it.seed_toolset(ROOT, dry_run=True)
    check("dry run: nothing written", not root.exists(), root)
    check("dry run: the registry untouched", "global-toolset" not in registry.read_text(encoding="utf-8"))
    check("dry run: would register", status["registered"].startswith("would add"), status["registered"])

    # --- the first real run creates, registers and fills it
    files = it.toolset_files(ROOT)
    status = it.seed_toolset(ROOT)
    data = json.loads(registry.read_text(encoding="utf-8"))
    check("registered, root relative to the registry",
          data["notebooks"].get("global-toolset") == {"root": "notebooks/global-toolset"}, data["notebooks"])
    check("the other entries and keys kept", "other" in data["notebooks"] and data.get("_comment") == "x", data)
    check("every file written", all((root / rel).is_file() for rel in files) and len(status["add"]) == len(files),
          len(status["add"]))
    check("the pack page, a skill page, an agent page, a framework doc, the marker, the README",
          all((root / p).is_file() for p in ["how-to/llm-wiki/llm-wiki.md", "how-to/llm-wiki/skills/wrap-up.md",
                                             "how-to/llm-wiki/agents/wiki-ingester.md",
                                             "wiki/project/best-practices/framework/wiki-frontmatter-best-practices.md",
                                             "how-to/_FRAMEWORK_MANAGED.md", "README.md"]))
    root2, _reg, registered2 = wc.toolset_location()
    check("found through its entry afterwards", registered2 and root2 == root, root2)
    check("status: current", it.toolset_status(ROOT, root)["state"] == "current")

    # --- a refresh: replace a changed page, remove a page whose skill no longer ships, keep other packs
    (root / "how-to/llm-wiki/commands.md").write_text("edited by hand\n", encoding="utf-8")
    (root / "how-to/llm-wiki/skills/retired-skill.md").write_text("gone\n", encoding="utf-8")
    other = root / "how-to" / "do-code-change" / "do-code-change.md"
    other.parent.mkdir(parents=True)
    other.write_text("another pack's page\n", encoding="utf-8")
    st = it.toolset_status(ROOT, root)
    check("status: stale, one to replace, one to remove",
          st["state"] == "stale" and st["replace"] == ["how-to/llm-wiki/commands.md"]
          and st["remove"] == ["how-to/llm-wiki/skills/retired-skill.md"] and not st["add"], st)
    it.seed_toolset(ROOT)
    check("the hand edit replaced",
          (root / "how-to/llm-wiki/commands.md").read_bytes() == (ROOT / "wiki-seed" / "commands.md").read_bytes())
    check("the retired page removed", not (root / "how-to/llm-wiki/skills/retired-skill.md").exists())
    check("another pack's folder untouched", other.read_text(encoding="utf-8") == "another pack's page\n")
    check("current again", it.toolset_status(ROOT, root)["state"] == "current")
    crlf = root / "how-to/llm-wiki/getting-started.md"
    crlf.write_bytes(crlf.read_bytes().replace(b"
", b"
").replace(b"
", b"
"))
    check("a copy differing only in line endings (git checkout) is current",
          it.toolset_status(ROOT, root)["state"] == "current", it.toolset_status(ROOT, root)["replace"])

    # --- {{TOOLSET_DIR}} in an installed skill and agent
    text = wc.fill_placeholders("a {{WIKI_SCRIPTS_DIR}} b {{TOOLSET_DIR}} c", "/s", "/t")
    check("fill_placeholders fills both", text == "a /s b /t c", text)
    install = it.load_install_skill_fn(ROOT / "scripts")
    dest = tmp / "skills"
    rc = install(skill="wrap-up", tool="claude-code", skills_src=ROOT / "skills", skills_dest=dest,
                 scripts_dir=tmp / "scripts", dry_run=False)
    installed = (dest / "wrap-up" / "SKILL.md").read_text(encoding="utf-8")
    check("install-skill fills {{TOOLSET_DIR}} from the registry",
          rc == 0 and "{{" not in installed and f"{root.as_posix()}/how-to/<pack>/" in installed,
          installed[installed.find("usage page"):][:200])
    agent = wc.fill_placeholders((ROOT / "agents/wiki-ingester/wiki-ingester-reading-list.json").read_text(encoding="utf-8"),
                                 "/s", root.as_posix())
    check("the ingester's reading list names the toolset's spec",
          f"{root.as_posix()}/wiki/project/best-practices/framework/wiki-frontmatter-best-practices.md" in agent)

    # --- new-wiki.py --phase docs --check: exit 0 when current, 1 when not, writes nothing
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    cmd = [sys.executable, str(ROOT / "scripts" / "new-wiki.py"), "--phase", "docs", "--check",
           "--bootstrap-source", str(ROOT)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)
    check("--phase docs --check: current -> exit 0", p.returncode == 0, p.stderr[-300:])
    (root / "how-to/llm-wiki/install.md").unlink()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)
    check("--phase docs --check: a missing page -> exit 1, named, not written",
          p.returncode == 1 and "how-to/llm-wiki/install.md" in p.stdout
          and not (root / "how-to/llm-wiki/install.md").exists(), (p.returncode, p.stdout[-300:]))
    p = subprocess.run([c for c in cmd if c != "--check"], capture_output=True, text=True, encoding="utf-8", env=env)
    check("--phase docs refreshes it", p.returncode == 0 and (root / "how-to/llm-wiki/install.md").is_file(),
          p.stderr[-300:])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
