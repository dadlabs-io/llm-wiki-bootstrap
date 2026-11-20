#!/usr/bin/env python3
"""Checks for task #54: a page declares itself standalone. Never shipped.

    python tests/scripts/test_standalone.py    # exit 0 = every check passed

Until 2026-09-24 the mechanical lint listed every page with no inbound link as an
orphan, and the cycle contract called a run clean at `orphans <= 1`, an allowance
for the wiki's HOME page. The user's rule (2026-09-24): one mechanism, no built-in
list. A page whose frontmatter carries `standalone: "<reason>"` is left off the
orphan list and listed apart with its reason; the allowance goes. A `standalone:`
with no reason (blank, `true`, `yes`) is not honoured: the page stays an orphan and
the report says why.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fake_qmd import fake_qmd_env  # noqa: E402  the lint needs an indexed wiki (task #133)

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
FRAMEWORK = ROOT / "framework-docs"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def page(title: str, body: str, extra: str = "") -> str:
    return (f"---\ntitle: \"{title}\"\ndate: 2026-09-01\ntier: self\nconfidence: high\n"
            f"tags: [x, y, z]\n{extra}---\n\n# {title}\n\n{body}\n")


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    try:
        import yaml
        return yaml.safe_load(m.group(1)) or {}
    except ImportError:
        return {k.strip(): v.strip().strip("\"'") for k, _, v in
                (l.partition(":") for l in m.group(1).splitlines() if ":" in l)}


def version(path: Path) -> int:
    return int(frontmatter(path.read_text(encoding="utf-8")).get("framework-version", 0))


# ── the lint ─────────────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    w = nb / "wiki"
    (w / "research").mkdir(parents=True)
    (nb / "_inbox" / "reports").mkdir(parents=True)
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")

    (w / "HOME.md").write_text(page("Home", "- [A](research/a.md)",
                                    'standalone: "the landing page: reading starts here"\n'), encoding="utf-8")
    (w / "research" / "a.md").write_text(page("A", "- [B](b.md)\n- [Linked](linked.md)"), encoding="utf-8")
    (w / "research" / "b.md").write_text(page("B", "- [A](a.md)"), encoding="utf-8")
    (w / "research" / "orphan.md").write_text(page("Orphan", "nothing links here"), encoding="utf-8")
    (w / "research" / "blank.md").write_text(page("Blank", "no reason", 'standalone: ""\n'), encoding="utf-8")
    (w / "research" / "bare-true.md").write_text(page("Bare", "no reason", "standalone: true\n"), encoding="utf-8")
    (w / "research" / "linked.md").write_text(page("Linked", "has a link in", 'standalone: "a hub"\n'),
                                              encoding="utf-8")

    run = nb / "_inbox" / "reports" / "2026-09-24" / "2026-09-24-01"
    env = fake_qmd_env(tmp / "bin", w, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t",
                        "--cycle-id", "2026-09-24-01", "--run-folder", str(run)],
                       cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)
    check("lint exits 0", p.returncode == 0, p.stderr[-300:])
    jp = run / "lint-mechanical.json"
    d = json.loads(jp.read_text(encoding="utf-8")) if jp.is_file() else {}
    orphans = sorted(d.get("orphans") or [])
    check("a page with no inbound link and no `standalone:` is an orphan", "research/orphan.md" in orphans, orphans)
    check("HOME.md with a reason is not an orphan", "HOME.md" not in orphans, orphans)
    check("a blank `standalone:` is not honoured", "research/blank.md" in orphans, orphans)
    check("`standalone: true` (no reason) is not honoured", "research/bare-true.md" in orphans, orphans)
    check("the orphan count is the three", (d.get("summary") or {}).get("orphans") == 3, d.get("summary"))
    sa = d.get("standalone")
    check("JSON lists the standalone pages apart, with the reason",
          sa == [{"file": "HOME.md", "reason": "the landing page: reading starts here"}], sa)
    check("summary counts the standalone pages", (d.get("summary") or {}).get("standalone") == 1, d.get("summary"))
    check("a standalone page that has inbound links is in neither list",
          "research/linked.md" not in orphans and all(s.get("file") != "research/linked.md" for s in sa or []), sa)

    report = (nb / "_inbox" / "reports" / "lint-report.md")
    text = report.read_text(encoding="utf-8") if report.is_file() else ""
    m = re.search(r"^## [^\n]*Standalone[^\n]*$(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
    check("the report has a Standalone section", bool(m), text[:300])
    sec = m.group(1) if m else ""
    check("the section names HOME.md with its reason",
          "HOME.md" in sec and "the landing page: reading starts here" in sec, sec[:300])
    check("the report header counts standalone pages", "**Standalone pages**: 1" in text, text[:600])
    om = re.search(r"^## [^\n]*Orphan[^\n]*$(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
    osec = om.group(1) if om else ""
    check("the orphan section says a reason-less `standalone:` is not honoured",
          bool(re.search(r"blank\.md[^\n]*standalone[^\n]*reason", osec))
          and bool(re.search(r"bare-true\.md[^\n]*standalone[^\n]*reason", osec)),
          osec[:400])
    check("the orphan section tells how to declare a page standalone", "standalone:" in osec, osec[:400])

# ── the docs ─────────────────────────────────────────────────────────────────
csf = FRAMEWORK / "cycle-step-return-format.md"
ctext = csf.read_text(encoding="utf-8")
check("the cycle contract drops the `orphans <= 1` allowance", "orphans <= 1" not in ctext)
check("the cycle contract: a clean run has no orphans",
      "summary.orphans == 0" in ctext, [l for l in ctext.splitlines() if "clean run" in l])
check("the cycle contract names the standalone array", "standalone: [{file, reason}]" in ctext)
check("cycle-step-return-format framework-version bumped to 10 or later", version(csf) >= 10, version(csf))

fm = FRAMEWORK / "wiki-frontmatter-best-practices.md"
ftext = fm.read_text(encoding="utf-8")
check("the frontmatter spec has a `standalone` optional-field row", "| `standalone` |" in ftext)
check("wiki-frontmatter-best-practices framework-version bumped to 20 or later", version(fm) >= 20, version(fm))

for home in (ROOT / "seed" / "wiki" / "HOME.md.tmpl",):
    reason = str(frontmatter(home.read_text(encoding="utf-8")).get("standalone") or "")
    check(f"{home.relative_to(ROOT).as_posix()} declares itself standalone with a reason",
          reason.strip().lower() not in {"", "true", "yes"}, reason)

# ── task #243, step 5: the old toolset framework path is named nowhere ──────
OLD_FRAMEWORK_PATH = "project/best-practices/framework"
OLD_PATH_PARTS = re.compile(r"""["']project["']\)?\s*[/,]\s*["']best-practices["']\)?\s*[/,]\s*["']framework["']""")
OLD_PATH_BACKSLASH = re.compile(r"project\\{1,2}best-practices\\{1,2}framework")
SWEPT_DIRS = ("skills", "agents", "templates", "seed", "wiki-seed", "framework-docs", "scripts")
SWEPT_FILES = ("CLAUDE.md", "INSTALL-INVENTORY.md", "V2_ROADMAP.md")
OLD_COPY_CONSTANT = "TOOLSET_OLD_FRAMEWORK_DOCS"  # the one line that names the old folder: the remove scan reads it


def test_no_shipped_file_names_the_old_toolset_framework_path():
    files = [ROOT / f for f in SWEPT_FILES]
    for d in SWEPT_DIRS:
        files += [p for p in (ROOT / d).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    hits = []
    for p in files:
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if OLD_COPY_CONSTANT in line and OLD_FRAMEWORK_PATH not in line and not OLD_PATH_BACKSLASH.search(line):
                continue
            if OLD_FRAMEWORK_PATH in line or OLD_PATH_PARTS.search(line) or OLD_PATH_BACKSLASH.search(line):
                hits.append(f"{p.relative_to(ROOT).as_posix()}:{n}")
    check("test_no_shipped_file_names_the_old_toolset_framework_path: no shipped file names "
          "project/best-practices/framework, spelled out or built from its parts",
          not hits and all(f.is_file() for f in files[:len(SWEPT_FILES)])
          and all((ROOT / d).is_dir() and any(p.is_file() for p in (ROOT / d).rglob("*")) for d in SWEPT_DIRS),f"{len(hits)} hits: {hits}")


test_no_shipped_file_names_the_old_toolset_framework_path()


# ── task #243, step 9: each framework doc opens with its local-changes line and a practice link ──
# Expected values are typed out, never built with the join or the wording the docs are checked against.
TOOLSET_FRAMEWORK_FOLDER = "notebooks/global-toolset/wiki/best-practices/framework"
STEP9_DOCS = {
    # file name: (expected practice page path from the notebooks root, or None; lowest version)
    "cycle-step-return-format.md": ("notebooks/agentic-design/wiki/research/wiki/wiki-best-practices-authoring.md", 10),
    "memory-signals-sidecar-vs-frontmatter-pattern.md":
        ("notebooks/agentic-design/wiki/research/wiki/wiki-best-practices-context-loading.md", 4),
    "tiered-context-loading.md":
        ("notebooks/agentic-design/wiki/research/wiki/wiki-best-practices-context-loading.md", 4),
    "wiki-authoring-best-practices.md":
        ("notebooks/agentic-design/wiki/research/wiki/wiki-best-practices-authoring.md", 17),
    "wiki-frontmatter-best-practices.md":
        ("notebooks/agentic-design/wiki/research/wiki/wiki-best-practices-frontmatter-and-tiers.md", 20),
    "wiki-search-bucket-rerank-spec.md": (None, 3),
}
LOCAL_LINE = ("Local changes: `best-practices/local/{name}` in the wiki you are working in, then the toolset's "
              "`local/{name}`, hold this install's own changes. Read them after this doc; where they differ, the "
              "wiki's local file wins, then the toolset's, then this doc.")
PRACTICE_LINK = re.compile(r"^Practice page: \[[^\]\n]+\]\((\.\./[^)\s]+\.md)\)$")


def lines_after_frontmatter(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
    return [l for l in (text[m.end():] if m else text).splitlines() if l.strip()]


def test_each_doc_opens_with_a_local_changes_line_naming_its_own_file():
    bad = {}
    for name in STEP9_DOCS:
        first = (lines_after_frontmatter(FRAMEWORK / name) or [""])[0]
        if first != LOCAL_LINE.format(name=name):
            bad[name] = first[:100]
    check("test_each_doc_opens_with_a_local_changes_line_naming_its_own_file: the first line under the frontmatter "
          "is the Local changes line with the doc's own file name",
          not bad and len(STEP9_DOCS) == 6 and len(list(FRAMEWORK.glob("*.md"))) == 6, bad)


def test_each_doc_has_a_practice_page_line_right_after_the_local_changes_line():
    bad = {}
    for name, (page_path, _) in STEP9_DOCS.items():
        body = lines_after_frontmatter(FRAMEWORK / name)
        second = body[1] if len(body) > 1 else ""
        ok = (body[:1] == [LOCAL_LINE.format(name=name)]
              and (second == "Practice page: none" if page_path is None else bool(PRACTICE_LINK.match(second))))
        if not ok:
            bad[name] = second[:120]
    check("test_each_doc_has_a_practice_page_line_right_after_the_local_changes_line: a link line, or exactly "
          "`Practice page: none` for the rerank spec", not bad, bad)


def test_each_practice_link_normalises_to_its_page_path_from_the_toolset_folder():
    import posixpath
    bad = {}
    for name, (page_path, _) in STEP9_DOCS.items():
        if page_path is None:
            continue
        body = lines_after_frontmatter(FRAMEWORK / name)
        m = PRACTICE_LINK.match(body[1]) if len(body) > 1 else None
        landed = posixpath.normpath(posixpath.join(TOOLSET_FRAMEWORK_FOLDER, m.group(1))) if m else None
        if landed != page_path:
            bad[name] = landed
    check("test_each_practice_link_normalises_to_its_page_path_from_the_toolset_folder: joined onto "
          "notebooks/global-toolset/wiki/best-practices/framework, each link lands on its agentic-design page",
          not bad and sum(1 for p, _ in STEP9_DOCS.values() if p) == 5, bad)


def test_the_where_we_stand_link_in_wiki_authoring_normalises_to_its_notebook_path():
    import posixpath
    text = (FRAMEWORK / "wiki-authoring-best-practices.md").read_text(encoding="utf-8")
    links = re.findall(r"\]\((\.\./[^)\s#]*llm-wiki-bootstrap/[^)\s#]+)\)", text)
    landed = [posixpath.normpath(posixpath.join(TOOLSET_FRAMEWORK_FOLDER, l)) for l in links]
    check("test_the_where_we_stand_link_in_wiki_authoring_normalises_to_its_notebook_path: the one link into "
          "llm-wiki-bootstrap lands on notebooks/llm-wiki-bootstrap/wiki/project/best-practices/"
          "wiki-authoring-where-we-stand.md",
          landed == ["notebooks/llm-wiki-bootstrap/wiki/project/best-practices/wiki-authoring-where-we-stand.md"],
          landed)


def test_each_doc_version_is_at_least_the_planned_number():
    bad = {n: version(FRAMEWORK / n) for n, (_, low) in STEP9_DOCS.items() if version(FRAMEWORK / n) < low}
    check("test_each_doc_version_is_at_least_the_planned_number: framework-version is 10, 4, 4, 17, 20 and 3 or "
          "later for the six docs", not bad, bad)


test_each_doc_opens_with_a_local_changes_line_naming_its_own_file()
test_each_doc_has_a_practice_page_line_right_after_the_local_changes_line()
test_each_practice_link_normalises_to_its_page_path_from_the_toolset_folder()
test_the_where_we_stand_link_in_wiki_authoring_normalises_to_its_notebook_path()
test_each_doc_version_is_at_least_the_planned_number()


# ── task #243, step 10: the frontmatter doc's tier rules and three field rows ──
# Expected texts are typed out here, never read back from the doc they check.
VENDOR_POST_RULE = ("An official vendor post with something checkable behind it (code, docs, a public benchmark) "
                    "is tier 2; one that is pitch alone is tier 4.")
REPOSITORY_SENTENCE = ("read at least the README and sanity-check the main code (not all of a big repo); "
                       "if unsure, check size or that the main functions work; else ask the user")
OLD_REPOSITORY_CELL_TEXT = "code read beyond the README"


def rubric_span() -> str:
    """What `wiki-update.py`'s `tier_rubric_text()` returns, from the package's framework-docs/ (the machine config
    points at an empty temp toolset, so the machine's own toolset is never read)."""
    import importlib.util
    with tempfile.TemporaryDirectory() as t:
        vault = Path(t) / "vault"
        (vault / "notebooks").mkdir(parents=True)
        registry = vault / "linked-notebooks.json"
        registry.write_text(json.dumps({"notebooks": {"other": {"root": "notebooks/other"}}}), encoding="utf-8")
        cfg = Path(t) / "wiki-config.json"
        cfg.write_text(json.dumps({"registry": registry.as_posix()}), encoding="utf-8")
        before = os.environ.get("WIKI_GLOBAL_CONFIG")
        os.environ["WIKI_GLOBAL_CONFIG"] = str(cfg)
        try:
            spec = importlib.util.spec_from_file_location("wiki_update_for_rubric", SCRIPTS / "wiki-update.py")
            assert spec is not None and spec.loader is not None
            mod = importlib.util.module_from_spec(spec)
            sys.path.insert(0, str(SCRIPTS))
            spec.loader.exec_module(mod)
            text, _where = mod.tier_rubric_text()
        finally:
            if before is None:
                os.environ.pop("WIKI_GLOBAL_CONFIG", None)
            else:
                os.environ["WIKI_GLOBAL_CONFIG"] = before
    return text or ""


def field_row(field: str) -> str:
    rows = [l for l in ftext.splitlines() if l.startswith(f"| `{field}` |")]
    return rows[0] if len(rows) == 1 else ""


def test_the_rubric_span_holds_the_vendor_post_rule():
    span = " ".join(rubric_span().split())
    check("test_the_rubric_span_holds_the_vendor_post_rule: the span `tier_rubric_text()` returns says an official "
          "vendor post with something checkable is tier 2 and one that is pitch alone is tier 4",
          VENDOR_POST_RULE in span, span[:200])


def test_the_rubric_span_holds_the_repository_sentence():
    span = " ".join(rubric_span().split())
    check("test_the_rubric_span_holds_the_repository_sentence: the span `tier_rubric_text()` returns carries the "
          "repository reading sentence", REPOSITORY_SENTENCE in span, span[:200])


def test_the_rubric_span_lacks_the_old_repository_cell_text():
    span = " ".join(rubric_span().split())
    check("test_the_rubric_span_lacks_the_old_repository_cell_text: the span is non-empty and no longer says "
          "'code read beyond the README'", bool(span) and OLD_REPOSITORY_CELL_TEXT not in span, span[:200])


def test_status_row_says_wiki_promote_strips_proposed():
    row = field_row("status")
    check("test_status_row_says_wiki_promote_strips_proposed: a `status` row names `proposed` and says "
          "`wiki-promote` strips it", "`proposed`" in row and "`wiki-promote` strips the `proposed` line" in row, row[:200])


def test_origin_row_says_the_agent_stamps_it_per_the_claude_md_template():
    row = field_row("origin")
    check("test_origin_row_says_the_agent_stamps_it_per_the_claude_md_template: the `origin` row says the agent "
          "stamps it, following the CLAUDE.md template",
          "The agent stamps it, following the CLAUDE.md template" in row, row[:300])


def test_origin_row_says_no_script_writes_it():
    row = field_row("origin")
    check("test_origin_row_says_no_script_writes_it: the `origin` row says no script writes it",
          "no script writes it" in row, row[:300])


def test_origin_row_still_lists_its_four_values():
    row = field_row("origin")
    check("test_origin_row_still_lists_its_four_values: the `origin` row still lists inline, wrap-up, wiki-update, wiki-cycle",
          all(f"`{v}`" in row for v in ("inline", "wrap-up", "wiki-update", "wiki-cycle")), row[:300])


def test_cycle_id_row_says_nothing_in_the_install_writes_it():
    row = field_row("cycle_id")
    check("test_cycle_id_row_says_nothing_in_the_install_writes_it: a `cycle_id` row says no script, skill, "
          "template or agent writes it into an entry",
          "no script, skill, template or agent in this install writes it into an entry" in row, row[:300])


test_the_rubric_span_holds_the_vendor_post_rule()
test_the_rubric_span_holds_the_repository_sentence()
test_the_rubric_span_lacks_the_old_repository_cell_text()
test_status_row_says_wiki_promote_strips_proposed()
test_origin_row_says_the_agent_stamps_it_per_the_claude_md_template()
test_origin_row_says_no_script_writes_it()
test_origin_row_still_lists_its_four_values()
test_cycle_id_row_says_nothing_in_the_install_writes_it()


# ── task #243, step 12: the CLAUDE.md template's precedence entry says where a project's own changes go ──
# The template is rendered the way the scaffold renders it: `new-wiki.py --phase B` into a temp target, under a
# temporary home so the machine's own config, registry and toolset are never read or written. Expected texts are
# typed out here, never read back from the template they check.
_RENDERED: list[str] = []


def rendered_claude_md() -> str:
    if _RENDERED:
        return _RENDERED[0]
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        home = tmp / "home"
        (home / ".claude").mkdir(parents=True)
        vault = tmp / "vault"
        (vault / "notebooks").mkdir(parents=True)
        registry = vault / "linked-notebooks.json"
        registry.write_text(json.dumps({"notebooks": {}}), encoding="utf-8")
        target = tmp / "work" / "demo"
        target.mkdir(parents=True)
        cfg = tmp / "wiki-config.json"
        cfg.write_text(json.dumps({"registry": registry.as_posix()}), encoding="utf-8")
        env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "GIT_CONFIG_NOSYSTEM": "1",
               "PYTHONIOENCODING": "utf-8", "WIKI_GLOBAL_CONFIG": str(cfg), "WIKI_TOOLING_STATE": "installed"}
        subprocess.run([sys.executable, str(SCRIPTS / "new-wiki.py"), "--phase", "B", "--target-folder", str(target),
                        "--project-name", "demo", "--project-description", "Wiki for demo",
                        "--project-folder", "stubs", "--research-folder", "stubs",
                        "--vault-root", str(vault / "notebooks"), "--registry", str(registry),
                        "--bootstrap-source", str(ROOT), "--drive-enabled", "no", "--skills-install", "global"],
                       capture_output=True, text=True, encoding="utf-8", env=env)
        out = target / "CLAUDE.md"
        _RENDERED.append(out.read_text(encoding="utf-8") if out.is_file() else "")
    return _RENDERED[0]


