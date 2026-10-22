#!/usr/bin/env python3
"""
Fetch a whole GitHub repository's prose as one verbatim raw under <topic>/raw/. Sibling to
wiki-fetch-pdf.py and wiki-fetch-page.py: fetch verbatim -> save to raw/ -> the caller writes the
curated entry on top.

A bare repo URL handed to `wiki-update.py --fetch-only` gets the README alone. When the whole repo is
the source (a skills pack, a tool's docs), this fetcher clones it at its current commit and writes the
README first, then every prose file (Markdown, reStructuredText, plain text: the docs, each SKILL.md,
the changelog) under `## File: <path>`, so every quote can be checked against the raw. Code, binaries,
vendored and build folders, and other languages' copies of the docs are left out. The header records
the commit and the file list, so a later snapshot can be filed with `--revises`.

Task #107 (improver pass 2026-10-12-mixed P4): the Chubby Skills ingest (task #95, 2026-10-11) and
the MarkItDown one (2026-10-05) each built this raw by hand.

Usage:
    wiki-fetch-repo.py --topic <topic> --url https://github.com/<owner>/<repo> --ingested-by claude-code
    [--max-kb 1500]     # refuse a bigger raw (exit 4) and list the files by size; 0 = no cap
Exit: 0 saved; 2 bad input (not a repo URL, no notebook); 3 git clone failed; 4 over --max-kb.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402
from _wiki_config import default_vault as _default_vault, resolve_vault_topic as _resolve_vault_topic  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_URL_RE = re.compile(r"^https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+?)(?:\.git)?/?(?:[#?].*)?$")
NOT_REPOS = {"orgs", "settings", "marketplace", "topics", "trending", "explore", "notifications", "sponsors"}
PROSE_SUFFIXES = {".md", ".mdx", ".markdown", ".rst", ".adoc"}  # not .txt: requirements and constraints files
# vendored, build and CI folders, and test fixtures (microsoft/markitdown's real fetch, 2026-10-12, carried six
# expected-output files from tests/test_files/)
SKIP_DIRS = {".git", ".github", "node_modules", "vendor", "third_party", "third-party", "dist", "build",
             "site-packages", ".venv", "venv", "__pycache__", ".tox", ".next", "target",
             "test", "tests", "testdata", "test_files", "fixtures", "__snapshots__"}
# boilerplate every repo carries, which says nothing about this one
SKIP_NAMES = {"license.md", "code_of_conduct.md", "security.md", "support.md", "thirdpartynotices.md",
              "third_party_notices.md", "notice.md", "pull_request_template.md"}
# a path segment or README suffix naming another language's copy (zh, zh-CN, ja, pt-BR, ...); English stays
LOCALE = r"(?:zh|ja|ko|fr|de|es|pt|ru|it|vi|tr|ar|id|th|pl|uk|nl|fa|he|hi|cs|sv|da|fi|no|hu|ro|el|bn)(?:[-_][A-Za-z]{2,4})?"
LOCALE_DIR_RE = re.compile(rf"^{LOCALE}$", re.I)
LOCALE_FILE_RE = re.compile(rf"[._-]{LOCALE}\.[A-Za-z]+$", re.I)


def slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:max_len].rstrip("-") or "repo"


def unique_path(target: Path) -> Path:
    if not target.exists():
        return target
    n = 2
    while True:
        cand = target.with_name(f"{target.stem}-{n}{target.suffix}")
        if not cand.exists():
            return cand
        n += 1


def prose_files(paths: list[str]) -> list[Path]:
    """The repo's prose files, the root README first, then the rest by path."""
    picked = []
    for path in paths:
        rel = p = Path(path)
        dirs = rel.parts[:-1]
        if any(d in SKIP_DIRS or LOCALE_DIR_RE.match(d) for d in dirs):
            continue
        if p.suffix.lower() not in PROSE_SUFFIXES or p.name.lower() in SKIP_NAMES:
            continue
        if LOCALE_FILE_RE.search(p.name):
            continue
        picked.append(rel)
    readme = [r for r in picked if len(r.parts) == 1 and r.name.lower().startswith("readme")]
    rest = sorted((r for r in picked if r not in readme), key=lambda r: r.as_posix().lower())
    return sorted(readme, key=lambda r: r.name.lower()) + rest


