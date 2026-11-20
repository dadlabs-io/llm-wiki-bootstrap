#!/usr/bin/env python3
"""Checks for task #243, step 3: a new wiki gets wiki/best-practices/local/README.md. Never shipped.

    uv run python tests/scripts/test_local_folder.py    # exit 0 = every check passed

`taxonomy_for` is called directly, and `new-wiki.py --phase B` runs as a subprocess into a new temp target and a
temp vault, under a temporary home (HOME, USERPROFILE and $WIKI_GLOBAL_CONFIG), so the machine's own ~/.claude,
registry and toolset are never read or written. The tooling state is pinned to `installed`, so Phase B installs
nothing.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(ROOT / "scripts"))
import _wiki_config as wc  # noqa: E402

SHIPPED_README = ROOT / "seed" / "best-practices-local" / "README.md"
LOCAL = "best-practices/local"
RESEARCH_STUBS = ["research/active", "research/long-term", "research/tooling", "research/best-practices",
                  "research/interesting-docs"]
PROJECT_STUBS = ["project/components", "project/decisions", "project/architecture", "project/patterns",
                 "project/troubleshooting", "project/best-practices"]

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


class Scaffold:
    """One temp home, vault and target; `run` calls Phase B into it."""

    def __init__(self, tmp: Path, name: str = "demo"):
        self.tmp, self.name = tmp, name
        self.home = tmp / "home"
        self.home.mkdir()
        (self.home / ".claude").mkdir()
        self.vault = tmp / "vault"
        (self.vault / "notebooks").mkdir(parents=True)
        self.registry = self.vault / "linked-notebooks.json"
        self.registry.write_text(json.dumps({"notebooks": {}}), encoding="utf-8")
        self.target = tmp / "work" / name
        self.target.mkdir(parents=True)
        self.global_cfg = tmp / "wiki-config.json"
        self.global_cfg.write_text(json.dumps({"registry": self.registry.as_posix()}), encoding="utf-8")
        self.wiki = self.vault / "notebooks" / name / "wiki"

    def run(self, project: str = "stubs", research: str = "stubs", extra: tuple = (),
            bootstrap: Path = ROOT) -> subprocess.CompletedProcess:
        env = {**os.environ, "HOME": str(self.home), "USERPROFILE": str(self.home), "GIT_CONFIG_NOSYSTEM": "1",
               "PYTHONIOENCODING": "utf-8", "WIKI_GLOBAL_CONFIG": str(self.global_cfg),
               "WIKI_TOOLING_STATE": "installed"}
        cmd = [sys.executable, str(ROOT / "scripts" / "new-wiki.py"), "--phase", "B",
               "--target-folder", str(self.target), "--project-name", self.name,
               "--project-description", f"Wiki for {self.name}", "--project-folder", project,
               "--research-folder", research, "--vault-root", str(self.vault / "notebooks"),
               "--registry", str(self.registry), "--bootstrap-source", str(bootstrap), "--drive-enabled", "no",
               "--skills-install", "global", *extra]
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)


def _snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): (p.read_bytes() if p.is_file() else None) for p in root.rglob("*")}


def test_taxonomy_puts_best_practices_local_before_sessions_for_all_nine_pairs():
    bad = []
    for project, pstubs in (("stubs", PROJECT_STUBS), ("empty", ["project"]), ("none", [])):
        for research, rstubs in (("stubs", RESEARCH_STUBS), ("empty", ["research"]), ("none", [])):
            got = wc.taxonomy_for(project, research)
            if got != rstubs + pstubs + [LOCAL, "sessions"]:
                bad.append((project, research, got))
    check("taxonomy_for: nine pairs, each the old folders then best-practices/local then sessions", not bad, bad)


def _phase_b_cases(project: str):
    with tempfile.TemporaryDirectory() as t:
        sc = Scaffold(Path(t))
        p = sc.run(project=project)
        readme = sc.wiki / LOCAL / "README.md"  # read before the temp folder goes
        return p, (readme.read_bytes() if readme.is_file() else None), (sc.wiki / "project").exists()


def test_phase_b_writes_local_readme_with_shipped_bytes_for_stubs():
    p, readme, _ = _phase_b_cases("stubs")
    check("--project-folder stubs: exit 0, best-practices/local/README.md has the shipped bytes",
          p.returncode == 0 and readme == SHIPPED_README.read_bytes(),
          (p.returncode, p.stdout[-300:], p.stderr[-300:]))


def test_phase_b_writes_local_readme_with_shipped_bytes_for_empty():
    p, readme, _ = _phase_b_cases("empty")
    check("--project-folder empty: exit 0, best-practices/local/README.md has the shipped bytes",
          p.returncode == 0 and readme == SHIPPED_README.read_bytes(),
          (p.returncode, p.stdout[-300:], p.stderr[-300:]))


def test_phase_b_writes_local_readme_with_shipped_bytes_for_none():
    p, readme, project_exists = _phase_b_cases("none")
    check("--project-folder none: exit 0, best-practices/local/README.md has the shipped bytes, no project/ folder",
          p.returncode == 0 and readme == SHIPPED_README.read_bytes() and not project_exists,
          (p.returncode, p.stdout[-300:], p.stderr[-300:]))


def test_phase_b_readme_folder_list_has_a_best_practices_local_line():
    with tempfile.TemporaryDirectory() as t:
        sc = Scaffold(Path(t))
        sc.run(project="none")
        listed = (sc.wiki / "README.md").read_text(encoding="utf-8") if (sc.wiki / "README.md").is_file() else ""
        check("the wiki's README folder list has a best-practices/local/ line",
              any(ln.startswith("- `best-practices/local/`") for ln in listed.splitlines()), listed[-600:])


def test_phase_b_readme_local_line_carries_its_note():
    with tempfile.TemporaryDirectory() as t:
        sc = Scaffold(Path(t))
        p = sc.run(project="none")
        listed = (sc.wiki / "README.md").read_text(encoding="utf-8") if (sc.wiki / "README.md").is_file() else ""
        line = next((ln for ln in listed.splitlines() if ln.startswith("- `best-practices/local/`")), "")
        check("Phase B exits 0, and the wiki's README line for best-practices/local/ carries a note naming the "
              "framework docs",
              p.returncode == 0 and line.startswith("- `best-practices/local/` — ") and "framework docs" in line,
              (p.returncode, line))


def test_phase_b_summary_lists_best_practices_local_before_sessions():
    with tempfile.TemporaryDirectory() as t:
        sc = Scaffold(Path(t))
        p = sc.run(project="none")
        try:
            summary = json.loads(p.stdout[p.stdout.index("{"):p.stdout.rindex("}") + 1])
        except ValueError:
            summary = {}
        check("the Phase B summary's wiki_folders lists best-practices/local before sessions",
              summary.get("wiki_folders", [])[-2:] == [LOCAL, "sessions"], summary.get("wiki_folders"))


def _finding_kinds(report: str, path: str) -> set:
    """The report's section headings under which `path` is listed as a bullet (one kind of finding each)."""
    kinds, heading = set(), ""
    for ln in report.splitlines():
        if ln.startswith("#"):
            heading = ln
        elif ln.startswith(f"- `{path}`"):
            kinds.add(heading)
    return kinds


