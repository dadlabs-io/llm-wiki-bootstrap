"""wiki-promote test suite: sandbox, prompts and checks for run_skill_test.py (task #16, 2026-10-12).

A throwaway registry with one notebook, `skilltest-promote`, copied fresh for each case from
fixtures/seed-notebook/ (the live entries that promoted ones link to and get backlinks from).
Promotion re-indexes the search, so each model gets a qmd index of its own (built in setup;
the real index is never touched).

Each case names, from fixtures/:
- `staged`: a folder in fixtures/staged/ copied into the notebook's _inbox/proposed/ (entries
  and their `<slug>.proposed_metadata.json` sidecars; omit it for empty staging);
- `say`: the user's line; `answers` (optional): what the user answers when the skill asks
  (the session cannot reply, so it is given up front).

The checks read what the session left behind and its tool calls, never its reasoning.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = "skilltest-promote"
ALLOWED_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep",
    "Bash(python:*)", "Bash(python3:*)", "Bash(uv:*)", "Bash(node:*)", "Bash(qmd:*)",
    "Bash(cd:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(grep:*)", "Bash(head:*)", "Bash(tail:*)",
    "Bash(wc:*)", "Bash(find:*)", "Bash(sort:*)", "Bash(echo:*)", "Bash(pwd:*)", "Bash(sed:*)",
    "Bash(mkdir:*)", "Bash(mv:*)", "Bash(rm:*)", "Bash(date:*)",
]


def _rmtree(path: Path) -> None:
    def onexc(func, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass
    if path.exists():
        shutil.rmtree(path, onexc=onexc)


def _qmd() -> list[str]:
    shim = shutil.which("qmd")
    if not shim:
        raise SystemExit("qmd not found on PATH")
    entry = Path(shim).resolve().parent / "node_modules" / "@tobilu" / "qmd" / "dist" / "cli" / "qmd.js"
    node = shutil.which("node")
    return [node, str(entry)] if entry.exists() and node else [shim]


def _qmd_index_file(index: str) -> Path:
    return Path.home() / ".cache" / "qmd" / f"{index}.sqlite"


def prepare_fixtures(repo: Path, refresh: bool = False) -> list[dict]:
    return []  # every entry is written for the test


def setup(model: str, sandbox: Path, repo: Path) -> dict:
    _rmtree(sandbox)
    nb = sandbox / "notebooks" / NOTEBOOK
    shutil.copytree(HERE / "fixtures" / "seed-notebook", nb)
    registry = sandbox / "linked-notebooks.json"
    registry.write_text(json.dumps({"notebooks": {NOTEBOOK: {"root": f"notebooks/{NOTEBOOK}"}}}, indent=2),
                        encoding="utf-8")
    project = sandbox / "project"
    cfg = json.dumps({"tool": "claude-code", "project_name": NOTEBOOK, "notebook": NOTEBOOK, "persona": "main",
                      "registry": registry.as_posix(), "scripts_installed_at": (repo / "scripts").as_posix()}, indent=2)
    for d in (project, sandbox):
        (d / ".claude").mkdir(parents=True, exist_ok=True)
        (d / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")
    index = f"skilltest-promote-{model}-{sandbox.parent.name}"
    _qmd_index_file(index).unlink(missing_ok=True)
    for args in (["collection", "add", str(nb / "wiki")], ["embed"]):
        subprocess.run([*_qmd(), "--index", index, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    return {"sandbox": sandbox, "project": project, "notebook": nb, "registry": registry,
            "skill_dir": sandbox / "skill" / "wiki-promote", "index": index, "scripts": repo / "scripts",
            "env": {"WIKI_QMD_INDEX": index, "PYTHONIOENCODING": "utf-8"}}


def teardown(ctx: dict) -> None:
    _rmtree(ctx["sandbox"])
    _qmd_index_file(ctx["index"]).unlink(missing_ok=True)


def snapshot(ctx: dict) -> dict:
    nb = ctx["notebook"]
    if not nb.exists():
        return {}
    return {p.relative_to(nb).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns) for p in nb.rglob("*") if p.is_file()}


HEADER = """You are running an automated test of the wiki-promote skill. The skill under test is at {skill}/SKILL.md. Read it and follow it exactly, as if the user had said the message below in this project. Do not use any installed copy of any skill.

