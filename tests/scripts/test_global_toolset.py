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

import argparse
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # the install prints arrows, as new-wiki.py does
sys.path.insert(0, str(ROOT / "scripts"))

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def _skip(test_name: str, reason: str):
    """A case that cannot run here: a visible line, no check recorded (a skip proves nothing, so it is no PASS)."""
    print(f"SKIP {test_name}: {reason}")


# --- task 243, step 1: the framework docs live at wiki/best-practices/framework/ in the toolset, the old copy goes.
# Each test below builds its own temp toolset through $WIKI_GLOBAL_CONFIG (a registry with no entry for it, so the
# toolset is <registry folder>/notebooks/global-toolset) and is run by _run() after the older checks.
OLD_DIR = "wiki/project/best-practices/framework"
NEW_DIR = "wiki/best-practices/framework"
SPEC_NAME = "wiki-frontmatter-best-practices.md"
DOC_NAMES = sorted(p.name for p in (ROOT / "framework-docs").glob("*.md"))


def _toolset_in(tmp: Path) -> Path:
    """A registry with no entry for the toolset and the machine config pointing at it; returns the toolset root."""
    vault = tmp / "vault"
    (vault / "notebooks").mkdir(parents=True)
    registry = vault / "linked-notebooks.json"
    registry.write_text(json.dumps({"notebooks": {"other": {"root": "notebooks/other"}}}), encoding="utf-8")
    cfg = tmp / "wiki-config.json"
    cfg.write_text(json.dumps({"registry": registry.as_posix()}), encoding="utf-8")
    os.environ["WIKI_GLOBAL_CONFIG"] = str(cfg)
    return wc.toolset_location()[0]


def _plant_old_docs(root: Path) -> list[str]:
    """The six docs at the old path, as an earlier install left them; returns their paths inside the toolset."""
    rels = []
    for name in DOC_NAMES:
        dst = root / OLD_DIR / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((ROOT / "framework-docs" / name).read_bytes())
        rels.append(f"{OLD_DIR}/{name}")
    return rels


def _docs_phase(*extra: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    cmd = [sys.executable, str(ROOT / "scripts" / "new-wiki.py"), "--phase", "docs", "--bootstrap-source", str(ROOT),
           *extra]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)


def test_empty_toolset_gets_docs_at_new_layout():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        same = all((root / NEW_DIR / n).is_file() and (root / NEW_DIR / n).read_bytes()
                   == (ROOT / "framework-docs" / n).read_bytes() for n in DOC_NAMES)
        check("new layout: the six docs written at wiki/best-practices/framework/, bytes as shipped",
              len(DOC_NAMES) == 6 and same, DOC_NAMES)
        check("new layout: status current", it.toolset_status(ROOT, root)["state"] == "current")
        check("new layout: nothing written under wiki/project/", not (root / "wiki" / "project").exists())


def test_old_copy_makes_status_stale_naming_the_six():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        rels = _plant_old_docs(root)
        st = it.toolset_status(ROOT, root)
        check("old copy: stale, remove names exactly the six old files, nothing to add or replace",
              st["state"] == "stale" and st["remove"] == sorted(rels) and not st["add"] and not st["replace"], st)


def test_refresh_clears_old_framework_folder_only():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        rels = _plant_old_docs(root)
        sibling = root / "wiki" / "project" / "best-practices" / "mine.md"
        sibling.write_text("kept\n", encoding="utf-8")
        it.seed_toolset(ROOT)
        check("refresh: the six old files deleted", not any((root / r).exists() for r in rels))
        check("refresh: the emptied old framework folder removed", not (root / OLD_DIR).exists())
        check("refresh: wiki/project/best-practices/ and its other file untouched",
              sibling.read_text(encoding="utf-8") == "kept\n")
        check("refresh: status current afterwards", it.toolset_status(ROOT, root)["state"] == "current")


def test_phase_docs_check_lists_old_files_as_remove_without_writing():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        rels = _plant_old_docs(root)
        before = {f.relative_to(root).as_posix(): f.read_bytes() for f in root.rglob("*") if f.is_file()}
        p = _docs_phase("--check")
        after = {f.relative_to(root).as_posix(): f.read_bytes() for f in root.rglob("*") if f.is_file()}
        lines = [ln.split() for ln in p.stdout.splitlines()]
        named = all(any(ln[:1] == ["REMOVE"] and ln[-1] == r for ln in lines) for r in rels)
        check("--check: exit 1, the six old files named as REMOVE", p.returncode == 1 and named,
              (p.returncode, p.stdout[-300:]))
        check("--check: nothing removed, the old files and folder still there",
              all((root / r).is_file() for r in rels))
        check("--check: every file in the toolset has the same name and bytes as before", before == after)