def test_lint_of_a_fresh_scaffold_draws_no_finding_on_the_local_readme_that_home_does_not():
    with tempfile.TemporaryDirectory() as t:
        sc = Scaffold(Path(t))
        sc.run()
        bad = sc.wiki / LOCAL / "bad-note.md"
        has_readme = (sc.wiki / LOCAL / "README.md").is_file()

        def lint():
            """What the lint prints plus the report file it saves (the findings are in both)."""
            q = subprocess.run([sys.executable, str(ROOT / "scripts" / "wiki-lint-mechanical.py"),
                                "--topic", sc.name, "--vault", str(sc.vault / "notebooks")],
                               capture_output=True, text=True, encoding="utf-8",
                               env={**os.environ, "HOME": str(sc.home), "USERPROFILE": str(sc.home),
                                    "WIKI_GLOBAL_CONFIG": str(sc.global_cfg), "PYTHONIOENCODING": "utf-8"})
            report = sc.vault / "notebooks" / sc.name / "_inbox" / "reports" / "lint-report.md"
            saved = report.read_text(encoding="utf-8") if report.is_file() else ""
            return "Report saved to" in q.stdout, q.stdout + q.stderr + saved

        ran, out = lint()
        readme_kinds = _finding_kinds(out, f"{LOCAL}/README.md")
        home_kinds = _finding_kinds(out, "HOME.md")
        check("lint of the fresh scaffold: the README is there, lint ran, and every kind of finding on the "
              "local README is a kind the scaffold's HOME.md draws too",
              has_readme and ran and bool(home_kinds) and readme_kinds <= home_kinds,
              (has_readme, ran, sorted(readme_kinds - home_kinds), sorted(home_kinds)))
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text("no frontmatter here\n", encoding="utf-8")
        ran2, out2 = lint()
        check("control: the same lint does name a note without frontmatter placed in best-practices/local/",
              has_readme and ran2 and "bad-note" in out2, out2[-400:])


