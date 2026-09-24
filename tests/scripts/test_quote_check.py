#!/usr/bin/env python3
"""Checks for the quote check in bootstrap/scripts/_entry_checks.py (check_quotes,
read_raw_text) and its two callers, the wiki-update.py gate and the mechanical
lint. Never shipped.

    python tests/scripts/test_quote_check.py              # exit 0 = every check passed
    python tests/scripts/test_quote_check.py --sabotage   # quote check disabled: must fail

The cases are the shapes agent-builder found in six sonnet-ingested entries
(2026-09-23 ingest-fidelity handoff): an invented phrase, a splice in reverse
order, a reworded quote, a changed name, plus the raw formats a quote must still
match (line-broken auto-captions with fillers, timestamps, HTML entities, VTT,
a notebook's printed output, a folder raw).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "bootstrap" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import _entry_checks as ec  # noqa: E402

if "--sabotage" in sys.argv:
    ec.check_quotes = lambda body, raw_text: []

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool):
    results.append((ok, name))


def warns(body: str, raw: str | None) -> list[str]:
    return [w for w in ec.check_entry_body(body, tags=["a", "b", "c"], raw_text=raw)["warnings"]
            if "quoted fragment" in w]


def kinds(body: str, raw: str | None) -> set[str]:
    out = set()
    for w in warns(body, raw):
        out |= {k for k in ("worded differently", "not found", "out of order") if k in w}
    return out


ARTICLE = ("The harness came late. We shipped a reranker change on a suite we hadn't checkpointed "
           "by budget yet. Candidate B improves recall at the smallest budget and loses 13 points "
           "at the largest. One number would have called that a win or a disaster.")
CAPTIONS = ("And\n\nthen I pass the\n\ntag data set to two\n\njudges.\n\nThe first is Gemma 4 E4B,\n\n"
            "which is about 8B\n\nby judge.\n\nAnd, uh, I want every\n\ndeveloper to start, uh,\n\n"
            "building\n\nvision programs.\n\nYou wo\n\nn't get anywhere from this\n\n.")

# ── clean shapes stay clean ──────────────────────────────────────────────────
check("exact quote with attribution is clean",
      kinds('> "We shipped a reranker change on a suite we hadn\'t checkpointed by budget yet." — the author', ARTICLE) == set())
check("ellipsis splice in source order is clean",
      kinds('> "The harness came late... Candidate B improves recall at the smallest budget"', ARTICLE) == set())
check("[bracketed insertion] splits like an ellipsis",
      kinds('> "improves recall at the smallest budget and loses 13 points at the largest [end-to-end -0.1]."', ARTICLE) == set())
check("curly quotes, case and punctuation ignored",
      kinds("> “one number would have called that a win, or a disaster”", ARTICLE) == set())
check("unmarked `>` line checked whole, attribution dropped",
      kinds("> Candidate B improves recall at the smallest budget — README, Results", ARTICLE) == set())
check("auto-captions: line breaks, fillers, split contraction",
      kinds('> "The first is Gemma 4 E4B, which is about 8B" / "I want every developer to start building vision programs" / "You won\'t get anywhere from this"', CAPTIONS) == set())
check("timestamps inside the raw are ignored",
      kinds('> "there\'s an architecture and an approach that is just fundamentally flawed"',
            "But underneath that, there's 11:39 an architecture and an approach that is [11:42] just fundamentally flawed") == set())
check("HTML entities in the raw are decoded",
      kinds('> "an author who can\'t predict which facts the model will need"',
            "They bloat because an author who can&#x27;t predict which facts the model will need writes") == set())
check("markdown link text in the raw matches plain text",
      kinds('> "see the context engineering guide for the details"',
            "see the [context engineering guide](https://example.com/guide) for the details") == set())
check("short spans (labels) are not checked",
      kinds('> "a reviewer may not be gated" — README, "Departments"', "a reviewer may not be gated, because") == set())
check("Obsidian callout is our note, not a quote",
      kinds("> [!note] This is our own summary of the whole section here", ARTICLE) == set())
check("fenced code is not a quote",
      kinds("```\n> this is a shell prompt line not a quote at all\n```", ARTICLE) == set())
check("no raw text: nothing checked",
      warns('> "an invented sentence that appears in no source anywhere"', None) == [])

# ── the handoff's failure shapes are caught ──────────────────────────────────
check("invented phrase -> not found",
      "not found" in kinds('> "a clean v2/v3 breaking reset of every public package"', ARTICLE))
check("splice in reverse order -> out of order",
      "out of order" in kinds('> "Candidate B improves recall at the smallest budget... We shipped a reranker change on a suite"', ARTICLE))
check("changed name inside a quote -> worded differently",
      "worded differently" in kinds('> "The first is Gemma 3n E4B, which is about 8B"', CAPTIONS))
check("reworded quote -> worded differently",
      "worded differently" in kinds('> "We shipped a reranker change on a suite we had not checkpointed by budget yet."', ARTICLE))
check("warning names the fragment",
      any("Gemma 3n E4B" in w for w in warns('> "The first is Gemma 3n E4B, which is about 8B"', CAPTIONS)))
_r = ec.check_entry_body('## TL;DR\nx\n> "an invented sentence that appears in no source anywhere"', raw_text=ARTICLE)
check("a quote problem is a warning, never an error",
      not any("quoted fragment" in e for e in _r["errors"]) and any("quoted fragment" in w for w in _r["warnings"]))

# ── raw formats ──────────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    vtt = td / "talk.vtt"
    vtt.write_text("WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.000\n<c>we don't build for</c>\n\n2\n"
                   "00:00:03.000 --> 00:00:05.000\nthe model of today\n", encoding="utf-8")
    check("VTT: cue timings and tags dropped",
          kinds('> "we don\'t build for the model of today"', ec.read_raw_text(vtt)) == set())
    nbk = td / "cookbook.ipynb"
    nbk.write_text(json.dumps({"cells": [{"cell_type": "code", "source": ["run(team)\n"],
                                          "outputs": [{"text": ["ANSWER after 9s wall-clock, 4 helper(s) spawned\n"]}]}]}),
                   encoding="utf-8")
    check("ipynb: printed outputs are part of the raw",
          kinds('> "ANSWER after 9s wall-clock, 4 helper(s) spawned"', ec.read_raw_text(nbk)) == set())
    folder = td / "repo"
    (folder / "docs").mkdir(parents=True)
    (folder / "README.md").write_text("A control plane for coding agents.", encoding="utf-8")
    (folder / "docs" / "DESIGN.md").write_text("Raw traces are vendor-specific and schema-unstable.", encoding="utf-8")
    check("folder raw: every text file under it is read",
          kinds('> "Raw traces are vendor-specific and schema-unstable"', ec.read_raw_text(folder)) == set())
    pdf = td / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 binary")
    check("PDF raw: no text, nothing checked", ec.read_raw_text(pdf) is None)

    # ── the callers: the gate files with a warning; the lint reports it ─────
    nbroot = td / "vault" / "nb"
    (nbroot / "wiki" / "research" / "tooling").mkdir(parents=True)
    (nbroot / "raw").mkdir()
    (nbroot / "raw" / "article.md").write_text(ARTICLE, encoding="utf-8")
    entry = td / "draft.md"
    entry.write_text("## TL;DR\n\nA test entry about a reranker story.\n\n"
                     '> "We shipped a reranker change on a suite we had not checkpointed by budget yet."\n\n'
                     "## Related\n\n- [a](a.md)\n- [b](b.md)\n", encoding="utf-8")
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-update.py"), "--vault", str(td / "vault"),
                        "--topic", "nb", "--folder", "research/tooling", "--source", str(entry),
                        "--source-url", "https://example.com/article", "--raw-path", "raw/article.md",
                        "--title", "Quote check test entry", "--tags", "a,b,c", "--tier", "3",
                        "--confidence", "medium", "--no-index", "--skip-integration"],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    out = p.stdout + p.stderr
    check("gate: a misquote files anyway (exit 0)", p.returncode == 0)
    check("gate: prints the quote warning", "worded differently" in out)
    filed = list((nbroot / "wiki" / "research" / "tooling").glob("*.md"))
    check("gate: the entry is written", len(filed) == 1)
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--vault", str(td / "vault"),
                        "--topic", "nb"],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    report = p.stdout
    check("lint: reports the quote warning on the filed entry", "worded differently" in report)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
