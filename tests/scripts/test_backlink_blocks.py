#!/usr/bin/env python3
"""Checks for task #240 (lesson #11): the mechanical lint compares every page's BACKLINKS-AUTO block with the links
that really point at it, and wiki-reciprocate-backlinks.py reads links by the same rule. Never shipped.

    uv run python tests/scripts/test_backlink_blocks.py                # every check; exit 0 = all passed
    uv run python tests/scripts/test_backlink_blocks.py test_name ...  # only the named checks

The lint always runs under a stand-in `qmd` (task #133), so an exit code is never red for a missing search index.
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
from _fake_qmd import fake_qmd_env  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def page(title: str, body: str = "") -> str:
    return (f"---\ntitle: \"{title}\"\ndate: 2026-09-01\ntier: 3\nconfidence: high\n"
            f"tags: [x, y, z]\n---\n\n# {title}\n\n{body}\n")


def blk(*targets: str) -> str:
    """A block as wiki-reciprocate-backlinks.py writes it, one line per target as written from the page."""
    lines = ["<!-- BACKLINKS-AUTO START -->", "", "## Backlinks (auto-maintained)", "",
             "_Other entries linking to this one._", ""]
    lines += [f"- [Title]({t})" for t in targets]
    lines += ["", "<!-- BACKLINKS-AUTO END -->"]
    return "\n".join(lines)


def run_lint(pages: dict[str, str]):
    """Write `pages` (wiki-relative path -> text) into a throwaway notebook and lint it: (process, report text, the
    run folder's lint-mechanical.json as a dict)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        nb = tmp / "notebooks" / "t"
        w = nb / "wiki"
        for rel, text in pages.items():
            (w / rel).parent.mkdir(parents=True, exist_ok=True)
            (w / rel).write_text(text, encoding="utf-8")
        (nb / "_inbox" / "reports").mkdir(parents=True)
        (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                                   encoding="utf-8")
        proj = tmp / "project"
        (proj / ".claude").mkdir(parents=True)
        (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
            {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
        run = nb / "_inbox" / "reports" / "r"
        env = fake_qmd_env(tmp / "bin", w, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t",
                            "--cycle-id", "c1", "--run-folder", str(run)],
                           cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)
        report = nb / "_inbox" / "reports" / "lint-report.md"
        text = report.read_text(encoding="utf-8") if report.is_file() else ""
        jp = run / "lint-mechanical.json"
        payload = json.loads(jp.read_text(encoding="utf-8")) if jp.is_file() else {}
    return p, text, payload


def section(text: str, word: str) -> str:
    m = re.search(rf"^## [^\n]*{word}[^\n]*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def entry_for(payload: dict, rel: str):
    """The `backlink_blocks` row for one page, or None."""
    return next((r for r in payload.get("backlink_blocks", []) if r.get("file") == rel), None)


def test_block_listing_a_page_that_does_not_link_here_is_reported_as_extra():
    p, text, payload = run_lint({
        "research/a.md": page("A"),
        "research/b.md": page("B", "\n" + blk("a.md")),
    })
    row = entry_for(payload, "research/b.md")
    check("a block listing a page that does not link here is reported with it as extra",
          row is not None and row["extra"] == ["research/a.md"] and row["missing"] == [], payload.get("backlink_blocks"))
    check("only that page is reported", [r["file"] for r in payload.get("backlink_blocks", [])] == ["research/b.md"],
          payload.get("backlink_blocks"))


def test_linker_left_out_of_a_block_is_reported_as_missing():
    p, text, payload = run_lint({
        "research/a.md": page("A", "[B](b.md)"),
        "research/c.md": page("C", "[B](b.md)"),
        "research/b.md": page("B", "\n" + blk("a.md")),
    })
    row = entry_for(payload, "research/b.md")
    check("a linker the block leaves out is reported as missing",
          row is not None and row["missing"] == ["research/c.md"] and row["extra"] == [], payload.get("backlink_blocks"))


def test_linked_page_with_no_block_is_reported_as_missing():
    p, text, payload = run_lint({
        "research/a.md": page("A", "[B](b.md)"),
        "research/b.md": page("B"),
    })
    row = entry_for(payload, "research/b.md")
    check("a linked page with no block is reported with its linker as missing",
          row is not None and row["missing"] == ["research/a.md"] and row["extra"] == [], payload.get("backlink_blocks"))


def test_matching_block_is_not_reported():
    p, text, payload = run_lint({
        "research/a.md": page("A", "[B](b.md)"),
        "research/b.md": page("B", "\n" + blk("a.md")),
    })
    check("a block that matches the links is not reported", payload.get("backlink_blocks") == [],
          payload.get("backlink_blocks", "key absent"))


def test_a_pages_own_block_does_not_make_it_a_linker():
    p, text, payload = run_lint({
        "research/a.md": page("A", "\n" + blk("b.md")),
        "research/b.md": page("B"),
    })
    check("the block's own lines are not links: b is not missing a, a lists b as extra",
          [(r["file"], r["extra"], r["missing"]) for r in payload.get("backlink_blocks", [])]
          == [("research/a.md", ["research/b.md"], [])], payload.get("backlink_blocks", "key absent"))


def test_summary_line_reads_pages_then_extra_then_missing_counts():
    p, text, payload = run_lint({
        "research/a.md": page("A", "[C](c.md)"),
        "research/b.md": page("B", "\n" + blk("d.md")),
        "research/c.md": page("C"),
        "research/d.md": page("D"),
    })
    check("the top of the report counts pages, extra and missing",
          "**Backlink blocks out of step**: 2 page(s) (extra 1, missing 1)" in text, text[:1500])


def test_json_summary_carries_the_out_of_step_page_count():
    p, text, payload = run_lint({
        "research/a.md": page("A", "[C](c.md)"),
        "research/b.md": page("B", "\n" + blk("d.md")),
        "research/c.md": page("C"),
        "research/d.md": page("D"),
    })
    check("the cycle JSON's summary has backlink_blocks_out_of_step",
          payload.get("summary", {}).get("backlink_blocks_out_of_step") == 2, payload.get("summary"))


def test_json_array_rows_have_file_extra_missing_unclosed_by_file():
    p, text, payload = run_lint({
        "research/a.md": page("A", "[C](c.md)"),
        "research/b.md": page("B", "\n" + blk("d.md")),
        "research/c.md": page("C"),
        "research/d.md": page("D"),
    })
    check("backlink_blocks lists each page with file, extra, missing and unclosed, by file",
          payload.get("backlink_blocks") == [
              {"file": "research/b.md", "extra": ["research/d.md"], "missing": [], "unclosed": False},
              {"file": "research/c.md", "extra": [], "missing": ["research/a.md"], "unclosed": False}],
          payload.get("backlink_blocks", "key absent"))


def test_report_section_names_each_out_of_step_page_with_its_pages():
    p, text, payload = run_lint({
        "research/a.md": page("A", "[C](c.md)"),
        "research/b.md": page("B", "\n" + blk("d.md")),
        "research/c.md": page("C"),
        "research/d.md": page("D"),
    })
    s = section(text, "Backlink Blocks Out of Step")
    check("the section names b with extra d and c with missing a",
          "`research/b.md` — extra `research/d.md`" in s and "`research/c.md` — missing `research/a.md`" in s, s)


CONTROL = {  # one page whose block lists a page that does not link there: the only row a clean case may report
    "research/ctl.md": page("Control", "\n" + blk("ctl-x.md")),
    "research/ctl-x.md": page("Control X"),
}


def reported(payload: dict):
    """The files of the `backlink_blocks` rows, or a note that the key is absent."""
    return [r["file"] for r in payload["backlink_blocks"]] if "backlink_blocks" in payload else "key absent"


def b_missing(pages: dict[str, str]):
    """Lint `pages` and return what the check says page b is missing (None: b is not reported)."""
    p, text, payload = run_lint(pages)
    row = entry_for(payload, "research/b.md")
    return None if row is None else row["missing"]


def test_link_to_a_section_of_a_page_counts_as_a_link():
    got = b_missing({"research/a.md": page("A", "[B](b.md#part)"), "research/b.md": page("B")})
    check("a link to b.md#part makes a a linker of b", got == ["research/a.md"], got)


def test_link_text_holding_brackets_counts_as_a_link():
    got = b_missing({"research/a.md": page("A", "[T [historical] x](b.md)"), "research/b.md": page("B")})
    check("a link whose text holds brackets makes a a linker of b", got == ["research/a.md"], got)


def test_link_with_empty_text_counts_as_a_link():
    got = b_missing({"research/a.md": page("A", "[](b.md)"), "research/b.md": page("B")})
    check("a link with empty text makes a a linker of b", got == ["research/a.md"], got)


def test_link_inside_inline_code_does_not_count():
    got = b_missing({"research/a.md": page("A", "write `[B](b.md)` to link"),
                     "research/c.md": page("C", "[B](b.md)"), "research/b.md": page("B")})
    check("only c, not the page that quotes the link in backticks, is a linker of b", got == ["research/c.md"], got)


def test_link_inside_a_backtick_fence_does_not_count():
    got = b_missing({"research/a.md": page("A", "```\n[B](b.md)\n```"),
                     "research/c.md": page("C", "[B](b.md)"), "research/b.md": page("B")})
    check("only c, not the page with the link in a ``` fence, is a linker of b", got == ["research/c.md"], got)


def test_link_inside_a_tilde_fence_does_not_count():
    got = b_missing({"research/a.md": page("A", "~~~\n[B](b.md)\n~~~"),
                     "research/c.md": page("C", "[B](b.md)"), "research/b.md": page("B")})
    check("only c, not the page with the link in a ~~~ fence, is a linker of b", got == ["research/c.md"], got)


def test_link_after_an_unclosed_fence_does_not_count():
    got = b_missing({"research/a.md": page("A", "```\nnever closed\n[B](b.md)"),
                     "research/c.md": page("C", "[B](b.md)"), "research/b.md": page("B")})
    check("only c, not the page whose fence runs to the end, is a linker of b", got == ["research/c.md"], got)


def test_self_link_does_not_count():
    p, text, payload = run_lint({**CONTROL, "research/b.md": page("B", "[me](b.md)\n\n" + blk("c.md")),
                                 "research/c.md": page("C", "[B](b.md)")})
    check("b linking itself leaves b out of the report; the control is still reported",
          reported(payload) == ["research/ctl.md"], reported(payload))


def test_link_target_with_whitespace_does_not_count():
    p, text, payload = run_lint({**CONTROL, "research/my page.md": page("Spaced"),
                                 "research/a.md": page("A", "[X](my page.md)")})
    check("a target with a space makes no linker: the spaced page is not reported",
          reported(payload) == ["research/ctl.md"], reported(payload))


def test_link_to_an_index_page_does_not_count():
    p, text, payload = run_lint({**CONTROL, "research/_INDEX.md": "# Index\n",
                                 "research/a.md": page("A", "[I](_INDEX.md)")})
    check("_INDEX.md is no entry: it is not reported", reported(payload) == ["research/ctl.md"], reported(payload))


def test_link_to_a_sessions_page_does_not_count():
    p, text, payload = run_lint({**CONTROL, "sessions/s.md": page("Session"),
                                 "research/a.md": page("A", "[S](../sessions/s.md)")})
    check("a sessions/ page is no entry: it is not reported", reported(payload) == ["research/ctl.md"], reported(payload))


def test_link_from_a_sessions_page_does_not_count():
    got = b_missing({"sessions/s.md": page("Session", "[B](../research/b.md)"),
                     "research/c.md": page("C", "[B](b.md)"), "research/b.md": page("B")})
    check("only c, not the sessions/ page, is a linker of b", got == ["research/c.md"], got)


def test_link_to_a_task_card_does_not_count():
    p, text, payload = run_lint({**CONTROL, "tasks/t1.md": page("Card"),
                                 "research/a.md": page("A", "[T](../tasks/t1.md)")})
    check("a tasks/ card is no entry: it is not reported", reported(payload) == ["research/ctl.md"], reported(payload))


def test_link_to_a_dot_file_does_not_count():
    p, text, payload = run_lint({**CONTROL, "research/.hidden.md": page("Hidden"),
                                 "research/a.md": page("A", "[H](.hidden.md)")})
    check("a dot-file is no entry: it is not reported", reported(payload) == ["research/ctl.md"], reported(payload))


def test_link_to_an_inbox_page_does_not_count():
    p, text, payload = run_lint({**CONTROL, "_inbox/x.md": page("Staged"),
                                 "research/a.md": page("A", "[X](../_inbox/x.md)")})
    check("an _inbox/ page is no entry: it is not reported", reported(payload) == ["research/ctl.md"], reported(payload))


UNCLOSED = "<!-- BACKLINKS-AUTO START -->\n\n## Backlinks (auto-maintained)\n\n- [A](a.md)\n"   # a START, never an END


def test_block_with_a_start_marker_lacking_its_end_is_marked_unclosed():
    p, text, payload = run_lint({"research/a.md": page("A", "[B](b.md)"), "research/b.md": page("B", "\n" + UNCLOSED)})
    check("b is reported unclosed, with nothing extra or missing judged",
          payload.get("backlink_blocks") == [
              {"file": "research/b.md", "extra": [], "missing": [], "unclosed": True}],
          payload.get("backlink_blocks", "key absent"))


def test_block_with_a_start_marker_lacking_its_end_is_named_in_the_report():
    p, text, payload = run_lint({"research/a.md": page("A", "[B](b.md)"), "research/b.md": page("B", "\n" + UNCLOSED)})
    s = section(text, "Backlink Blocks Out of Step")
    check("the section lists b as block not closed", "research/b.md" in s and "block not closed" in s, s)


def test_unclosed_block_counts_as_one_page_in_the_summary_line():
    p, text, payload = run_lint({"research/a.md": page("A", "[B](b.md)"), "research/b.md": page("B", "\n" + UNCLOSED)})
    check("the top of the report counts it as a page, extra 0, missing 0",
          "**Backlink blocks out of step**: 1 page(s) (extra 0, missing 0)" in text, text[:1500])


def test_lint_exits_zero_with_blocks_out_of_step():
    p, text, payload = run_lint({**CONTROL, "research/a.md": page("A", "[B](b.md)"),
                                 "research/b.md": page("B", "\n" + UNCLOSED)})
    check("two pages out of step and the lint still exits 0", p.returncode == 0 and len(payload.get("backlink_blocks", [])) == 2,
          (p.returncode, p.stderr[-300:], payload.get("backlink_blocks", "key absent")))


def test_marker_quoted_in_inline_code_is_neither_a_block_nor_unclosed():
    p, text, payload = run_lint({
        "research/a.md": page("A", "A block opens with `<!-- BACKLINKS-AUTO START -->` on its own line.\n\n[B](b.md)"),
        "research/b.md": page("B")})
    check("a is no unclosed page and still a linker: b is missing a, and only b is reported",
          payload.get("backlink_blocks") == [
              {"file": "research/b.md", "extra": [], "missing": ["research/a.md"], "unclosed": False}],
          payload.get("backlink_blocks", "key absent"))


def rebuild_then_lint(pages: dict[str, str]):
    """Write `pages`, run wiki-reciprocate-backlinks.py once, then the lint: (the rebuild's process, every page's text
    afterwards by wiki-relative path, the lint's lint-mechanical.json as a dict)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        nb = tmp / "notebooks" / "t"
        w = nb / "wiki"
        for rel, text in pages.items():
            (w / rel).parent.mkdir(parents=True, exist_ok=True)
            (w / rel).write_text(text, encoding="utf-8")
        (nb / "_inbox" / "reports").mkdir(parents=True)
        (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                                   encoding="utf-8")
        proj = tmp / "project"
        (proj / ".claude").mkdir(parents=True)
        (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
            {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
        env = fake_qmd_env(tmp / "bin", w, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        rebuild = subprocess.run([sys.executable, str(SCRIPTS / "wiki-reciprocate-backlinks.py"), "--topic", "t"],
                                 cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)
        texts = {rel: (w / rel).read_text(encoding="utf-8") for rel in pages}
        run = nb / "_inbox" / "reports" / "r"
        subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t",
                        "--cycle-id", "c1", "--run-folder", str(run)],
                       cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)
        jp = run / "lint-mechanical.json"
        payload = json.loads(jp.read_text(encoding="utf-8")) if jp.is_file() else {}
    return rebuild, texts, payload


def test_rebuild_lists_the_linker_of_a_section_link():
    r, texts, payload = rebuild_then_lint({"research/a.md": page("A", "[B](b.md#part)"), "research/b.md": page("B")})
    check("b's block lists a", "- [A](../research/a.md)" in texts["research/b.md"], (r.stderr[-300:], texts["research/b.md"][-300:]))


def test_rebuild_lists_the_linker_of_a_link_text_holding_brackets():
    r, texts, payload = rebuild_then_lint({"research/a.md": page("A", "[T [historical] x](b.md)"), "research/b.md": page("B")})
    check("b's block lists a", "- [A](../research/a.md)" in texts["research/b.md"], (r.stderr[-300:], texts["research/b.md"][-300:]))


def test_rebuild_lists_the_linker_of_a_link_with_empty_text():
    r, texts, payload = rebuild_then_lint({"research/a.md": page("A", "[](b.md)"), "research/b.md": page("B")})
    check("b's block lists a", "- [A](../research/a.md)" in texts["research/b.md"], (r.stderr[-300:], texts["research/b.md"][-300:]))


def test_rebuild_ignores_a_link_inside_inline_code():
    r, texts, payload = rebuild_then_lint({"research/a.md": page("A", "write `[B](b.md)` to link\n\n[C](c.md)"),
                                           "research/b.md": page("B"), "research/c.md": page("C")})
    check("c gets its block (the rebuild ran) and b gets none",
          "BACKLINKS-AUTO START" in texts["research/c.md"] and "BACKLINKS-AUTO" not in texts["research/b.md"],
          (r.stderr[-300:], texts["research/b.md"][-300:]))


def test_rebuild_ignores_a_link_inside_a_backtick_fence():
    r, texts, payload = rebuild_then_lint({"research/a.md": page("A", "```\n[B](b.md)\n```\n\n[C](c.md)"),
                                           "research/b.md": page("B"), "research/c.md": page("C")})
    check("c gets its block (the rebuild ran) and b gets none",
          "BACKLINKS-AUTO START" in texts["research/c.md"] and "BACKLINKS-AUTO" not in texts["research/b.md"],
          (r.stderr[-300:], texts["research/b.md"][-300:]))


def test_rebuild_ignores_a_link_inside_a_tilde_fence():
    r, texts, payload = rebuild_then_lint({"research/a.md": page("A", "~~~\n[B](b.md)\n~~~\n\n[C](c.md)"),
                                           "research/b.md": page("B"), "research/c.md": page("C")})
    check("c gets its block (the rebuild ran) and b gets none",
          "BACKLINKS-AUTO START" in texts["research/c.md"] and "BACKLINKS-AUTO" not in texts["research/b.md"],
          (r.stderr[-300:], texts["research/b.md"][-300:]))


def test_rebuild_writes_no_block_into_a_page_under_inbox():
    r, texts, payload = rebuild_then_lint({"research/a.md": page("A", "[X](../_inbox/x.md)\n\n[B](b.md)"),
                                           "_inbox/x.md": page("Staged"), "research/b.md": page("B")})
    check("b gets its block (the rebuild ran) and the staged page is left as written",
          "BACKLINKS-AUTO START" in texts["research/b.md"] and texts["_inbox/x.md"] == page("Staged"),
          (r.stderr[-300:], texts["_inbox/x.md"][-300:]))


def test_rebuild_takes_no_linker_from_a_page_under_inbox():
    r, texts, payload = rebuild_then_lint({"_inbox/x.md": page("Staged", "[B](../research/b.md)"),
                                           "research/a.md": page("A", "[C](c.md)"),
                                           "research/b.md": page("B"), "research/c.md": page("C")})
    check("c gets its block (the rebuild ran) and b gets none",
          "BACKLINKS-AUTO START" in texts["research/c.md"] and "BACKLINKS-AUTO" not in texts["research/b.md"],
          (r.stderr[-300:], texts["research/b.md"][-300:]))


def test_lint_lists_nothing_after_one_rebuild():
    r, texts, payload = rebuild_then_lint({
        "research/a.md": page("A", "[B](b.md#part) and [T [historical] x](c.md) and [](d.md) and [D](d.md)"),
        "research/b.md": page("B"), "research/c.md": page("C"), "research/d.md": page("D")})
    check("the lint finds no block out of step after one rebuild, and the summary says 0",
          payload.get("backlink_blocks") == [] and payload.get("summary", {}).get("backlink_blocks_out_of_step") == 0,
          (payload.get("backlink_blocks", "key absent"), r.stderr[-300:]))


def test_unclosed_block_page_stays_listed_after_one_rebuild():
    r, texts, payload = rebuild_then_lint({"research/a.md": page("A", "[B](b.md)"),
                                           "research/b.md": page("B", "\n" + UNCLOSED)})
    check("only b, as unclosed, is listed after one rebuild",
          payload.get("backlink_blocks") == [{"file": "research/b.md", "extra": [], "missing": [], "unclosed": True}],
          (payload.get("backlink_blocks", "key absent"), r.stderr[-300:]))


GOLDEN_BLOCK = ("<!-- BACKLINKS-AUTO START -->\n\n## Backlinks (auto-maintained)\n\n"
                "_Other entries linking to this one. Managed by `wiki-reciprocate-backlinks.py`; "
                "do not hand-edit within the BACKLINKS-AUTO markers._\n\n"
                "- [A](../research/a.md)\n- [C](../project/c.md)\n\n<!-- BACKLINKS-AUTO END -->")


def test_block_text_is_byte_identical_to_the_golden_for_ordinary_links():
    r, texts, payload = rebuild_then_lint({"research/a.md": page("A", "[B](b.md)"),
                                           "project/c.md": page("C", "[B](../research/b.md)"),
                                           "research/b.md": page("B")})
    check("b is its own text, a blank line, the golden block and a newline",
          texts["research/b.md"] == page("B") + "\n" + GOLDEN_BLOCK + "\n", texts["research/b.md"][-600:])


def run_all(selected: list[str]) -> int:
    tests = [(n, f) for n, f in sorted(globals().items(), key=lambda kv: kv[0]) if n.startswith("test_") and callable(f)]
    names = {n for n, _ in tests}
    unknown = [s for s in selected if s not in names]
    if unknown:
        print("unknown check(s): " + ", ".join(unknown))
        return 2
    for n, f in tests:
        if not selected or n in selected:
            first = len(results)
            f()
            results[first:] = [(ok, f"{n}: {name}") for ok, name in results[first:]]   # the runner names the test
    sys.stdout.reconfigure(encoding="utf-8")
    failed = [n for ok, n in results if not ok]
    for ok, n in results:
        print(("PASS " if ok else "FAIL ") + n)
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run_all(sys.argv[1:]))