def test_dry_run_prints_would_lines_for_the_local_folder_with_its_readme():
    with tempfile.TemporaryDirectory() as t:
        sc = Scaffold(Path(t))
        p = sc.run(extra=("--dry-run",))
        lines = p.stdout.splitlines()
        folder = [ln for ln in lines if ln.startswith("WOULD mkdir") and ln.replace("\\", "/").endswith(LOCAL)]
        readme = [ln for ln in lines if ln.startswith("WOULD write")
                  and f"{LOCAL}/README.md" in ln.replace("\\", "/")]
        check("--dry-run: exit 0, a WOULD mkdir line for best-practices/local and a WOULD write line for its README",
              p.returncode == 0 and len(folder) == 1 and len(readme) == 1, (p.returncode, p.stdout[-500:]))


def test_dry_run_leaves_the_temp_tree_unchanged():
    with tempfile.TemporaryDirectory() as t:
        sc = Scaffold(Path(t))
        before = _snapshot(Path(t))
        p = sc.run(extra=("--dry-run",))
        after = _snapshot(Path(t))
        check("--dry-run: exit 0, every file and folder in the temp tree has the same name and bytes as before",
              p.returncode == 0 and before == after, (p.returncode, sorted(set(after) ^ set(before))))


def test_missing_readme_source_stops_the_scaffold_before_any_best_practices_folder():
    with tempfile.TemporaryDirectory() as t:
        pkg = Path(t) / "pkg"
        shutil.copytree(ROOT / "seed", pkg / "seed")
        shutil.copytree(ROOT / "templates", pkg / "templates")
        shutil.rmtree(pkg / "seed" / "best-practices-local")
        (Path(t) / "run").mkdir()
        sc = Scaffold(Path(t) / "run")
        p = sc.run(bootstrap=pkg)
        out = p.stdout + p.stderr
        named = "best-practices-local" in out
        folders = [q for q in (Path(t) / "run").rglob("best-practices") if q.is_dir() and q.parent == sc.wiki]
        check("missing README source: non-zero exit, the missing file named, no wiki/best-practices folder",
              p.returncode != 0 and named and not folders, (p.returncode, out[-500:], folders))


def test_existing_claude_md_is_kept_byte_for_byte():
    with tempfile.TemporaryDirectory() as t:
        sc = Scaffold(Path(t))
        mine = sc.target / "CLAUDE.md"
        mine.write_bytes(b"# my own rules\r\nkeep me\r\n")
        p = sc.run(extra=("--force",))
        check("a target that already has a CLAUDE.md: exit 0, the file's bytes unchanged",
              p.returncode == 0 and mine.read_bytes() == b"# my own rules\r\nkeep me\r\n",
              (p.returncode, mine.read_bytes(), p.stdout[-300:]))