def test_phase_docs_refresh_turns_check_current():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        rels = _plant_old_docs(root)
        p = _docs_phase()
        check("--phase docs: exit 0, the old copy and its folder gone",
              p.returncode == 0 and not (root / OLD_DIR).exists() and not any((root / r).exists() for r in rels),
              (p.returncode, p.stderr[-300:]))
        p = _docs_phase("--check")
        check("--phase docs --check: exit 0 after the refresh", p.returncode == 0, (p.returncode, p.stdout[-300:]))


def test_unregistered_toolset_with_only_old_docs_is_migrated():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        rels = _plant_old_docs(root)  # the folder exists, holding the old docs only; the registry has no entry
        st = it.seed_toolset(ROOT)
        check("old docs only, no registry entry: the new six added, the old six removed, then current",
              all((root / NEW_DIR / n).is_file() for n in DOC_NAMES) and not any((root / r).exists() for r in rels)
              and it.toolset_status(ROOT, root)["state"] == "current" and st["registered"].startswith("added"), st)


@contextlib.contextmanager
def _held(path: Path):
    """An open handle: on Windows it makes unlink raise PermissionError (the held file of the plan's Failures)."""
    handle = open(path, "rb")
    try:
        yield
    finally:
        handle.close()


def test_held_old_file_is_named_in_failed_rest_proceeds():
    if sys.platform != "win32":  # an open handle blocks a delete only on Windows
        _skip("test_held_old_file_is_named_in_failed_rest_proceeds", "an open handle blocks a delete only on Windows")
        return
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        rels = _plant_old_docs(root)
        held_rel = rels[0]
        with _held(root / held_rel):
            try:
                st = it.seed_toolset(ROOT)
            except OSError as e:
                check("held file: seed_toolset does not raise", False, repr(e))
                return
            entries = st.get("failed")
            check("held file: exactly that file in failed, with a reason",
                  isinstance(entries, list) and len(entries) == 1
                  and entries[0]["path"] == (root / held_rel).as_posix() and entries[0]["reason"], entries)
            check("held file: the other five old files removed",
                  not any((root / r).exists() for r in rels[1:]) and (root / held_rel).is_file())
            check("held file: all six new docs still copied", all((root / NEW_DIR / n).is_file() for n in DOC_NAMES))
            check("held file: the old folder, still holding it, is not removed", (root / OLD_DIR).is_dir())


def test_phase_docs_reports_held_file_as_failed():
    if sys.platform != "win32":
        _skip("test_phase_docs_reports_held_file_as_failed", "an open handle blocks a delete only on Windows")
        return
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        rels = _plant_old_docs(root)
        with _held(root / rels[0]):
            p = _docs_phase()
        want = f"FAILED {(root / rels[0]).as_posix()}: "
        check("--phase docs with a held file: exit 1 and a `FAILED <path>: <reason>` line",
              p.returncode == 1 and any(ln.startswith(want) and len(ln) > len(want) for ln in p.stdout.splitlines()),
              (p.returncode, p.stdout[-300:]))


def test_dry_run_lists_no_failed_entries():
    if sys.platform != "win32":
        _skip("test_dry_run_lists_no_failed_entries", "an open handle blocks a delete only on Windows")
        return
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        rels = _plant_old_docs(root)
        with _held(root / rels[0]):
            st = it.seed_toolset(ROOT, dry_run=True)
        check("dry run with a held file: the old six reported to remove, no failed entries, all still there",
              st["remove"] == sorted(rels) and not st.get("failed") and all((root / r).is_file() for r in rels), st)