def precedence_framework_entry() -> str:
    lines = [l for l in rendered_claude_md().splitlines() if l.startswith("1. **Framework-contract docs**")]
    return lines[0] if len(lines) == 1 else ""


def test_precedence_entry_names_the_local_folder_path_for_a_doc():
    entry = precedence_framework_entry()
    check("test_precedence_entry_names_the_local_folder_path_for_a_doc: the rendered precedence entry for the "
          "framework-contract docs names `wiki/best-practices/local/<doc name>`",
          "`wiki/best-practices/local/<doc name>`" in entry, entry[:300])


def test_precedence_entry_says_to_read_the_local_file_after_the_framework_doc():
    entry = precedence_framework_entry()
    check("test_precedence_entry_says_to_read_the_local_file_after_the_framework_doc: the entry says to read the "
          "local file after the framework doc",
          "`wiki/best-practices/local/<doc name>`, never in the doc; read it after the framework doc" in entry,
          entry[:300])


def test_precedence_entry_points_to_the_local_changes_line():
    entry = precedence_framework_entry()
    check("test_precedence_entry_points_to_the_local_changes_line: the entry points to the doc's \"Local changes\" "
          "line for the order",
          "(the doc's \"Local changes\" line says in what order)" in entry, entry[:300])


def test_rendered_template_lacks_the_old_toolset_framework_path():
    text = rendered_claude_md()
    check("test_rendered_template_lacks_the_old_toolset_framework_path: the rendered CLAUDE.md is non-empty and "
          "has no `project/best-practices/framework`",
          bool(text) and OLD_FRAMEWORK_PATH not in text, text[:200])


def test_precedence_entry_does_not_copy_the_local_changes_sentence():
    entry = precedence_framework_entry()
    check("test_precedence_entry_does_not_copy_the_local_changes_sentence: the entry exists and carries neither "
          "'where they differ' nor 'local file wins' from the doc line",
          bool(entry) and all(p not in entry for p in
                              ("where they differ", "local file wins", "wiki's local file", "then the toolset's")),
          entry[:300])


test_precedence_entry_names_the_local_folder_path_for_a_doc()
test_precedence_entry_says_to_read_the_local_file_after_the_framework_doc()
test_precedence_entry_points_to_the_local_changes_line()
test_rendered_template_lacks_the_old_toolset_framework_path()
test_precedence_entry_does_not_copy_the_local_changes_sentence()

failed =[n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
