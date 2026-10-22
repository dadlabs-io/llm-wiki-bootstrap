#!/usr/bin/env python3
"""Checks for task #107 (improver pass 2026-10-12-mixed P4): wiki-fetch-repo.py saves a whole GitHub repo's
prose as one raw.

    uv run python tests/scripts/test_fetch_repo.py    # exit 0 = every check passed

Before: a bare repo URL fetched only the README, so a whole-repo read (Chubby Skills, task #95; MarkItDown,
2026-10-05) appended the docs and every SKILL.md to the raw by hand. Now the fetcher clones the repo at its
current commit and writes the README, then every prose file under `## File: <path>`, with the commit and the
file list in the header; code, vendored folders and other languages' copies are left out. A local git repo
plays GitHub (`--clone-from`), so no check touches the network.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


FILES = {
    "README.md": "# Demo skills\n\nA pack of agent skills for testing.\n",
    "README.zh-CN.md": "# 演示技能\n",
    "docs/guide.md": "# Guide\n\nInstall the pack, then run the first skill.\n",
    "docs/zh/guide.md": "# 指南\n",
    "skills/summarise/SKILL.md": "---\nname: summarise\n---\n\nSummarise a document in five lines.\n",
    "CHANGELOG.md": "## 1.0\n\nFirst release.\n",
    "src/app.py": "print('code is not prose')\n",
    "node_modules/dep/README.md": "# vendored\n",
    "assets/logo.png": "not really a png",
    # noise seen in microsoft/markitdown's real fetch (2026-10-12): test fixtures, CI files, boilerplate
    "tests/test_files/expected_outputs/receipt.md": "# RECEIPT\n",
    ".github/constraints.txt": "pip==24\n",
    "CODE_OF_CONDUCT.md": "# Code of conduct\n",
    "SECURITY.md": "# Security\n",
    "requirements-dev.txt": "pytest\n",
}

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    repo = td / "demo-skills"
    for rel, text in FILES.items():
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")

    def git(*a):
        return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, encoding="utf-8")

    git("init", "-q")
    git("-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init")
    commit = git("rev-parse", "HEAD").stdout.strip()

    vault = td / "vault"
    (vault / "nb" / "wiki").mkdir(parents=True)
    url = "https://github.com/example/demo-skills"
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-fetch-repo.py"), "--vault", str(vault), "--topic", "nb",
                        "--url", url, "--clone-from", str(repo), "--ingested-by", "test"],
                       capture_output=True, text=True, encoding="utf-8", timeout=180)
    out = p.stdout + p.stderr
    check("exit 0", p.returncode == 0, out[-500:])
    raws = sorted((vault / "nb" / "raw").glob("*.md")) if (vault / "nb" / "raw").is_dir() else []
    check("one raw written", len(raws) == 1, [r.name for r in raws])
    text = raws[0].read_text(encoding="utf-8") if raws else ""
    check("prints raw_path=", f"raw_path={raws[0]}" in p.stdout if raws else False, p.stdout[-300:])
    check("source_url is the repo URL", f"source_url: {url}\n" in text, text[:400])
    check("the commit is recorded", f"commit: {commit}" in text, text[:400])
    check("type github-repo", "type: github-repo" in text, text[:400])
    for rel in ("README.md", "docs/guide.md", "skills/summarise/SKILL.md", "CHANGELOG.md"):
        check(f"{rel} is in, under its File heading, with its text",
              f"## File: {rel}\n" in text and FILES[rel].strip().splitlines()[-1] in text, rel)
    for rel in ("README.zh-CN.md", "docs/zh/guide.md", "src/app.py", "node_modules/dep/README.md", "assets/logo.png",
                "tests/test_files/expected_outputs/receipt.md", ".github/constraints.txt", "CODE_OF_CONDUCT.md",
                "SECURITY.md", "requirements-dev.txt"):
        check(f"{rel} is left out", f"## File: {rel}" not in text, rel)
    check("the README comes first", text.find("## File: README.md") < text.find("## File: docs/guide.md"), "")
    check("the raw names the repo in its file name", bool(raws) and "demo-skills" in raws[0].name, [r.name for r in raws])

    # A cap keeps a huge repo from becoming one unreadable raw
    p2 = subprocess.run([sys.executable, str(SCRIPTS / "wiki-fetch-repo.py"), "--vault", str(vault), "--topic", "nb",
                         "--url", url, "--clone-from", str(repo), "--max-kb", "0.1"],
                        capture_output=True, text=True, encoding="utf-8", timeout=180)
    check("over --max-kb: exit 4, nothing new written, the file sizes listed",
          p2.returncode == 4 and len(list((vault / "nb" / "raw").glob("*.md"))) == 1 and "docs/guide.md" in p2.stdout + p2.stderr,
          (p2.returncode, (p2.stdout + p2.stderr)[-300:]))

    # A path Windows reserves (CON, AUX, NUL) fails git's checkout there, so the clone "fails" though git has every
    # file (kadoa-org/congress-trading-monitor's public/data/ticker/CON.json, investment-agent, 2026-10-22). The blobs
    # go in through git plumbing, since Windows cannot create such a file on disk.
    def blob(text):
        return subprocess.run(["git", "-C", str(repo), "hash-object", "-w", "--stdin"], input=text, capture_output=True,
                              text=True, encoding="utf-8").stdout.strip()
    ntfs = ("-c", "core.protectNTFS=false")   # Git for Windows refuses such a path in its own index otherwise
    git(*ntfs, "update-index", "--add", "--cacheinfo", f"100644,{blob('{}')},public/data/ticker/CON.json")
    git(*ntfs, "update-index", "--add", "--cacheinfo",
        f"100644,{blob('# Aux notes' + chr(10) + chr(10) + 'Read from git.' + chr(10))},docs/AUX.md")
    git(*ntfs, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "reserved names")
    check("the fixture commit holds both reserved paths",
          {"public/data/ticker/CON.json", "docs/AUX.md"} <= set(git("ls-tree", "-r", "--name-only", "HEAD").stdout.split()),
          git("ls-tree", "-r", "--name-only", "HEAD").stdout)
    p4 = subprocess.run([sys.executable, str(SCRIPTS / "wiki-fetch-repo.py"), "--vault", str(vault), "--topic", "nb",
                         "--url", url, "--clone-from", str(repo), "--ingested-by", "test"],
                        capture_output=True, text=True, encoding="utf-8", timeout=180)
    new = sorted(set((vault / "nb" / "raw").glob("*.md")) - set(raws))
    text4 = new[0].read_text(encoding="utf-8") if new else ""
    check("a repo with a Windows-reserved path (CON) still saves (exit 0)", p4.returncode == 0 and len(new) == 1,
          (p4.returncode, (p4.stdout + p4.stderr)[-300:]))
    check("... with the prose file whose name Windows reserves (docs/AUX.md) and the README",
          "## File: docs/AUX.md\n" in text4 and "Read from git." in text4 and "## File: README.md\n" in text4, text4[:300])

    # Not a GitHub repo URL
    p3 = subprocess.run([sys.executable, str(SCRIPTS / "wiki-fetch-repo.py"), "--vault", str(vault), "--topic", "nb",
                         "--url", "https://example.com/not-a-repo"], capture_output=True, text=True, encoding="utf-8",
                        timeout=60)
    check("a URL that is not a GitHub repo: exit 2", p3.returncode == 2, (p3.returncode, (p3.stdout + p3.stderr)[-200:]))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