def test_non_md_items_in_old_folder_keep_the_folder():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        rels = _plant_old_docs(root)
        (root / OLD_DIR / "notes.txt").write_text("mine\n", encoding="utf-8")
        (root / OLD_DIR / "sub").mkdir()
        (root / OLD_DIR / "sub" / "keep.txt").write_text("mine too\n", encoding="utf-8")
        st = it.seed_toolset(ROOT)
        check("old folder with a .txt file and a subfolder: the .md files removed, no error reported",
              not any((root / r).exists() for r in rels) and not st["failed"], st["failed"])
        check("old folder with a .txt file and a subfolder: both stay, so does the folder",
              (root / OLD_DIR / "notes.txt").is_file() and (root / OLD_DIR / "sub" / "keep.txt").is_file())


def test_write_failure_is_listed_failed_rest_refreshed():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        (root / "wiki").mkdir(parents=True)
        (root / "wiki" / "best-practices").write_text("a plain file where the folder belongs\n", encoding="utf-8")
        st = it.seed_toolset(ROOT)
        failed_paths = sorted(Path(e["path"]).name for e in st["failed"])
        check("a plain file where wiki/best-practices/ belongs: the six docs and local/README.md listed in failed, "
              "each with a reason",
              failed_paths == sorted(DOC_NAMES + ["README.md"]) and all(e["reason"] for e in st["failed"]),
              st["failed"])
        check("a plain file where wiki/best-practices/ belongs: every other file still written",
              all((root / rel).is_file() for rel in it.toolset_files(ROOT)
                  if not rel.as_posix().startswith("wiki/best-practices/")))


def test_global_install_summary_names_failed_paths():
    summary = {"scripts_copied": 0, "helpers_copied": 0, "skills_installed": 0, "scripts_dest": "s",
               "skills_dest": "k", "scripts_dest_value": "s",
               "toolset": {"add": [], "replace": [], "remove": [], "registered": "already", "root": "r",
                           "failed": [{"path": "r/wiki/x.md", "reason": "PermissionError: held"}]}}
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        it.print_summary(summary)
    text = out.getvalue()
    check("install summary: a `FAILED <path>: <reason>` line and a word saying the refresh is incomplete",
          "FAILED r/wiki/x.md: PermissionError: held" in text and "incomplete" in text.lower(), text[-400:])