def git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def fetch_repo(vault_root, topic, url, ingested_by, max_kb, clone_from=None) -> int:
    m = REPO_URL_RE.match(url.strip())
    if not m or m.group(1) in NOT_REPOS:
        print(f"ERROR: not a GitHub repository URL: {url} (expected https://github.com/<owner>/<repo>)",
              file=sys.stderr)
        return 2
    owner, name = m.group(1), m.group(2)
    topic_root = Path(vault_root) / topic
    if not topic_root.is_dir():
        print(f"ERROR: topic '{topic}' not found at {topic_root}", file=sys.stderr)
        return 2
    raw_dir = topic_root / "raw"

    with tempfile.TemporaryDirectory(prefix="wiki-fetch-repo-") as td:
        dest = Path(td) / name
        src = clone_from or f"https://github.com/{owner}/{name}.git"
        print(f"  Cloning: {src} (current commit only)")
        # no checkout: every file is read from git's objects, so a path Windows reserves (CON, AUX, NUL) cannot fail
        # the clone there (kadoa-org/congress-trading-monitor's public/data/ticker/CON.json, 2026-10-22)
        c = git("clone", "--depth", "1", "--no-checkout", "--quiet", str(src), str(dest))
        if c.returncode != 0:
            print(f"ERROR: git clone failed: {c.stderr.strip()[-400:]}", file=sys.stderr)
            return 3
        commit = git("rev-parse", "HEAD", cwd=dest).stdout.strip()
        branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=dest).stdout.strip()
        listed = git("-c", "core.quotePath=false", "ls-tree", "-r", "--name-only", "HEAD", cwd=dest)
        if listed.returncode != 0:
            print(f"ERROR: git ls-tree failed: {listed.stderr.strip()[-400:]}", file=sys.stderr)
            return 3
        files = prose_files(listed.stdout.splitlines())
        if not files:
            print("ERROR: the repository has no prose files (no README, docs or SKILL.md)", file=sys.stderr)
            return 2
        texts = []
        for f in files:
            shown = subprocess.run(["git", "show", f"HEAD:{f.as_posix()}"], cwd=dest, capture_output=True)
            if shown.returncode != 0:
                print(f"ERROR: git show failed for {f.as_posix()}: "
                      f"{shown.stderr.decode('utf-8', 'replace').strip()[-300:]}", file=sys.stderr)
                return 3
            texts.append((f, shown.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n").rstrip()))

    size_kb = sum(len(t.encode("utf-8")) for _, t in texts) / 1024
    if max_kb and size_kb > max_kb:
        print(f"Refusing: the prose comes to {size_kb:,.0f} KB, over --max-kb {max_kb:g}. Files by size:",
              file=sys.stderr)
        for f, t in sorted(texts, key=lambda x: -len(x[1])):
            print(f"  {len(t.encode('utf-8')) / 1024:8.1f} KB  {f.as_posix()}", file=sys.stderr)
        print("Raise --max-kb (0 = no cap) if the whole repo is the source, or fetch the files that matter.",
              file=sys.stderr)
        return 4

    now = datetime.now().astimezone()
    title = f"{owner}/{name}"
    fm = ["---", f'title: "{title}"', f"source_url: {url.strip()}", "type: github-repo", f"repo: {title}",
          f"commit: {commit}", f"branch: {branch}", f"files: {len(texts)}",
          f"fetched: {now.isoformat(timespec='seconds')}", f"ingested_by: {ingested_by}", "---", ""]
    body = [f"# {title} at {commit[:12]}", "",
            f"**Source**: <{url.strip()}> · **Commit**: `{commit}` · **Files**: {len(texts)} ({size_kb:,.0f} KB)", "",
            "Files, in the order below:", ""]
    body += [f"- `{f.as_posix()}`" for f, _ in texts]
    for f, t in texts:
        body += ["", f"## File: {f.as_posix()}", "", t]
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = unique_path(raw_dir / f"{now.strftime('%Y-%m-%d')}-{slugify(owner + '-' + name)}-repo.md")
    atomic_write_text(raw_path, "\n".join(fm + body) + "\n")
    print(f"Saved raw: {raw_path} ({len(texts)} files, {size_kb:,.0f} KB, commit {commit[:12]})")
    print()
    print(f"raw_path={raw_path}")
    print(f"source_url={url.strip()}")
    print(f"suggested_title={title}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch a whole GitHub repo's prose into one raw under raw/")
    ap.add_argument("--topic", required=True, help="Topic (notebook) name")
    ap.add_argument("--url", required=True, help="https://github.com/<owner>/<repo>")
    ap.add_argument("--vault", default=None, help=f"Vault root (default: {_default_vault()})")
    ap.add_argument("--ingested-by", default="cli", help="Who initiated this fetch")
    ap.add_argument("--max-kb", type=float, default=1500, help="Refuse a raw bigger than this (0 = no cap)")
    ap.add_argument("--clone-from", default=None, help=argparse.SUPPRESS)  # tests: a local repo plays GitHub
    args = ap.parse_args()
    args.vault, args.topic = _resolve_vault_topic(args.topic, args.vault)
    return fetch_repo(args.vault, args.topic, args.url, args.ingested_by, args.max_kb, args.clone_from)


if __name__ == "__main__":
    sys.exit(main())
