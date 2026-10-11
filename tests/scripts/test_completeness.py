#!/usr/bin/env python3
"""Checks for the completeness mark on raws (task #96 step 3). Never shipped. A fetcher that got only part of a
source marks its raw `completeness: preview` (or `summary`); `_entry_checks.raw_completeness` reads the mark, and
the old signs on raws saved before it (a page fetcher's `paywall:` line, the X fetcher's long-post note), and
`wiki-update.py` refuses to file an entry from such a raw unless `--partial-source '<why>'` is given, which writes
`source_completeness:` into the entry. No network.

    uv run python tests/scripts/test_completeness.py    # exit 0 = every check passed
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import _entry_checks as ec  # noqa: E402

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


BODY = "Agents keep state in files so a later run can pick up where the last one stopped.\n"
LEGACY_NOTE = ("> **Note**: this tweet has a `note_tweet` (long-form \"Article\") payload the syndication API does\n"
               "> not expand — the `text` field above may be truncated relative to the full post.\n")


def raw(fm: str, body: str = BODY) -> str:
    return f"---\ntitle: A source\nsource_url: https://example.com/a\n{fm}---\n\n# A source\n\n{body}"


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    nb = td / "vault" / "nb"
    (nb / "wiki" / "research" / "tooling").mkdir(parents=True)
    rawdir = nb / "raw"
    rawdir.mkdir()
    files = {
        "preview": raw("completeness: preview\n"),
        "summary": raw("completeness: summary\n"),
        "full": raw("completeness: full\n"),
        "unmarked": raw(""),
        "paywall": raw('paywall: "suspected paywall or truncated page (40 chars)"\n'),
        "longpost": raw("type: tweet\n", BODY + "\n" + LEGACY_NOTE),
        "odd": raw("completeness: partial\n"),
        "mentions": raw("", BODY + "The syndication API has a `note_tweet` field for long posts.\n"),
    }
    for name, text in files.items():
        (rawdir / f"{name}.md").write_text(text, encoding="utf-8")
    (rawdir / "paper.pdf").write_bytes(b"%PDF-1.4 binary")
    (rawdir / "repo").mkdir()
    (rawdir / "repo" / "README.md").write_text(raw("completeness: preview\n"), encoding="utf-8")

    # ── the reader ──
    rc = ec.raw_completeness
    check("a raw marked preview reads as preview", rc(rawdir / "preview.md") == "preview", rc(rawdir / "preview.md"))
    check("a raw marked summary reads as summary", rc(rawdir / "summary.md") == "summary")
    check("a raw marked full reads as whole (None)", rc(rawdir / "full.md") is None)
    check("an unmarked raw reads as whole (None)", rc(rawdir / "unmarked.md") is None)
    check("an old page-fetcher raw with a paywall: line reads as preview", rc(rawdir / "paywall.md") == "preview")
    check("an old X raw with the long-post note reads as preview", rc(rawdir / "longpost.md") == "preview")
    check("an unknown value is returned as written", rc(rawdir / "odd.md") == "partial", rc(rawdir / "odd.md"))
    check("a PDF raw has no mark (None)", rc(rawdir / "paper.pdf") is None)
    check("a folder raw has no mark (None)", rc(rawdir / "repo") is None)
    check("a missing raw has no mark (None)", rc(rawdir / "nope.md") is None)
    check("an article that mentions note_tweet in its prose is not a long post",
          rc(rawdir / "mentions.md") is None)

    # ── the gate in wiki-update.py ──
    entry = td / "draft.md"
    entry.write_text("## TL;DR\n\nA test entry about state in files.\n\n"
                     "## Related\n\n- [a](a.md)\n- [b](b.md)\n", encoding="utf-8")

    def file(raw_name: str, *extra: str, title: str = "Completeness test entry"):
        p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-update.py"), "--vault", str(td / "vault"),
                            "--topic", "nb", "--folder", "research/tooling", "--source", str(entry),
                            "--source-url", f"https://example.com/{raw_name}", "--raw-path", f"raw/{raw_name}.md",
                            "--title", title, "--tags", "a,b,c", "--tier", "3", "--confidence", "medium",
                            "--no-index", "--skip-integration", *extra],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        return p.returncode, p.stdout + p.stderr

    def entries() -> list[Path]:
        return sorted(p for p in nb.rglob("*.md") if "raw" not in p.parts and p.name != "draft.md")

    code, out = file("preview")
    check("a preview raw is refused (exit 1)", code == 1, (code, out[-300:]))
    check("... saying it holds only a preview, and naming --partial-source",
          "preview" in out and "--partial-source" in out, out[-400:])
    check("... and nothing is written", entries() == [], entries())

    code, out = file("summary")
    check("a summary raw is refused too", code == 1 and "summary" in out, (code, out[-300:]))

    code, out = file("paywall")
    check("an old paywall raw is refused too", code == 1, (code, out[-300:]))

    code, out = file("longpost")
    check("an old long-post raw is refused too", code == 1, (code, out[-300:]))

    code, out = file("odd")
    check("an unknown completeness value is refused, naming the three values",
          code == 1 and "full" in out and "preview" in out and "summary" in out, (code, out[-300:]))
    check("... and nothing is written", entries() == [], entries())

    code, out = file("preview", "--partial-source", "the user asked for the opening only",
                     title="Filed from a preview")
    filed = entries()
    text = filed[0].read_text(encoding="utf-8") if filed else ""
    fm, _ = ec.split_frontmatter(text)
    check("--partial-source files it (exit 0)", code == 0 and len(filed) == 1, (code, out[-300:]))
    check("... with source_completeness: preview in the entry's frontmatter",
          fm.get("source_completeness") == "preview", fm)
    check("... and prints the reason", "the user asked for the opening only" in out, out[-300:])
    for f in filed:
        f.unlink()

    code, out = file("unmarked", title="Filed from a whole raw")
    filed = entries()
    fm, _ = ec.split_frontmatter(filed[0].read_text(encoding="utf-8")) if filed else ({}, "")
    check("an unmarked raw files as before (exit 0)", code == 0 and len(filed) == 1, (code, out[-300:]))
    check("... with no source_completeness field", "source_completeness" not in fm, fm)
    for f in filed:
        f.unlink()

    code, out = file("full", "--partial-source", "not needed", title="Filed from a full raw")
    filed = entries()
    fm, _ = ec.split_frontmatter(filed[0].read_text(encoding="utf-8")) if filed else ({}, "")
    check("--partial-source on a whole raw files it unmarked, and says the flag was not needed",
          code == 0 and "source_completeness" not in fm and "not marked" in out, (code, fm, out[-300:]))
    for f in filed:
        f.unlink()

    code, out = file("summary", "--partial-source", "an abstract is all there is", "--staged",
                     title="Staged from a summary")
    staged = sorted((nb / "_inbox" / "proposed").glob("*.md"))
    fm, _ = ec.split_frontmatter(staged[0].read_text(encoding="utf-8")) if staged else ({}, "")
    check("a staged entry from a summary raw carries source_completeness: summary",
          code == 0 and fm.get("source_completeness") == "summary", (code, fm, out[-300:]))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
