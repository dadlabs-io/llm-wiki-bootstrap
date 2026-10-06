#!/usr/bin/env python3
"""Duplicate check by a raw's content, not only its URL (task #81 P5). Never shipped.

    python tests/scripts/test_dedup_content.py    # exit 0 = every check passed

Cycle 2026-10-05-02: a Drive copy of a 482-page book already filed from its Amazon URL passed the URL
dedup, and a worker read all 482 pages before noticing. The two PDFs were byte-identical; their text
raws differed only in the fetcher's header. Three layers (Mark, 2026-10-06): an exact copy (size, then
SHA-256) and a near-identical text (85%+ of the new raw's 5-word runs already in an older raw) block
with `duplicate_of=`; a partial overlap (50-85%: the same review reaching us from two sources) warns.
A raw counts only when an entry, filed or staged, cites the other raw.
"""
from __future__ import annotations

import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


rng = random.Random(81)
VOCAB = ("agent harness context memory tool budget review plan step model token cache search index wiki entry "
         "source quote claim test suite worker gate raw fetch page slide image email cycle report promote link "
         "graph vector rerank keyword prompt eval judge fixture baseline drift owner bucket ticket").split()


def prose(n: int) -> str:
    return " ".join(rng.choice(VOCAB) for _ in range(n)) + "."


ARTICLE = "\n\n".join(prose(60) for _ in range(10))      # ~600 words
OTHER = "\n\n".join(prose(60) for _ in range(10))


def raw(url: str, body: str, title: str = "An article") -> str:
    return (f'---\ntitle: "{title}"\nsource_url: {url}\nfetched: 2026-10-06T10:00:00-04:00\n---\n\n'
            f"# {title}\n\n**Source**: <{url}>\n\n---\n\n{body}\n")


def entry(title: str, raw_path: str) -> str:
    return (f'---\ntitle: "{title}"\nsource_url: https://example.com/{title.replace(" ", "-")}\nraw_path: {raw_path}\n'
            f"tier: 3\nconfidence: medium\ntags: [a, b, c]\n---\n\n## TL;DR\n\n{title}.\n\n## Related\n\n"
            "- [x](x.md)\n- [y](y.md)\n")


def run(*args: str):
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-update.py"), "--vault", str(vault), "--topic", "nb", *args],
                       capture_output=True, text=True, encoding="utf-8", timeout=180)
    return p.returncode, p.stdout + p.stderr