def _load_wiki_update():
    spec = importlib.util.spec_from_file_location("wiki_update_for_spec_lookup", ROOT / "scripts" / "wiki-update.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RUBRIC = "### tier rubric\nTOOLSET-NEW-PATH-RUBRIC\n\n### review cadence\n"


def test_spec_lookup_reads_the_toolset_at_new_path():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        spec = root / NEW_DIR / SPEC_NAME
        spec.parent.mkdir(parents=True)
        spec.write_text(RUBRIC, encoding="utf-8")
        text, where = _load_wiki_update().tier_rubric_text()
        check("spec lookup: the toolset's new-path spec is the one read",
              text is not None and "TOOLSET-NEW-PATH-RUBRIC" in text and Path(where).resolve() == spec.resolve(),
              (where, text))


def test_spec_lookup_falls_back_to_package_docs_without_new_path():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        stale = root / OLD_DIR / SPEC_NAME  # only the old path holds a spec: it is not read any more
        stale.parent.mkdir(parents=True)
        stale.write_text("### tier rubric\nOLD-PATH-RUBRIC\n\n### review cadence\n", encoding="utf-8")
        text, where = _load_wiki_update().tier_rubric_text()
        check("spec lookup: no spec at the new path -> framework-docs/ beside scripts/ (the old path is not read)",
              text is not None and "OLD-PATH-RUBRIC" not in text
              and Path(where).resolve() == (ROOT / "framework-docs" / SPEC_NAME).resolve(), (where, text))


# --- task 243, step 2: the toolset carries wiki/best-practices/local/README.md as a framework file; the user's files
# beside it are never added, changed, removed or listed in `remove`.
LOCAL_DIR = "wiki/best-practices/local"
LOCAL_README = f"{LOCAL_DIR}/README.md"
LOCAL_README_SRC = ROOT / "seed" / "best-practices-local" / "README.md"


def _shipped_readme() -> str:
    return LOCAL_README_SRC.read_text(encoding="utf-8") if LOCAL_README_SRC.is_file() else ""


def test_empty_toolset_gets_local_readme_with_shipped_bytes():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        before = it.toolset_status(ROOT, root)
        it.seed_toolset(ROOT)
        dst = root / LOCAL_README
        check("local README: reported as add on an empty toolset", LOCAL_README in before["add"], before["add"])
        check("local README: created with the shipped text's bytes",
              LOCAL_README_SRC.is_file() and dst.is_file() and dst.read_bytes() == LOCAL_README_SRC.read_bytes())
        check("local README: status current afterwards", it.toolset_status(ROOT, root)["state"] == "current")


def test_edited_local_readme_is_replaced_by_refresh():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        dst = root / LOCAL_README
        dst.write_text("edited by hand\n", encoding="utf-8")
        st = it.toolset_status(ROOT, root)
        check("edited README: stale with only it in replace", st["state"] == "stale"
              and st["replace"] == [LOCAL_README] and not st["add"] and not st["remove"], st)
        check("edited README: --check exits 1 before the refresh", _docs_phase("--check").returncode == 1)
        it.seed_toolset(ROOT)
        check("edited README: the shipped bytes restored",
              LOCAL_README_SRC.is_file() and dst.read_bytes() == LOCAL_README_SRC.read_bytes())
        check("edited README: --check exits 0 after the refresh", _docs_phase("--check").returncode == 0)
        shipped = LOCAL_README_SRC.read_bytes() if LOCAL_README_SRC.is_file() else b"x\n"
        dst.write_bytes(shipped[: len(shipped) // 2])  # an older shipped text, as an earlier install left it
        st = it.toolset_status(ROOT, root)
        it.seed_toolset(ROOT)
        check("older shipped README: stale with it in replace, then restored",
              st["state"] == "stale" and st["replace"] == [LOCAL_README] and dst.read_bytes() == shipped, st)


def test_deleted_local_readme_is_added_again():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        (root / LOCAL_README).unlink()
        st = it.toolset_status(ROOT, root)
        check("deleted README: add names it", st["add"] == [LOCAL_README] and st["state"] == "stale", st)
        it.seed_toolset(ROOT)
        check("deleted README: created again with the shipped bytes",
              LOCAL_README_SRC.is_file() and (root / LOCAL_README).read_bytes() == LOCAL_README_SRC.read_bytes())


def test_user_files_in_local_are_untouched():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        mine = root / LOCAL_DIR / "my-notes.md"
        mine.write_bytes(b"my own notes\r\nline two\n")
        deep = root / LOCAL_DIR / "my-folder" / "deeper" / "kept.md"
        deep.parent.mkdir(parents=True)
        deep.write_bytes(b"kept\n")
        snap = {f.relative_to(root).as_posix(): f.read_bytes() for f in (root / LOCAL_DIR).rglob("*") if f.is_file()}
        st = it.toolset_status(ROOT, root)
        check("user files: status current and nothing in remove with them there",
              st["state"] == "current" and not st["remove"] and not st["add"] and not st["replace"], st)
        it.seed_toolset(ROOT)
        st2 = it.seed_toolset(ROOT)
        after = {f.relative_to(root).as_posix(): f.read_bytes() for f in (root / LOCAL_DIR).rglob("*") if f.is_file()}
        check("user files: two refreshes leave every file's name and bytes as they were", snap == after
              and f"{LOCAL_DIR}/my-notes.md" in after and f"{LOCAL_DIR}/my-folder/deeper/kept.md" in after, after)
        check("user files: the second refresh wrote and removed nothing",
              not st2["add"] and not st2["replace"] and not st2["remove"] and not st2["failed"], st2)
        check("user folders: the subfolders are still there", deep.is_file() and mine.is_file())


def test_dry_run_reports_local_readme_writes_nothing():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        st = it.seed_toolset(ROOT, dry_run=True)
        check("dry run, empty toolset: README in add, nothing written (the toolset folder is not even created)",
              LOCAL_README in st["add"] and not root.exists(), st["add"])
        it.seed_toolset(ROOT)
        dst = root / LOCAL_README
        dst.write_text("edited by hand\n", encoding="utf-8")
        snap = {f.relative_to(root).as_posix(): f.read_bytes() for f in root.rglob("*") if f.is_file()}
        st = it.seed_toolset(ROOT, dry_run=True)
        after = {f.relative_to(root).as_posix(): f.read_bytes() for f in root.rglob("*") if f.is_file()}
        check("dry run, edited README: README in replace, every file in the toolset the same name and bytes",
              st["replace"] == [LOCAL_README] and snap == after, st)


def test_shipped_local_readme_names_both_places():
    lines = [ln.lower() for ln in _shipped_readme().splitlines()]
    check("shipped README: one line gives the global toolset's wiki/best-practices/local/ for every wiki",
          any("every wiki" in ln and "global toolset's" in ln and "wiki/best-practices/local/" in ln for ln in lines),
          lines)
    check("shipped README: one line gives this wiki's own wiki/best-practices/local/ for this wiki only",
          any("this wiki only" in ln and "this wiki's" in ln and "wiki/best-practices/local/" in ln
              and "global toolset" not in ln for ln in lines), lines)


def test_shipped_local_readme_tells_the_reader_to_ask_when_unsure():
    lines = [ln.lower() for ln in _shipped_readme().splitlines()]
    check("shipped README: one line tells the reader, when unsure which, to ask the user",
          any("when unsure which" in ln and "ask the user" in ln for ln in lines), lines)


def test_shipped_local_readme_says_do_not_edit_it():
    text = _shipped_readme().lower()
    check("shipped README: it is a framework file replaced on update, do not edit it, name a file after the doc",
          "do not edit" in text and "replaced" in text and "name a file after the framework doc" in text, text[-400:])


def test_shipped_local_readme_has_the_lint_frontmatter():
    text = _shipped_readme()
    head = text.split("---")[1] if text.startswith("---") and text.count("---") >= 2 else ""
    keys = {ln.split(":", 1)[0].strip(): ln.split(":", 1)[1].strip() for ln in head.splitlines() if ":" in ln}
    check("shipped README: frontmatter has title, date, tags and tier",
          all(keys.get(k) for k in ("title", "date", "tags", "tier")), keys)
    check("shipped README: framework-contract true, framework-version 1",
          keys.get("framework-contract") == "true" and keys.get("framework-version") == "1", keys)
    import _entry_checks as ec  # the parser and checks the lint uses
    fm, _body = ec.split_frontmatter(text)
    check("shipped README: the lint's frontmatter parser loads it with no finding and treats it as a framework page",
          fm.get("title") and not ec.check_frontmatter_loadable(text)
          and ec.is_exempt(LOCAL_README_SRC, fm), (fm, ec.check_frontmatter_loadable(text)))


def test_shipped_local_readme_has_no_template_placeholder():
    text = _shipped_readme()
    check("shipped README: not empty and no {{ placeholder, so rendering equals copying",
          bool(text.strip()) and "{{" not in text, text[:200])


def test_plain_file_where_local_belongs_lists_readme_in_failed():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        shutil.rmtree(root / LOCAL_DIR)
        (root / LOCAL_DIR).write_text("a plain file where the folder belongs\n", encoding="utf-8")
        commands = root / "how-to/llm-wiki/commands.md"
        commands.write_text("edited by hand\n", encoding="utf-8")
        try:
            st = it.seed_toolset(ROOT)
        except OSError as e:
            check("plain file: seed_toolset does not raise", False, repr(e))
            return
        failed = st.get("failed")
        check("plain file: exactly the README in failed, with a reason",
              isinstance(failed, list) and len(failed) == 1 and failed[0]["path"] == (root / LOCAL_README).as_posix()
              and failed[0]["reason"], failed)
        check("plain file: every other file still refreshed (the edited page restored)",
              commands.read_bytes() == (ROOT / "wiki-seed" / "commands.md").read_bytes())
        p = _docs_phase()
        want = f"FAILED {(root / LOCAL_README).as_posix()}: "
        check("plain file: --phase docs exits 1 printing `FAILED <path>: <reason>`",
              p.returncode == 1 and any(ln.startswith(want) and len(ln) > len(want) for ln in p.stdout.splitlines()),
              (p.returncode, p.stdout[-300:]))


def test_unwritable_readme_replacement_is_listed_failed_rest_done():
    if hasattr(os, "geteuid") and os.geteuid() == 0:  # root writes through a read-only file
        _skip("test_unwritable_readme_replacement_is_listed_failed_rest_done",
              "root writes through a read-only file, nothing proved here")
        return
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        dst = root / LOCAL_README
        dst.write_text("edited by hand\n", encoding="utf-8")
        commands = root / "how-to/llm-wiki/commands.md"
        commands.write_text("edited by hand\n", encoding="utf-8")
        os.chmod(dst, 0o444)  # replacing it raises PermissionError, as a file held by another program does
        try:
            st = it.seed_toolset(ROOT)
        except OSError as e:
            check("unwritable README: seed_toolset does not raise", False, repr(e))
            return
        finally:
            os.chmod(dst, 0o644)
        failed = st.get("failed")
        check("unwritable README: exactly that file in failed, with a reason",
              isinstance(failed, list) and len(failed) == 1 and failed[0]["path"] == dst.as_posix()
              and failed[0]["reason"], failed)
        check("unwritable README: the other edited page restored, the README left as it was",
              commands.read_bytes() == (ROOT / "wiki-seed" / "commands.md").read_bytes()
              and dst.read_text(encoding="utf-8") == "edited by hand\n")


def test_missing_readme_source_is_skipped_by_status():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        pkg = Path(t) / "pkg"
        (pkg / "seed").mkdir(parents=True)
        (pkg / "seed" / "global-toolset-README.md").write_text("toolset readme\n", encoding="utf-8")
        listed = it.toolset_files(pkg)
        st = it.toolset_status(pkg, root)
        check("README source missing from the package: listed, but not in add, replace or remove, no error",
              Path(LOCAL_README) in listed and LOCAL_README not in st["add"] + st["replace"] + st["remove"]
              and st["add"] == ["README.md"], (list(listed), st))


def _plain_file_where_best_practices_belongs(root: Path) -> None:
    (root / "wiki").mkdir(parents=True)
    (root / "wiki" / "best-practices").write_text("a plain file where the folder belongs\n", encoding="utf-8")


def test_failed_reason_reads_error_class_colon_message():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        _plain_file_where_best_practices_belongs(root)
        st = it.seed_toolset(ROOT)
        odd = [e["reason"] for e in st["failed"] if not re.match(r"^[A-Z]\w*Error: \S", e["reason"])]
        check("every failed reason reads `<ErrorClass>: <message>`", bool(st["failed"]) and not odd, odd or st["failed"])


def test_unremovable_old_folder_is_listed_failed_not_raised():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        it.seed_toolset(ROOT)
        _plant_old_docs(root)
        old = root / OLD_DIR
        real_rmdir = Path.rmdir

        def rmdir(self):
            if self == old:
                raise PermissionError("held by another program")
            return real_rmdir(self)

        with mock.patch.object(Path, "rmdir", rmdir):
            try:
                st = it.seed_toolset(ROOT)
            except OSError as e:
                check("old folder that cannot be removed: seed_toolset does not raise", False, repr(e))
                return
        check("old folder that cannot be removed: exactly that folder in failed, reason says why",
              [e["path"] for e in st["failed"]] == [old.as_posix()]
              and st["failed"][0]["reason"] == "PermissionError: held by another program", st["failed"])


def test_install_summary_counts_the_failed_operations():
    summary = {"scripts_copied": 0, "helpers_copied": 0, "skills_installed": 0, "scripts_dest": "s",
               "skills_dest": "k", "scripts_dest_value": "s",
               "toolset": {"add": [], "replace": [], "remove": [], "registered": "already", "root": "r",
                           "failed": [{"path": "r/a.md", "reason": "PermissionError: held"},
                                      {"path": "r/b.md", "reason": "PermissionError: held"}]}}
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        it.print_summary(summary)
    check("install summary: the incomplete line counts the two failed operations",
          "INCOMPLETE, 2 file operation(s) failed" in out.getvalue(), out.getvalue()[-400:])


def test_phase_docs_failure_line_is_a_warning_with_the_count():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        _plain_file_where_best_practices_belongs(root)
        p = _docs_phase()
        want = re.compile(rf"(?<!\d){len(DOC_NAMES) + 1} file operation\(s\) FAILED, so the refresh is incomplete")
        check(f"--phase docs with {len(DOC_NAMES) + 1} failed writes: exit 1, a `!` warning line counts them",
              p.returncode == 1 and any(ln.startswith("[new-wiki] ! ") and want.search(ln) for ln in p.stderr.splitlines()),
              (p.returncode, p.stderr[-400:]))


def _load_script(file_name: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / "scripts" / file_name)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _install_summary_with_failed_toolset(root: Path) -> dict:
    """What install_tooling returns after a real refresh of a toolset with a plain file where best-practices/ belongs."""
    _plain_file_where_best_practices_belongs(root)
    toolset = it.seed_toolset(ROOT)
    return {"scripts_copied": 0, "helpers_copied": 0, "skills_installed": 0, "scripts_dest": "s",
            "skills_dest": "k", "scripts_dest_value": "s", "toolset": toolset}


def test_wiki_upgrade_exits_1_when_a_toolset_write_failed():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        summary = _install_summary_with_failed_toolset(root)
        mod = _load_script("wiki-upgrade.py", "wiki_upgrade_for_exit_code")
        with (mock.patch.object(mod, "install_tooling", return_value=summary),
              mock.patch.object(mod, "derive_bootstrap_source", return_value=ROOT),
              mock.patch.object(sys, "argv", ["wiki-upgrade.py"]),
              contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO())):
            code = mod.main()
        check("wiki-upgrade.py with a failed toolset write: exit 1, the FAILED lines still printed",
              code == 1 and "FAILED " in out.getvalue(), (code, out.getvalue()[-300:]))


def test_wiki_upgrade_exits_1_when_a_skill_was_refused():
    summary = {"scripts_copied": 0, "helpers_copied": 0, "skills_installed": 0, "scripts_dest": "s",
               "skills_dest": "k", "scripts_dest_value": "s", "frontmatter_failed": ["wrap-up"]}
    mod = _load_script("wiki-upgrade.py", "wiki_upgrade_for_refused_skill")
    with (mock.patch.object(mod, "install_tooling", return_value=summary),
          mock.patch.object(mod, "print_summary"),
          mock.patch.object(mod, "derive_bootstrap_source", return_value=ROOT),
          mock.patch.object(sys, "argv", ["wiki-upgrade.py"]),
          contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO())):
        code = mod.main()
    check("wiki-upgrade.py with a refused skill: exit 1", code == 1, code)


def test_new_wiki_tooling_mode_exits_1_when_a_toolset_write_failed():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        summary = _install_summary_with_failed_toolset(root)
        mod = _load_script("new-wiki.py", "new_wiki_for_exit_code")
        args = mock.Mock(tool="claude-code", dry_run=False, bootstrap_source=str(ROOT))
        with (mock.patch.object(mod, "_install_tooling", return_value=summary),
              contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO())):
            code = mod.phase_tooling(args)
        check("new-wiki.py --mode tooling with a failed toolset write: exit 1, the FAILED lines still printed",
              code == 1 and "FAILED " in out.getvalue(), (code, out.getvalue()[-300:]))