The notebook is `{notebook}`, this project's notebook, at {nb}. Its search index is named `{index}`: the scripts pick that up by themselves (pass them no `--index`). Run scripts as the skill writes them, `uv run --project <scripts dir> python <path> ...`, with no environment-variable prefix, and write only inside {sandbox}. The user cannot reply while this runs: where the skill says to ask the user something, take the answer given below if there is one; with none given, ask it in your final message and stop there, without acting on an answer you do not have.

{answers}The user said: """


def prompt(case: dict, ctx: dict) -> str:
    nb = ctx["notebook"]
    _rmtree(nb)
    shutil.copytree(HERE / "fixtures" / "seed-notebook", nb)
    proposed = nb / "_inbox" / "proposed"
    if case.get("staged"):
        shutil.copytree(HERE / "fixtures" / "staged" / case["staged"], proposed)
    ctx["before_case"] = snapshot(ctx)
    answers = f"When the skill asks the user, the user answers: {case['answers']}\n\n" if case.get("answers") else ""
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), notebook=NOTEBOOK, nb=nb.as_posix(), index=ctx["index"],
                         sandbox=ctx["sandbox"].as_posix(), answers=answers) + case["say"]


ENTRIES = {  # slug: (title, date, tier, first words of the TL;DR, target_folder)
    "bm25-vs-embeddings-for-agent-memory": ("BM25 versus embeddings for agent memory", "2026-10-02", "2",
                                            "keyword scoring", "research/tooling"),
    "chunk-size-decision-for-notes": ("Chunk size decision for notes", "2026-10-05", "3",
                                      "heading boundaries", "project/decisions"),
    "evicting-stale-agent-memories": ("Evicting stale agent memories", "2026-10-08", "1",
                                      "evict a memory", "project/patterns"),
}
BM25, CHUNK, EVICT = list(ENTRIES)
MONTHS = "oct"


def _lines(text: str) -> list[str]:
    ls = [l.rstrip() for l in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while ls and not ls[-1]:
        ls.pop()
    while ls and not ls[0]:
        ls.pop(0)
    return ls


def _split(text: str):
    """(frontmatter lines, body lines), each trimmed of trailing space and outer blank lines."""
    m = re.match(r"\A\s*---[ \t]*\n(.*?)\n---[ \t]*\n?(.*)\Z", text.replace("\r\n", "\n"), re.S)
    return (_lines(m.group(1)), _lines(m.group(2))) if m else ([], _lines(text))


def _status(line: str) -> bool:
    return bool(re.match(r"""^status:\s*["']?proposed["']?\s*$""", line.strip()))


def _staged_file(case: dict, name: str) -> Path:
    return HERE / "fixtures" / "staged" / case["staged"] / name


def _final(run: dict) -> str:
    return str(run["result"].get("result") or (run["texts"][-1] if run["texts"] else ""))


def _named(text: str, slug: str) -> bool:
    t = text.lower()
    return slug in t or ENTRIES[slug][0].lower() in t


def _says_what_remains(text: str) -> bool:
    """Requirement 7: the report says how many remain in staging. Either the count 1 beside a staging word,
    or the one entry left (chunk-size-decision-for-notes) named as still staged / in staging / remaining.
    A reply that never says what remains fails."""
    unit = r"(?:remain|left|still|staging|staged|waiting|pending|held)"
    num = r"(?:\b1\b|\bone\b)"
    title, _d, _t, _k, _target = ENTRIES[CHUNK]
    ident = (rf"(?:chunk|{re.escape(CHUNK)}|{re.escape(title)}|number 2|#\s?2\b|\bentry 2\b|\bitem 2\b|\bsecond\b|\b2nd\b)")
    gap = r"[^.\n]{0,80}"
    return bool(re.search(rf"{num}{gap}{unit}|{unit}{gap}{num}|{ident}{gap}{unit}|{unit}{gap}{ident}", text, re.I))


def _says_nothing_staged(text: str) -> bool:
    return bool(re.search(r"nothing|empty|\bnone\b|\bzero\b|\bno\b[^.\n]{0,40}(staged|staging|proposed|entr|items?|pending)"
                          r"|\b0\b[^.\n]{0,20}(staged|entr|items?)", text, re.I))


def _date_shown(win: str, date: str) -> bool:
    day = int(date[-2:])
    return date in win or bool(re.search(rf"{MONTHS}[a-z]*\.?\s+0?{day}\b|\b0?{day}\s+{MONTHS}", win, re.I))


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    res: list[dict] = []

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    errs = run.get("error_texts") or {}
    other = [d for d in (r.get("permission_denials") or [])
             if not (isinstance(d, dict) and "read-guard:" in str(errs.get(d.get("tool_use_id"), "")))]
    add("no permission denials (read-guard counted apart)", not other,
        [d.get("tool_name") if isinstance(d, dict) else d for d in other])

    nb = ctx["notebook"]
    bc = ctx["before_case"]
    now = snapshot(ctx)
    new = sorted(set(now) - set(bc))
    changed = sorted(k for k in now if k in bc and now[k] != bc[k])
    gone = sorted(set(bc) - set(now))
    kind = case.get("kind")
    prop, rej = nb / "_inbox" / "proposed", nb / "_inbox" / "rejected"
    text = run["text"]

    def wiki_copies(slug):
        return sorted(p.relative_to(nb).as_posix() for p in (nb / "wiki").rglob(f"{slug}.md"))

    def still_staged(slug):
        md, side = prop / f"{slug}.md", prop / f"{slug}.proposed_metadata.json"
        orig_md, orig_side = _staged_file(case, f"{slug}.md"), _staged_file(case, f"{slug}.proposed_metadata.json")
        add(f"{slug}: still in _inbox/proposed/ with its sidecar", md.is_file() and side.is_file())
        if md.is_file():
            got = [l for l in _lines(md.read_text(encoding="utf-8", errors="replace")) if not _status(l)]
            want = [l for l in _lines(orig_md.read_text(encoding="utf-8")) if not _status(l)]
            add(f"{slug}: staged entry unchanged", got == want)
        if side.is_file():
            add(f"{slug}: sidecar unchanged", side.read_bytes() == orig_side.read_bytes())
        add(f"{slug}: not in the wiki", not wiki_copies(slug), wiki_copies(slug))

    def promoted(slug):
        title, date, tier, key, target = ENTRIES[slug]
        dest = nb / "wiki" / target / f"{slug}.md"
        add(f"{slug}: at wiki/{target}/{slug}.md", dest.is_file())
        add(f"{slug}: entry and sidecar gone from _inbox/proposed/",
            not (prop / f"{slug}.md").exists() and not (prop / f"{slug}.proposed_metadata.json").exists())
        if not dest.is_file():
            return
        got_fm, got_body = _split(dest.read_text(encoding="utf-8", errors="replace"))
        o_fm, o_body = _split(_staged_file(case, f"{slug}.md").read_text(encoding="utf-8"))
        add(f"{slug}: no 'status: proposed' line", not any(_status(l) for l in got_fm))
        add(f"{slug}: frontmatter otherwise kept", all(l in got_fm for l in o_fm if not _status(l)))
        add(f"{slug}: body unchanged (anything the script appends after it is allowed)",
            got_body[:len(o_body)] == o_body)
        side = json.loads(_staged_file(case, f"{slug}.proposed_metadata.json").read_bytes())
        for b in side.get("suggested_backlinks", []):
            p = nb / "wiki" / b["file"]
            if not p.is_file():
                add(f"{slug}: backlink target {b['file']} exists", False)
                continue
            raw = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").split("\n")
            heads = [i for i, l in enumerate(raw) if re.match(r"^\s*#{1,6}\s+\S", l)]
            rel = next((i for i in heads if re.match(r"^\s*#{1,6}\s+related\b", raw[i], re.I)), None)
            footer = next((i for i, l in enumerate(raw) if l.lstrip().startswith("*Source:")), len(raw))
            end = min([footer] + [i for i in heads if rel is not None and i > rel])
            hits = [i for i, l in enumerate(raw) if slug in l]
            add(f"{slug}: backlink sits in the Related section of {b['file']}, above the source footer",
                rel is not None and any(rel < i < end for i in hits), f"related={rel} end={end} hits={hits}")
            add(f"{b['file']}: no 'See also' section", not any(re.search(r"see also", raw[i], re.I) for i in heads))
            seed = (HERE / "fixtures" / "seed-notebook" / "wiki" / b["file"]).read_text(encoding="utf-8")
            kept = [l for l in _lines(seed) if l and l not in [x.rstrip() for x in raw]]
            add(f"{b['file']}: the entry's own lines are all still there", not kept, kept[:2])

    def reported(slug):
        target = ENTRIES[slug][4]
        add(f"report names {slug} and where it went ({target})", _named(text, slug) and target in text)

    if kind in ("pick", "broken"):
        promoted(BM25)
        promoted(EVICT)
        still_staged(CHUNK)
        files = [p.relative_to(nb).as_posix() for p in rej.rglob("*") if p.is_file()] if rej.is_dir() else []
        add("nothing in _inbox/rejected/", not files, files)
        add("the held-back / unpicked entry's slug is not linked from any wiki entry",
            not [p for p in (nb / "wiki").rglob("*.md") if CHUNK in p.read_text(encoding="utf-8", errors="replace")])
        reported(BM25)
        reported(EVICT)
        add("report says what remains in staging (the count 1, or the one entry left named as still staged)",
            _says_what_remains(text), _final(run)[-200:])
        if kind == "broken":
            add("reply names the held-back entry", _named(text, CHUNK))
            add("reply says why (the sidecar / its JSON)",
                bool(re.search(r"sidecar|metadata|json|invalid|malformed|parse|comma", text, re.I)))
        return res

    if kind == "reject":
        dest = rej / f"{CHUNK}.md"
        add("rejected entry is at _inbox/rejected/<slug>.md", dest.is_file())
        if dest.is_file():
            got = [l for l in _lines(dest.read_text(encoding="utf-8", errors="replace")) if not _status(l)]
            want = [l for l in _lines(_staged_file(case, f"{CHUNK}.md").read_text(encoding="utf-8")) if not _status(l)]
            add("rejected entry's content unchanged", got == want)
        add("rejected entry no longer in _inbox/proposed/", not (prop / f"{CHUNK}.md").exists())
        sidecars = sorted(p.relative_to(nb).as_posix() for p in nb.rglob(f"{CHUNK}.proposed_metadata.json"))
        add("rejected entry's sidecar is gone", not sidecars, sidecars)
        for slug in (BM25, EVICT):
            still_staged(slug)
        add("nothing promoted (no staged slug exists under wiki/)", not any(wiki_copies(s) for s in ENTRIES),
            {s: wiki_copies(s) for s in ENTRIES if wiki_copies(s)})
        seeds = ["wiki/research/tooling/qmd-hybrid-search-notes.md",
                 "wiki/project/decisions/use-markdown-notes-as-source-of-truth.md",
                 "wiki/project/patterns/small-entries-one-claim.md"]
        add("the live entries are untouched", not [k for k in seeds if k in changed or k in gone],
            [k for k in seeds if k in changed or k in gone])
        return res

    if kind == "nochoice":
        add("nothing in the notebook moved, changed, added or removed", not (new or changed or gone),
            {"new": new[:3], "changed": changed[:3], "gone": gone[:3]})
        lines = text.replace("\r", "").split("\n")
        for slug, (title, date, tier, key, target) in ENTRIES.items():
            idx = [i for i, l in enumerate(lines) if title.lower() in l.lower() or slug in l.lower()]
            ok = False
            for i in idx:
                win = "\n".join(lines[i:i + 3])
                bare = re.sub(re.escape(date), "", win)
                bare = re.sub(re.escape(title), "", bare, flags=re.I)
                if (_date_shown(win, date)
                        and re.search(rf"(?<![\w.\-/])(?:tier\s*[:=]?\s*|t)?{tier}(?![\w.\-/])", bare, re.I)
                        and key in win.lower()):
                    ok = True
            add(f"listing shows {slug}: title, date, tier and the TL;DR's first words together", ok,
                f"title/slug on {len(idx)} line(s)")
        asks = "?" in text and bool(re.search(r"\ball\b", text, re.I)) and bool(
            re.search(r"pick|number|choose|select|which|specific", text, re.I))
        add("asks whether to promote all or pick (and stops)", asks, _final(run)[-200:])
        return res

    if kind == "empty":
        bad = [k for k in new + changed + gone if k.startswith(("wiki/", "raw/", "_inbox/"))]
        add("nothing under wiki/, raw/ or _inbox/ added, changed or removed", not bad, bad)
        add("says there is nothing in staging", _says_nothing_staged(text), _final(run)[-200:])
        return res

    raise ValueError(f"unknown case kind: {case['id']} ({kind})")