def test_first_run_renders_the_three_wiki_scaffold_files():
    with tempfile.TemporaryDirectory() as t:
        sc = Scaffold(Path(t))
        p = sc.run()
        texts = {n: (sc.wiki / n).read_text(encoding="utf-8") if (sc.wiki / n).is_file() else None
                 for n in ("_MAP.md", "README.md", "HOME.md")}
        check("a first run: _MAP.md, README.md and HOME.md written, non-empty, no template placeholder left",
              p.returncode == 0 and all(v and "{{" not in v for v in texts.values())
              and f"# {sc.name} — wiki" in texts["README.md"], (p.returncode, {k: bool(v) for k, v in texts.items()}))


# ---------- step 4: a user's note in best-practices/local/ is linted like any entry (seam F) ----------
_NOTE_HEAD = """---
title: "My local note"
date: 2026-11-19
source_url: internal://local-note
ingested_by: human
{tags}tier: self
confidence: high
last_reviewed: 2026-11-19
review_after: 2027-02-19
standalone: "a user's own note: nothing links to it by design"
---

# My local note
"""
_NOTE_BODY = """
## TL;DR

A note of my own about how this wiki should be written.

## Related

- [Home](../../HOME.md)
- [Read me](../../README.md)
"""
VALID_NOTE = _NOTE_HEAD.format(tags="tags: [local, notes, stub]\n") + _NOTE_BODY
NOTE_WITHOUT_TAGS = _NOTE_HEAD.format(tags="") + _NOTE_BODY
NOTE_WITHOUT_FRONTMATTER = "# My local note\n" + _NOTE_BODY


def _lint_report_after_writing(notes: dict) -> str:
    """Scaffold a fresh wiki, write each `{path under wiki/: text}` into it, run the mechanical lint over it, and
    return what it prints plus the report file it saves (the findings are in both)."""
    with tempfile.TemporaryDirectory() as t:
        sc = Scaffold(Path(t))
        sc.run()
        for rel, text in notes.items():
            p = sc.wiki / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        q = subprocess.run([sys.executable, str(ROOT / "scripts" / "wiki-lint-mechanical.py"),
                            "--topic", sc.name, "--vault", str(sc.vault / "notebooks")],
                           capture_output=True, text=True, encoding="utf-8",
                           env={**os.environ, "HOME": str(sc.home), "USERPROFILE": str(sc.home),
                                "WIKI_GLOBAL_CONFIG": str(sc.global_cfg), "PYTHONIOENCODING": "utf-8"})
        report = sc.vault / "notebooks" / sc.name / "_inbox" / "reports" / "lint-report.md"
        saved = report.read_text(encoding="utf-8") if report.is_file() else ""
        return q.stdout + q.stderr + saved


def test_valid_note_in_best_practices_local_draws_no_lint_finding():
    out = _lint_report_after_writing({f"{LOCAL}/my-notes.md": VALID_NOTE,
                                      f"{LOCAL}/bad-note.md": NOTE_WITHOUT_FRONTMATTER})
    # the report lists a page that declares `standalone:` under its own "declared" heading: a list, not a finding
    seen = {k for k in _finding_kinds(out, f"{LOCAL}/my-notes.md") if "Standalone Pages" not in k}
    control = _finding_kinds(out, f"{LOCAL}/bad-note.md")
    check("lint: a note with valid frontmatter in best-practices/local/ is named under no finding "
          "(the control, a note without frontmatter beside it, is named)",
          "Report saved to" in out and not seen and bool(control), (sorted(seen), sorted(control), out[-600:]))