class _ArgsDefaultingToNone(argparse.Namespace):
    """Parsed arguments where every option the test does not give is None, as an unset flag is."""

    def __getattr__(self, name: str) -> None:
        return None


def test_scaffold_stops_when_the_global_install_it_runs_failed_a_toolset_write():
    with tempfile.TemporaryDirectory() as t:
        root = _toolset_in(Path(t))
        summary = _install_summary_with_failed_toolset(root)
        mod = _load_script("new-wiki.py", "new_wiki_for_exit_code_phase_b")
        target = Path(t) / "proj"
        args = _ArgsDefaultingToNone(target_folder=str(target), bootstrap_source=str(ROOT), project_name="proj",
                                     tool="claude-code", project_folder="stubs", research_folder="stubs",
                                     install_global_if_missing=True, dry_run=False)
        install = mock.Mock(return_value=summary)
        err = io.StringIO()
        with (mock.patch.dict(os.environ, {"WIKI_TOOLING_DRY_RUN": "0"}),
              mock.patch.object(mod, "global_tooling_status", return_value={"state": "missing", "complete": False}),
              mock.patch.object(mod, "format_tooling_status", return_value=""),
              mock.patch.object(mod, "_install_tooling", install),
              contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err)):
            code = mod.phase_b(args)
        check("--install-global-if-missing with a failed toolset write: exit 1 and no project folder created",
              code == 1 and not target.exists(), (code, target.exists()))
        check("--install-global-if-missing with a failed toolset write: the install ran once, the message says why",
              install.call_count == 1 and "the global toolset refresh is incomplete" in err.getvalue(),
              (install.call_count, err.getvalue()[-300:]))
        check("--install-global-if-missing with a failed toolset write: the message names the refresh command",
              "install-wiki.ps1 -RefreshOnly" in err.getvalue(), err.getvalue()[-300:])


