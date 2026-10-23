#!/usr/bin/env python3
"""Checks for the one shared frontmatter parser, `_entry_checks.split_frontmatter` (task #177 row 1). Never shipped.

    uv run python tests/scripts/test_frontmatter_parser.py    # exit 0 = every check passed

A dozen scripts each parsed frontmatter by hand, and they disagreed: most stripped quotes with
`.strip('"').strip("'")`, which eats every quote at both ends, so a title written with escaped quotes
(`"Acme: \\"Build agents\\""`, as json.dumps writes it) came back as `Acme: \\"Build agents\\` and a value that
merely ended in a quoted word lost its closing quote; triage stripped nothing; the shared one turned an empty
value into a list. One parser now, with YAML's own quoting rules for the cases the wiki writes.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from _entry_checks import split_frontmatter, yaml_scalar  # noqa: E402

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def fm(header: str, body: str = "# Title\n\nBody.\n", nl: str = "\n") -> tuple[dict, str]:
    return split_frontmatter(nl.join(["---", *header.split("\n"), "---", *body.split("\n")]))


d, _ = fm('title: "Acme on Instagram: \\"Build agents\\""')
check("a double-quoted value with escaped quotes decodes exactly", d.get("title") == 'Acme on Instagram: "Build agents"',
      d.get("title"))
d, _ = fm('title: "caf\\u00e9 \\\\ notes"')
check("... \\u escapes and a backslash decode too", d.get("title") == "café \\ notes", d.get("title"))
d, _ = fm("title: 'It''s \"done\"'")
check("a single-quoted value: one pair off, '' is a quote", d.get("title") == 'It\'s "done"', d.get("title"))
d, _ = fm('title: He said "hi"')
check("an unquoted value keeps a quote it ends with", d.get("title") == 'He said "hi"', d.get("title"))
d, _ = fm("title: plain value: with a colon")
check("an unquoted value keeps everything after the first colon", d.get("title") == "plain value: with a colon",
      d.get("title"))
d, _ = fm('tags: [a, "b c", \'d\']')
check("an inline list, each item unquoted", d.get("tags") == ["a", "b c", "d"], d.get("tags"))
d, _ = fm("tags:\n  - a\n  - \"b\"\n- c")
check("a block list, indented or not", d.get("tags") == ["a", "b", "c"], d.get("tags"))
d, _ = fm("review_after:\ntitle: x")
check("an empty value is an empty string, not a list", d.get("review_after") == "" and d.get("title") == "x", d)
d, _ = fm("checker:\n  verdict: fix\ntitle: x")
check("an indented key is never a top-level one", "verdict" not in d and d.get("title") == "x", d)
d, _ = fm("# a comment\ntitle: x")
check("a comment line is skipped", d == {"title": "x"}, d)
d, body = fm('title: "x"\nraw_path: raw/a.md', nl="\r\n")
check("Windows line endings: values carry no \\r", d == {"title": "x", "raw_path": "raw/a.md"}, d)
d, body = fm("title: x", body="# Heading\n\nText.\n")
check("the body starts on the line after the closing ---", body == "# Heading\n\nText.\n", repr(body[:30]))
text = "No frontmatter here.\n---\ntitle: x\n---\n"
d, body = split_frontmatter(text)
check("no frontmatter at the top: {} and the text unchanged", d == {} and body == text, (d, body[:20]))
d, body = split_frontmatter("---\ntitle: x\nno closing line\n")
check("an unclosed block: no frontmatter", d == {}, d)
d, _ = fm("title: x\ntitle: y")
check("a repeated key: the last one wins, as in YAML", d.get("title") == "y", d)
# flat=True: every value a string, for the scripts that read fields as text (the lint, the cycle scope, triage...)
d, _ = split_frontmatter('---\ntags: [a, "b c"]\nrelated:\n  - x\ntitle: "A: \\"B\\""\nempty:\n---\nbody\n', flat=True)
check("flat: an inline list stays its own text", d.get("tags") == '[a, "b c"]', d.get("tags"))
check("flat: a block list's key is an empty string, its items no keys", d.get("related") == ""
      and not any(k.startswith("-") for k in d), d)
check("flat: scalars are decoded as in the default mode", d.get("title") == 'A: "B"' and d.get("empty") == "", d)
check("flat: every value is a string", all(isinstance(v, str) for v in d.values()), d)
check("yaml_scalar: a lone quote character is kept", yaml_scalar('"') == '"', yaml_scalar('"'))
check("yaml_scalar: a broken double-quoted escape falls back to one pair off", yaml_scalar('"a\\q"') == "a\\q",
      yaml_scalar('"a\\q"'))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
