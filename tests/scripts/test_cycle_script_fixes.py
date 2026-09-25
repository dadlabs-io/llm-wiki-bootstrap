#!/usr/bin/env python3
"""Checks for the three /wiki-cycle script fixes of task #42 (findings 1, 8 and 9 of
the 2026-09-23 live cycle). Never shipped.

    python tests/scripts/test_cycle_script_fixes.py    # exit 0 = every check passed

- Finding 1: wiki-fetch-drive-folder.py --out wrote only the Markdown report; the
  cycle's drive-fetch.json was written by hand. --out now writes the JSON beside it.
- Finding 9: wiki-lint-mechanical.py had no --cycle-id / --run-folder, so the cycle's
  lint-mechanical.json was written by hand too.
- Finding 8: wiki-update.py --staged suggested backlinks on one shared generic tag or
  a single word ("vaults", "personal-assistant"); a worker trimmed 5 of 12 by hand.

Drive is never contacted: main() runs with the Drive calls replaced by stubs.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "bootstrap" / "scripts"
sys.path.insert(0, str(SCRIPTS))

results: list[tuple[bool, str]] = []
STEP_FIELDS = ("skill", "cycle_id", "step", "timestamp", "status", "summary",
               "queued", "skipped", "deferred", "notes", "errors")


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def entry(title: str, tags: list[str], body: str) -> str:
    return (f"---\ntitle: \"{title}\"\ndate: 2026-09-01\ntier: 3\nconfidence: medium\n"
            f"tags: [{', '.join(tags)}]\n---\n\n# {title}\n\n{body}\n")


def notebook(tmp: Path) -> Path:
    """A registry notebook `t` with a project folder pointing at it; returns the project."""
    nb = tmp / "notebooks" / "t"
    (nb / "wiki" / "research" / "tooling").mkdir(parents=True)
    (nb / "_inbox" / "reports").mkdir(parents=True)
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    w = nb / "wiki" / "research" / "tooling"
    (w / "a.md").write_text(entry("A", ["x", "y", "z"], "## TL;DR\n\nA.\n\n## Related\n\n- [B](b.md)\n- [gone](missing.md)\n"),
                            encoding="utf-8")
    (w / "b.md").write_text(entry("B", ["x", "y", "z"], "## TL;DR\n\nB.\n\n## Related\n\n- [A](a.md)\n"), encoding="utf-8")
    return proj


# ── finding 9: the mechanical lint writes its cycle step files ───────────────
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    proj = notebook(tmp)
    run = tmp / "notebooks" / "t" / "_inbox" / "reports" / "2026-09-24" / "2026-09-24-01"
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t"],
                       cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)
    check("lint without the flags: exit 0, no run folder written", p.returncode == 0 and not run.exists(),
          p.stderr[-200:])
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t",
                        "--cycle-id", "2026-09-24-01", "--run-folder", str(run)],
                       cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)
    check("lint with --cycle-id/--run-folder: exit 0", p.returncode == 0, p.stderr[-300:])
    jp, mp = run / "lint-mechanical.json", run / "lint-mechanical.md"
    check("lint writes lint-mechanical.json", jp.is_file())
    check("lint writes lint-mechanical.md", mp.is_file())
    d = json.loads(jp.read_text(encoding="utf-8")) if jp.is_file() else {}
    check("lint JSON has every contract field", all(f in d for f in STEP_FIELDS),
          [f for f in STEP_FIELDS if f not in d])
    check("lint JSON names its step and cycle", d.get("step") == "lint-mechanical"
          and d.get("cycle_id") == "2026-09-24-01" and d.get("status") == "completed", d.get("step"))
    s = d.get("summary") or {}
    keys = ("files_scanned", "broken_links", "orphans", "stale_pending", "missing_frontmatter",
            "missing_tier", "invalid_tier", "missing_confidence", "invalid_confidence", "unquoted_yaml")
    check("lint summary carries the contract's counters", all(isinstance(s.get(k), int) for k in keys),
          {k: s.get(k) for k in keys})
    check("lint counts the planted broken link", s.get("broken_links") == 1 and s.get("files_scanned") == 2, s)
    bl = d.get("broken_links") or []
    check("lint lists the broken link as {file, target, link_text}",
          len(bl) == 1 and bl[0].get("target") == "missing.md" and bl[0].get("file", "").endswith("a.md")
          and "link_text" in bl[0], bl)
    check("lint lists orphans as a sibling array", isinstance(d.get("orphans"), list), d.get("orphans"))
    md = mp.read_text(encoding="utf-8") if mp.is_file() else ""
    check("lint .md has the sidecar header and points at the full report",
          "# lint-mechanical — 2026-09-24-01" in md and "**Status**: completed" in md and "lint-report.md" in md, md[:200])

# ── finding 1: the Drive fetch writes drive-fetch.json beside its --out report ──
drive = load("wiki-fetch-drive-folder")
ENTRIES = [{"title": "One", "url": "https://example.com/one", "file": "one.txt", "file_id": "f1", "dup_file_ids": ["f4"]},
           {"title": "Two", "url": "https://example.com/two", "file": "two.txt", "file_id": "f2", "dup_file_ids": []},
           {"title": "Known", "url": "https://example.com/known", "file": "k.txt", "file_id": "f3", "dup_file_ids": []}]
DUPS = [{"file": "one-again.txt", "file_id": "f4", "kept_file": "one.txt", "url": "https://example.com/one"}]
drive.get_drive_service = lambda *a, **k: object()
drive.find_folder_id = lambda service, name, parent_id=None: f"id-{name}"
drive.scan_folder = lambda service, label, folder_id: ([dict(e) for e in ENTRIES], list(DUPS))
drive.wiki_source_url_keys = lambda topic, vault=None: {drive.url_dedup_key("https://example.com/known")}
drive.queue_entries_into_topic = lambda entries, *a: (1, 1, [("f1", "queued", "ok"), ("f2", "error", "boom")])
drive.move_handled_files = lambda *a, **k: (2, 0, [])
drive._write_activity_log = lambda entry: None
with tempfile.TemporaryDirectory() as td:
    out = Path(td) / "2026-09-24-01" / "drive-fetch.md"
    argv = sys.argv
    sys.argv = ["wiki-fetch-drive-folder.py", "--folder-name", "__FOR CLAUDE", "--subfolder", "t",
                "--queue-into", "t", "--move-handled", "--archive-subfolder", "2026-09-24-01", "--out", str(out)]
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rc = drive.main()
    finally:
        sys.argv = argv
    check("drive main exits 0", rc == 0, rc)
    check("drive still prints its one-line JSON summary", '"status": "ok"' in buf.getvalue(), buf.getvalue()[-200:])
    check("drive writes the Markdown report at --out", out.is_file())
    jp = out.with_suffix(".json")
    check("drive writes drive-fetch.json beside it", jp.is_file())
    d = json.loads(jp.read_text(encoding="utf-8")) if jp.is_file() else {}
    check("drive JSON has every contract field", all(f in d for f in STEP_FIELDS), [f for f in STEP_FIELDS if f not in d])
    check("drive JSON: step drive-fetch, cycle id from --archive-subfolder",
          d.get("step") == "drive-fetch" and d.get("cycle_id") == "2026-09-24-01", (d.get("step"), d.get("cycle_id")))
    s = d.get("summary") or {}
    check("drive summary: the contract's counters",
          (s.get("urls_resolved"), s.get("urls_queued"), s.get("urls_deduped")) == (3, 1, 2), s)
    check("drive summary: the scratchpad's counters",
          (s.get("unique_urls"), s.get("queued"), s.get("queue_failed"), s.get("moved"), s.get("move_failed")) == (3, 1, 1, 2, 0), s)
    check("drive queued[] is the queued URL", [q.get("url") for q in d.get("queued", [])] == ["https://example.com/one"],
          d.get("queued"))
    check("drive skipped[] holds the already-in-wiki and the duplicate",
          sorted(q.get("url") for q in d.get("skipped", [])) == ["https://example.com/known", "https://example.com/one"],
          d.get("skipped"))
    check("drive deferred[] holds the failed queue with its reason",
          [(q.get("url"), q.get("reason")) for q in d.get("deferred", [])] == [("https://example.com/two", "boom")],
          d.get("deferred"))

# ── finding 8: no backlink suggested on one shared tag or a single word ──────
upd = load("wiki-update")
with tempfile.TemporaryDirectory() as td:
    w = Path(td) / "wiki"
    f = w / "research" / "tooling"
    f.mkdir(parents=True)
    new = Path(td) / "new-entry.md"
    new.write_text(entry("Obsidian vaults for agent memory", ["obsidian", "vaults", "personal-assistant", "markdown"],
                         "## Related\n\n- [Linked one](linked-one.md)\n"), encoding="utf-8")
    cands = {
        "one-tag.md": (["vaults", "security"], "Password vaults and secret stores."),
        "two-tags.md": (["obsidian", "vaults"], "Notes on vaults kept in Obsidian."),
        "title-phrase.md": (["unrelated"], "A comparison: obsidian vaults for agent memory, reviewed."),
        "linked-one.md": (["unrelated"], "Mentions vaults once."),
        "no-tags.md": ([], "Some personal-assistant bots."),
    }
    inbound = []
    for name, (tags, body) in cands.items():
        (f / name).write_text(entry(name, tags, body) if tags else f"# {name}\n\n{body}\n", encoding="utf-8")
    inbound = upd.find_inbound_candidates(new, w, "Obsidian vaults for agent memory")
    kept = {p.name for p, _t, _s in upd._curate_backlink_candidates(inbound, w, max_n=8, entry_path=new)}
    found = {p.name for p, _t, _s in inbound}
    check("backlinks: the fixture's five candidates are all found as mentions", found == set(cands), sorted(found))
    check("backlinks: one shared tag + a single word is not suggested", "one-tag.md" not in kept, sorted(kept))
    check("backlinks: a single word with no shared tags is not suggested", "no-tags.md" not in kept, sorted(kept))
    check("backlinks: two shared tags are suggested", "two-tags.md" in kept, sorted(kept))
    check("backlinks: a multi-word title match is suggested", "title-phrase.md" in kept, sorted(kept))
    check("backlinks: an entry the new one links to is suggested", "linked-one.md" in kept, sorted(kept))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
