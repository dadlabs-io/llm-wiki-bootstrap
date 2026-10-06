#!/usr/bin/env python3
"""A PDF the user saved by hand attaches to the ticket that was waiting for it (task #81 P7). Never shipped.

    python tests/scripts/test_attach_pdfs.py    # exit 0 = every check passed

A page no fetcher can get is left in its intake bucket as "save as PDF"; Mark saves it from Chrome. On
2026-10-05 he saved 28 PDFs into intake/llm-wiki/ and a one-off script matched each to its ticket by title
words, converted it and set the ticket's raw_path (two needed hand fixes: an X thread whose ticket title
shared one word with the PDF's name, and an article with no PDF). The Drive route had the same gap: a
PDF saved to Drive was queued as a new ticket under its Drive link, so the article's URL was lost and the
item was queued twice. Both routes now go through one matcher: each PDF to its best waiting ticket (title
and URL words, a word only that ticket has counts), converted, attached as raw_path, the source URL kept;
an unmatched or ambiguous PDF is listed, never guessed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _samples import tiny_pdf  # noqa: E402

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def ticket(source: str, title: str, raw: str | None = None) -> str:
    return (f"---\nsource: {source}\ntitle: {title}\nadded_by: drive-fetch\npriority: 3\n"
            + (f"raw_path: {raw}\n" if raw else "") + "---\n\nsave as PDF: paywall\n")


def front(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    head = text.split("---")[1] if text.startswith("---") else ""
    return {k.strip(): v.strip() for k, _, v in (l.partition(":") for l in head.splitlines()) if v}


def setup(tmp: Path) -> tuple[Path, Path]:
    vault = tmp / "vault"
    nb = vault / "nb"
    (nb / "wiki").mkdir(parents=True)
    (nb / "raw").mkdir()
    intake = nb / "_inbox" / "intake"
    for b in ("llm-wiki", "agent-builder", "main"):
        (intake / b).mkdir(parents=True)
    (nb / "_inbox" / "pending").mkdir(parents=True)
    (intake / "llm-wiki" / "harness.md").write_text(
        ticket("https://medium.com/@someone/the-harness-is-the-product-4f2a9c", "The Harness Is the Product"),
        encoding="utf-8")
    (intake / "agent-builder" / "beam.md").write_text(
        ticket("https://x.com/beamnxw/status/1975550000000000000", "Post by beamnxw on X"), encoding="utf-8")
    (intake / "main" / "plugins.md").write_text(
        ticket("https://medium.com/@dev/9-claude-code-plugins-you-should-know-77aa", "9 Claude Code Plugins"),
        encoding="utf-8")
    (intake / "main" / "plugins-too.md").write_text(
        ticket("https://medium.com/@dev/9-claude-code-plugins-you-should-know-part-two-88bb", "9 Claude Code Plugins"),
        encoding="utf-8")
    (nb / "_inbox" / "pending" / "done-already.md").write_text(
        ticket("https://medium.com/@x/restarting-your-agent-is-not-repairing-it-1", "Restarting Your Agent Is Not Repairing It",
               raw="raw/old.md"), encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"nb": {"root": "vault/nb"}}}), encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "nb", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    return vault, nb


def run_triage(vault: Path, *args: str):
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-triage.py"), "--topic", "nb", "attach-pdfs", *args],
                       cwd=vault.parent / "project", capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return p.returncode, p.stdout + p.stderr


# ── route 1: PDFs saved into an intake folder ────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    vault, nb = setup(tmp)
    saved = nb / "_inbox" / "intake" / "llm-wiki"
    (saved / "The Harness Is the Product _ by Someone _ Medium.pdf").write_bytes(tiny_pdf("The harness is the product."))
    (saved / "(1) beamnxw on X_ thread about agents.pdf").write_bytes(tiny_pdf("A thread about agents."))
    (saved / "Restarting Your Agent Is Not Repairing It.pdf").write_bytes(tiny_pdf("Restarting is not repairing."))
    (saved / "9 Claude Code Plugins _ Medium.pdf").write_bytes(tiny_pdf("Nine plugins."))
    (saved / "Something else entirely.pdf").write_bytes(tiny_pdf("Unrelated."))

    code, out = run_triage(vault, "--dry-run")
    check("--dry-run: lists the matches, changes nothing",
          code == 0 and "harness.md" in out and "raw_path" not in (saved / "harness.md").read_text(encoding="utf-8")
          and len(list(saved.glob("*.pdf"))) == 5 and not list((nb / "raw").glob("*.md")), (code, out[-500:]))

    code, out = run_triage(vault)
    h = front(saved / "harness.md")
    check("a Medium PDF attaches to its ticket: raw_path set, the article URL kept",
          code == 0 and h.get("raw_path", "").startswith("raw/") and (nb / h.get("raw_path", "x")).is_file()
          and h.get("source") == "https://medium.com/@someone/the-harness-is-the-product-4f2a9c", (code, h, out[-400:]))
    check("... the raw holds the PDF's text", "harness is the product" in
          (nb / h.get("raw_path", "x")).read_text(encoding="utf-8").lower() if h.get("raw_path") else False)
    b = front(nb / "_inbox" / "intake" / "agent-builder" / "beam.md")
    check("an X thread matches on its handle, a word no other ticket has, across buckets",
          b.get("raw_path", "").startswith("raw/"), (b, out[-400:]))
    check("a ticket that already has its raw is never a candidate",
          front(nb / "_inbox" / "pending" / "done-already.md").get("raw_path") == "raw/old.md"
          and "Restarting Your Agent" in out and "unmatched" in out.lower(), out[-500:])
    check("two equally good tickets: the PDF is listed as ambiguous, neither ticket touched",
          "raw_path" not in (nb / "_inbox" / "intake" / "main" / "plugins.md").read_text(encoding="utf-8")
          and "raw_path" not in (nb / "_inbox" / "intake" / "main" / "plugins-too.md").read_text(encoding="utf-8")
          and "ambiguous" in out.lower(), out[-500:])
    check("an unrelated PDF is listed as unmatched and left where it is",
          "Something else entirely" in out and (saved / "Something else entirely.pdf").is_file(), out[-400:])
    check("an attached PDF leaves the bucket (its copy is kept beside the raw)",
          not (saved / "The Harness Is the Product _ by Someone _ Medium.pdf").exists()
          and any(p.suffix == ".pdf" for p in (nb / "raw").iterdir()), sorted(p.name for p in saved.iterdir()))
    code2, out2 = run_triage(vault)
    check("a second run attaches nothing twice", code2 == 0 and "attached: 0" in out2.lower(), out2[-300:])

# ── the matcher alone: one shared common word is never enough (wiki-cycle suite, 2026-10-06: a Drive run attached
# "Agent memory survey.pdf" to "Handoff files between agent sessions", a ticket queued seconds earlier) ──
sys.path.insert(0, str(SCRIPTS))
import _pdf_match as pm  # noqa: E402
with tempfile.TemporaryDirectory() as td:
    nb = Path(td) / "nb"
    (nb / "_inbox" / "intake" / "main").mkdir(parents=True)
    (nb / "_inbox" / "pending").mkdir(parents=True)
    (nb / "_inbox" / "intake" / "main" / "handoff.md").write_text(
        ticket("https://example.org/skilltest/handoff-files-between-agent-sessions", "Handoff files between agent sessions"),
        encoding="utf-8")
    (nb / "_inbox" / "pending" / "fresh.md").write_text(
        ticket("https://example.org/agent-memory-survey", "Agent memory survey"), encoding="utf-8")
    found, missed, _ = pm.match([Path("Agent memory survey.pdf")], pm.waiting_tickets(nb))
    check("one shared word that is not a whole URL segment matches nothing", not found and missed, found)
    check("an untriaged ticket in pending/ is never a candidate (a save-as-PDF ticket waits in an intake bucket)",
          all("pending" not in str(t["path"]) for t in pm.waiting_tickets(nb)), [str(t["path"]) for t in pm.waiting_tickets(nb)])

# ── route 2: a PDF saved to Drive attaches to the waiting ticket, not a second ticket ──
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    vault, nb = setup(tmp)
    scan = tmp / "drive" / "__FOR CLAUDE" / "nb"
    scan.mkdir(parents=True)
    (scan / "The Harness Is the Product _ by Someone _ Medium.pdf").write_bytes(tiny_pdf("The harness is the product."))
    (scan / "Agent memory survey.pdf").write_bytes(tiny_pdf("A survey of agent memory."))
    (scan / "handoff.txt").write_text("https://example.org/skilltest/handoff-files-between-agent-sessions", encoding="utf-8")
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-fetch-drive-folder.py"), "--subfolder", "nb",
                        "--queue-into", "nb", "--queue-vault", str(vault), "--archive-subfolder", "c1",
                        "--out", str(tmp / "run" / "drive-fetch.md")], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300,
                       env={**os.environ, "WIKI_DRIVE_FROM_DIR": str(tmp / "drive"), "PYTHONIOENCODING": "utf-8"})
    check("Drive: the scan exits 0", p.returncode == 0, (p.stderr or p.stdout)[-400:])
    h = front(nb / "_inbox" / "intake" / "llm-wiki" / "harness.md")
    new = [t for t in (nb / "_inbox" / "pending").glob("*.md") if t.name != "done-already.md" and not t.name.startswith("_")]
    check("Drive: the waiting ticket gets the raw, its article URL kept",
          h.get("raw_path", "").startswith("raw/") and h.get("source", "").startswith("https://medium.com/"), h)
    check("Drive: no second ticket is queued for the attached PDF",
          not [t for t in new if "harness" in t.name], [t.name for t in new])
    check("Drive: an unrelated PDF is queued as its own ticket, not attached to the link the same run queued",
          any("agent-memory-survey" in t.name for t in new)
          and "raw_path" not in next((t.read_text(encoding="utf-8") for t in new if "handoff" in t.name), "raw_path"),
          [t.name for t in new])
    check("Drive: the file is archived as handled", (scan / "_completed" / "c1").is_dir()
          and any((scan / "_completed" / "c1").iterdir()), sorted(x.name for x in scan.iterdir()))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