def test_note_without_tags_in_best_practices_local_draws_the_finding_it_draws_elsewhere():
    out = _lint_report_after_writing({f"{LOCAL}/my-notes.md": NOTE_WITHOUT_TAGS,
                                      "research/active/my-notes.md": NOTE_WITHOUT_TAGS})
    here = _finding_kinds(out, f"{LOCAL}/my-notes.md")
    there = _finding_kinds(out, "research/active/my-notes.md")
    check("lint: the same note without `tags` is named under the same findings in best-practices/local/ as in "
          "research/active/, among them the missing-tags one",
          here == there and any("tags" in k.lower() for k in here), (sorted(here), sorted(there), out[-600:]))


def test_note_without_frontmatter_in_best_practices_local_draws_the_finding_it_draws_elsewhere():
    out = _lint_report_after_writing({f"{LOCAL}/my-notes.md": NOTE_WITHOUT_FRONTMATTER,
                                      "research/active/my-notes.md": NOTE_WITHOUT_FRONTMATTER})
    here = _finding_kinds(out, f"{LOCAL}/my-notes.md")
    there = _finding_kinds(out, "research/active/my-notes.md")
    check("lint: the same note without frontmatter is named under the same findings in best-practices/local/ as in "
          "research/active/, and there is at least one",
          here == there and bool(here), (sorted(here), sorted(there), out[-600:]))