def test_scaffold_warning_names_a_stale_toolset():
    with tempfile.TemporaryDirectory() as t:
        mod = _load_script("new-wiki.py", "new_wiki_for_stale_toolset_warning")
        target = Path(t) / "proj"
        target.mkdir()
        (target / "unrelated.txt").write_text("stops the scaffold right after the warning\n", encoding="utf-8")
        args = _ArgsDefaultingToNone(target_folder=str(target), bootstrap_source=str(ROOT), project_name="proj",
                                     tool="claude-code", dry_run=False)
        status = {"state": "stale", "complete": True, "current": False, "stale_skills": [], "stale_scripts": [],
                  "stale_agents": [], "toolset": {"state": "stale"}}
        err = io.StringIO()
        with (mock.patch.object(mod, "global_tooling_status", return_value=status),
              contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err)):
            mod.phase_b(args)
        warning = next((ln for ln in err.getvalue().splitlines() if "differs from the bootstrap source" in ln), "")
        check("stale toolset, current skills and scripts: the warning names the toolset docs and the refresh command",
              "toolset docs" in warning and "()" not in warning and "install-wiki.ps1 -RefreshOnly" in warning,
              err.getvalue()[-400:])


def _run(fn):
    """Run one test function; every check it records is named after it, and a crash is a failed check, not the end."""
    first = len(results)
    try:
        fn()
    except Exception as e:  # noqa: BLE001 - a crash is a failed check named after the test, not the end of the file
        check(f"raised {type(e).__name__}: {e}", False)
    results[first:] = [(ok, f"{fn.__name__}: {name}") for ok, name in results[first:]]


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
                                             "wiki/best-practices/framework/wiki-frontmatter-best-practices.md",
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
    src_bytes = (ROOT / "wiki-seed" / "getting-started.md").read_bytes()
    lf = src_bytes.replace(b"\r\n", b"\n")
    crlf.write_bytes(lf if src_bytes != lf else lf.replace(b"\n", b"\r\n"))  # the other line endings
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
          f"{root.as_posix()}/wiki/best-practices/framework/wiki-frontmatter-best-practices.md" in agent)

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