with tempfile.TemporaryDirectory() as td:
    vault = Path(td) / "vault"
    nb = vault / "nb"
    rawd = nb / "raw"
    folder = nb / "wiki" / "research" / "tooling"
    proposed = nb / "_inbox" / "proposed"
    for d in (rawd, folder, proposed):
        d.mkdir(parents=True)
    (rawd / "a.md").write_text(raw("https://one.example/a", ARTICLE), encoding="utf-8")
    (folder / "entry-a.md").write_text(entry("Entry A", "raw/a.md"), encoding="utf-8")
    book = bytes(rng.randrange(256) for _ in range(40_000))
    (rawd / "b.pdf").write_bytes(book)
    (rawd / "b.md").write_text(raw("https://amazon.example/book", OTHER, "A book"), encoding="utf-8")
    (proposed / "entry-b.md").write_text(entry("Entry B", "raw/b.md"), encoding="utf-8")
    (rawd / "orphan.md").write_text(raw("https://two.example/o", "\n\n".join(prose(60) for _ in range(6))),
                                    encoding="utf-8")

    # layer 2: the same article from another URL, a different header
    (rawd / "c.md").write_text(raw("https://mirror.example/a", ARTICLE, "Same article, mirrored"), encoding="utf-8")
    code, out = run("--check-duplicate", "raw/c.md")
    check("near-identical text: exit 3 and duplicate_of= names the filed entry",
          code == 3 and "duplicate_of=" in out and "entry-a.md" in out, (code, out[-300:]))

    words = ARTICLE.split()
    for i in range(0, len(words), 60):
        words[i] = "changed"
    (rawd / "c2.md").write_text(raw("https://mirror.example/a2", " ".join(words)), encoding="utf-8")
    code, out = run("--check-duplicate", "raw/c2.md")
    check("a few words off is still a duplicate", code == 3 and "entry-a.md" in out, (code, out[-300:]))

    half = "\n\n".join(ARTICLE.split("\n\n")[:6] + [prose(60) for _ in range(5)])
    (rawd / "d.md").write_text(raw("https://review.example/d", half), encoding="utf-8")
    code, out = run("--check-duplicate", "raw/d.md")
    check("partial overlap: exit 0 with a warning naming the entry",
          code == 0 and "overlap" in out.lower() and "entry-a.md" in out and "duplicate_of=" not in out,
          (code, out[-300:]))

    (rawd / "e.md").write_text(raw("https://new.example/e", "\n\n".join(prose(60) for _ in range(8))),
                               encoding="utf-8")
    code, out = run("--check-duplicate", "raw/e.md")
    check("different content: exit 0, no duplicate, no warning",
          code == 0 and "duplicate_of=" not in out and "overlap" not in out.lower(), (code, out[-300:]))

    # layer 1: a byte-identical PDF, its entry still staged
    (rawd / "new-book.pdf").write_bytes(book)
    code, out = run("--check-duplicate", "raw/new-book.pdf")
    check("exact copy (PDF): exit 3, duplicate_of= the staged entry citing its twin",
          code == 3 and "entry-b.md" in out, (code, out[-300:]))

    (rawd / "2026-07-01-book2.pdf").write_bytes(book[::-1])
    (rawd / "2026-07-02-2026-07-01-book2.md").write_text(raw("https://amazon.example/b2", prose(80), "Book 2"), encoding="utf-8")
    (folder / "entry-b2.md").write_text(entry("Entry B2", "raw/2026-07-02-2026-07-01-book2.md"), encoding="utf-8")
    (rawd / "2026-10-05-book2.pdf").write_bytes(book[::-1])
    code, out = run("--check-duplicate", "raw/2026-10-05-book2.pdf")
    check("exact copy of a PDF whose entry cites a text raw named after it: still a duplicate",
          code == 3 and "entry-b2.md" in out, (code, out[-300:]))

    (rawd / "o2.md").write_text((rawd / "orphan.md").read_text(encoding="utf-8").replace("two.example", "three.example"),
                                encoding="utf-8")
    code, out = run("--check-duplicate", "raw/o2.md")
    check("a twin no entry cites: not a duplicate (exit 0), but said",
          code == 0 and "duplicate_of=" not in out and "orphan.md" in out, (code, out[-300:]))

    code, out = run("--check-duplicate", "raw/nope.md")
    check("a raw that does not exist: exit 2, saying so", code == 2 and "unrecognized" not in out and "nope.md" in out, (code, out[-200:]))

    # automatic: --fetch-only of a local copy, and filing with --raw-path
    src = Path(td) / "copy-of-a.md"
    src.write_text(raw("https://third.example/a", ARTICLE), encoding="utf-8")
    code, out = run("--fetch-only", "--source", str(src))
    check("--fetch-only reports duplicate_of= right after saving the raw", "duplicate_of=" in out and "entry-a.md" in out,
          (code, out[-300:]))
    summary = Path(td) / "summary.md"
    summary.write_text("## TL;DR\n\nA summary.\n\n## Related\n\n- [x](x.md)\n- [y](y.md)\n", encoding="utf-8")
    before = sorted(p.name for p in folder.iterdir())
    code, out = run("--folder", "research/tooling", "--source", str(summary), "--source-url", "https://mirror.example/a",
                    "--raw-path", "raw/c.md", "--title", "Mirrored", "--tags", "a,b,c", "--tier", "3",
                    "--confidence", "medium", "--no-index", "--skip-integration")
    check("filing a raw that duplicates an entry: Skip (dedup), duplicate_of=, nothing written",
          code == 0 and "Skip (dedup)" in out and "entry-a.md" in out and sorted(p.name for p in folder.iterdir()) == before,
          (code, out[-300:]))
    code, out = run("--folder", "research/tooling", "--source", str(summary), "--source-url", "https://mirror.example/a",
                    "--raw-path", "raw/c.md", "--title", "Mirrored", "--tags", "a,b,c", "--tier", "3",
                    "--confidence", "medium", "--no-index", "--skip-integration", "--force")
    check("--force files it anyway", code == 0 and "wiki_path=" in out, (code, out[-300:]))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