# ---------- step 4b: _MAP.md lists notes in best-practices/local/ (seam F) ----------
def _compile_map(files: dict) -> str:
    """Write each `{path under wiki/: text}` into a minimal temp wiki, run wiki-map-compile's `process` over it and
    return the _MAP.md it wrote with the date lines that change with the day left out."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("wiki_map_compile", ROOT / "scripts" / "wiki-map-compile.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory() as t:
        wiki = Path(t) / "demo" / "wiki"
        wiki.mkdir(parents=True)
        for rel, text in files.items():
            p = wiki / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        mod.process(wiki, "demo")
        text = (wiki / "_MAP.md").read_text(encoding="utf-8")
    return "\n".join(ln for ln in text.splitlines() if not ln.startswith(("date:", "last_reviewed:", "review_after:")))


def _folder_block(map_text: str, folder: str) -> list:
    """The lines of the `### [`<folder>/`]` section of a map, or [] when it has none."""
    block, inside = [], False
    for ln in map_text.splitlines():
        if ln.startswith("### "):
            inside = ln.startswith(f"### [`{folder}/`]")
        elif ln.startswith("## "):
            inside = False
        if inside:
            block.append(ln)
    return block


RESEARCH_NOTE = VALID_NOTE.replace("My local note", "Research note")
PROJECT_NOTE = VALID_NOTE.replace("My local note", "Project note")
BASE_WIKI = {"research/active/research-note.md": RESEARCH_NOTE, "project/decisions/project-note.md": PROJECT_NOTE}


def test_map_lists_a_note_in_best_practices_local():
    text = _compile_map({**BASE_WIKI, f"{LOCAL}/my-notes.md": VALID_NOTE})
    block = _folder_block(text, LOCAL)
    check("_MAP.md: a section for best-practices/local/ lists the note as a link to it",
          "- [My local note](./best-practices/local/my-notes.md) _[Tself]_" in block, block)


def test_existing_map_sections_do_not_change_when_best_practices_local_gains_a_note():
    without = _compile_map(BASE_WIKI)
    with_note = _compile_map({**BASE_WIKI, f"{LOCAL}/my-notes.md": VALID_NOTE})
    pairs = [(_folder_block(without, f), _folder_block(with_note, f)) for f in ("research/active", "project/decisions")]
    check("_MAP.md: the research/active/ and project/decisions/ sections are non-empty and the same with and "
          "without a note in best-practices/local/", all(a and a == b for a, b in pairs), pairs)


def test_wiki_with_no_best_practices_folder_compiles_a_map_with_no_best_practices_section():
    text = _compile_map(BASE_WIKI)
    check("_MAP.md: a wiki with no best-practices folder compiles a map that names none and has its two sections",
          "best-practices" not in text and bool(_folder_block(text, "research/active"))
          and bool(_folder_block(text, "project/decisions")), text[-400:])


def test_a_best_practices_local_folder_with_no_titled_note_leaves_the_map_unchanged():
    without = _compile_map(BASE_WIKI)
    no_title = VALID_NOTE.replace('title: "My local note"\n', "")
    untitled = _compile_map({**BASE_WIKI, f"{LOCAL}/scratch.md": NOTE_WITHOUT_FRONTMATTER,
                             f"{LOCAL}/no-title.md": no_title})
    check("_MAP.md: a best-practices/local/ folder holding only notes with no title (no frontmatter, and "
          "frontmatter without a title) compiles the same map as no folder at all",
          "title:" not in no_title and untitled == without, (untitled[-300:], without[-300:]))


def test_the_shipped_local_readme_is_treated_in_the_map_as_a_readme_in_research_is():
    readme = SHIPPED_README.read_text(encoding="utf-8")
    text = _compile_map({"research/active/README.md": readme, f"{LOCAL}/README.md": readme})

    def treatment(folder: str):
        block = _folder_block(text, folder)
        entry = [ln.replace(folder, "<folder>") for ln in block if ln.startswith("- [")]
        purpose = [ln for ln in block[1:] if ln.strip() and not ln.startswith(("Top entries:", "- ["))]
        return bool(block), entry, purpose, bool(purpose) and not purpose[0].startswith("(no purpose set")

    here, there = treatment(LOCAL), treatment("research/active")
    check("_MAP.md: the shipped local README gets a section, a listed entry and a purpose line exactly as the same "
          "README does in research/active/", here == there and here[0] and bool(here[1]) and here[3], (here, there))


def _run(fn):
    """Run one test function; every check it records is named after it, and a crash is a failed check, not the end."""
    first = len(results)
    try:
        fn()
    except Exception as e:  # noqa: BLE001 - a crash is a failed check named after the test, not the end of the file
        check(f"raised {type(e).__name__}: {e}", False)
    results[first:] = [(ok, f"{fn.__name__}: {name}") for ok, name in results[first:]]


for _test in (test_taxonomy_puts_best_practices_local_before_sessions_for_all_nine_pairs,
              test_phase_b_writes_local_readme_with_shipped_bytes_for_stubs,
              test_phase_b_writes_local_readme_with_shipped_bytes_for_empty,
              test_phase_b_writes_local_readme_with_shipped_bytes_for_none,
              test_phase_b_readme_folder_list_has_a_best_practices_local_line,
              test_phase_b_readme_local_line_carries_its_note,
              test_phase_b_summary_lists_best_practices_local_before_sessions,
              test_lint_of_a_fresh_scaffold_draws_no_finding_on_the_local_readme_that_home_does_not,
              test_dry_run_prints_would_lines_for_the_local_folder_with_its_readme,
              test_dry_run_leaves_the_temp_tree_unchanged,
              test_missing_readme_source_stops_the_scaffold_before_any_best_practices_folder,
              test_existing_claude_md_is_kept_byte_for_byte,
              test_first_run_renders_the_three_wiki_scaffold_files,
              test_valid_note_in_best_practices_local_draws_no_lint_finding,
              test_note_without_tags_in_best_practices_local_draws_the_finding_it_draws_elsewhere,
              test_note_without_frontmatter_in_best_practices_local_draws_the_finding_it_draws_elsewhere,
              test_map_lists_a_note_in_best_practices_local,
              test_existing_map_sections_do_not_change_when_best_practices_local_gains_a_note,
              test_wiki_with_no_best_practices_folder_compiles_a_map_with_no_best_practices_section,
              test_a_best_practices_local_folder_with_no_titled_note_leaves_the_map_unchanged,
              test_the_shipped_local_readme_is_treated_in_the_map_as_a_readme_in_research_is):
    _run(_test)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