for _test in (test_empty_toolset_gets_docs_at_new_layout, test_old_copy_makes_status_stale_naming_the_six,
              test_refresh_clears_old_framework_folder_only,
              test_phase_docs_check_lists_old_files_as_remove_without_writing,
              test_phase_docs_refresh_turns_check_current,
              test_unregistered_toolset_with_only_old_docs_is_migrated,
              test_held_old_file_is_named_in_failed_rest_proceeds, test_phase_docs_reports_held_file_as_failed,
              test_dry_run_lists_no_failed_entries, test_non_md_items_in_old_folder_keep_the_folder,
              test_write_failure_is_listed_failed_rest_refreshed, test_global_install_summary_names_failed_paths,
              test_spec_lookup_reads_the_toolset_at_new_path,
              test_spec_lookup_falls_back_to_package_docs_without_new_path,
              test_empty_toolset_gets_local_readme_with_shipped_bytes, test_edited_local_readme_is_replaced_by_refresh,
              test_deleted_local_readme_is_added_again, test_user_files_in_local_are_untouched,
              test_dry_run_reports_local_readme_writes_nothing, test_shipped_local_readme_names_both_places,
              test_shipped_local_readme_tells_the_reader_to_ask_when_unsure,
              test_shipped_local_readme_says_do_not_edit_it, test_shipped_local_readme_has_the_lint_frontmatter,
              test_shipped_local_readme_has_no_template_placeholder,
              test_plain_file_where_local_belongs_lists_readme_in_failed,
              test_unwritable_readme_replacement_is_listed_failed_rest_done,
              test_missing_readme_source_is_skipped_by_status,
              test_failed_reason_reads_error_class_colon_message,
              test_unremovable_old_folder_is_listed_failed_not_raised,
              test_install_summary_counts_the_failed_operations,
              test_phase_docs_failure_line_is_a_warning_with_the_count,
              test_wiki_upgrade_exits_1_when_a_toolset_write_failed,
              test_new_wiki_tooling_mode_exits_1_when_a_toolset_write_failed,
              test_wiki_upgrade_exits_1_when_a_skill_was_refused,
              test_scaffold_stops_when_the_global_install_it_runs_failed_a_toolset_write,
              test_scaffold_warning_names_a_stale_toolset):
    _run(_test)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
