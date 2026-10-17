#!/usr/bin/env python3
"""
read-guard.py — makes "read this document" mean the whole document, by
enforcement rather than by a rule in CLAUDE.md (user, 2026-09-18).

Why: a transcript audit found 45 instruction and resume files (handoff.md,
task.md, SKILL.md, CLAUDE.md, ...) read only partly since 2026-08-20, each
reported as read, although the user's global CLAUDE.md says to read in full.
Public reports say the same of CLAUDE.md rules alone (claude-code #2595, #28743).

One script, three hook events (the tooling install registers it for all three):

  PreToolUse (Read | Bash | PowerShell) — refuses, before it runs:
    - a Read of a document with a `limit` that starts at the top, when the
      whole file fits in one Read (a capped first page of a small file)
    - a shell command that prints part of a document: head / tail / sed -n
      on a document, a document piped into head / tail / sed -n,
      Get-Content -TotalCount / -Head / -Tail / -First, or Get-Content piped
      into Select-Object -First / -Last
    - a shell `cat` / `type` / Get-Content of documents whose combined size
      is over the shell's output cap (the output would come back truncated)
    - a wiki-update.py call that files an entry from a raw (`--raw-path`) the
      session and its helper agents have not read to its last line (task #149,
      2026-10-15: the REA entry was filed from part of a 29,095-line raw)

  Stop and SubagentStop — at the end of every turn, reads the session's own
  transcript: every Read of a document made in this turn is checked against
  the lines the Read tool reported returning (startLine, numLines, totalLines),
  pooled with every other Read of that file in the session, the session's
  helper agents' included (task #150). A document not
  covered from line 1 to its last line blocks the stop with the missing
  ranges, once per turn (stop_hook_active lets the second stop through, so it
  can never loop). This also catches the Read tool's own silent truncation
  (claude-code #28783, #92979).

A "document" is a file with one of DOC_EXTS. Code files are out of scope.
Any error inside the guard allows the action: a guard bug must never stop work.

Usage: Claude Code passes the hook input as JSON on stdin.
  python read-guard.py            # as the hook runs it
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

# `.txt` left out on 2026-09-26: in the first week every `.txt` block was a command's saved
# output (test results, a script's report, Claude Code's saved tool output), never a document
# anyone was asked to read. Folders are not exempt: a scratchpad also holds cloned source
# repositories, whose documents are read whole like any other.
DOC_EXTS = {".md", ".markdown", ".mdx", ".rst", ".adoc", ".org"}
# A Read above this size may need several pages (the Read tool caps one call at
# about 25,000 tokens); a start-capped Read is only allowed above it.
ONE_READ_MAX_BYTES = 60_000
# Claude Code keeps about 30,000 characters of a shell command's output and
# saves the rest to a file behind a short preview. Stay well under it.
SHELL_OUTPUT_MAX_BYTES = 25_000

_PARTIAL_PS = re.compile(r"-(TotalCount|Head|Tail|First|Last)\b", re.I)
_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\s*(?=\n|$)", re.S)
_REDIRECT = re.compile(r"^\d*>>?&?\d*$")
# a redirect that names a file: `>`, `2>>`, `&>` (a separate word, the file follows) or `2>err.txt` (attached);
# `2>&1` names no file
_REDIRECT_TO_FILE = re.compile(r"^(?:\d*|&)>>?(?!&)(.*)$")


def segments(command: str) -> list[tuple[str, bool]]:
    """The command's simple commands, each with whether it reads the previous
    one's output through a pipe. Quote-aware; heredoc bodies are dropped (their
    text is data, not commands)."""
    command = _HEREDOC.sub(lambda m: m.group(0).split("\n", 1)[0], command)
    out, buf, quote, piped, i = [], [], None, False, 0
    while i < len(command):
        c = command[i]
        if quote:
            if c == quote:
                quote = None
            elif c == "\\" and quote == '"' and i + 1 < len(command):
                buf.append(c)
                i += 1
                c = command[i]
            buf.append(c)
        elif c in "'\"":
            quote = c
            buf.append(c)
        elif c == "\\" and i + 1 < len(command):
            buf.append(command[i:i + 2])
            i += 1
        elif c in "|;&\n":
            two = command[i:i + 2]
            if two in ("||", "&&"):
                i += 1
            elif c == "&" and buf and buf[-1] == ">":  # >& redirect, not a separator
                buf.append(c)
                i += 1
                continue
            out.append(("".join(buf).strip(), piped))
            piped = c == "|" and two != "||"
            buf = []
        else:
            buf.append(c)
        i += 1
    out.append(("".join(buf).strip(), piped))
    return [(s, p) for s, p in out if s]


def _operands(words: list[str]) -> list[str]:
    """Words after the command name that are not options or redirect targets."""
    ops, skip = [], False
    for w in words[1:]:
        if skip:
            skip = False
            continue
        if _REDIRECT.match(w) or w in ("<", "<<", "<<<"):
            skip = True
            continue
        if w.startswith((">", "<", "-")):
            continue
        ops.append(w)
    return ops


# The two append-only logs a do-code-change run keeps (2026-09-26, the user's pick): a session
# wants their newest entries, not 48 KB of history each time, so inside `.do-code-change/` they
# are logs, not documents. The run's other files (plan.md, requirements.md, ...) stay documents.
_APPEND_ONLY_LOGS = {"doubt-log.md", "checkpoints.md"}


def is_doc(path: str) -> bool:
    p = path.strip().strip("'\"")
    if Path(p).suffix.lower() not in DOC_EXTS:
        return False
    parts = p.replace("\\", "/").lower().split("/")
    return not (parts[-1] in _APPEND_ONLY_LOGS and ".do-code-change" in parts)


def _resolve(path: str, cwd: str) -> Path:
    p = Path(os.path.expanduser(path.strip().strip("'\"")))
    if not p.is_absolute():
        p = Path(cwd or ".") / p
    return p


def _size(path: str, cwd: str) -> int:
    try:
        return _resolve(path, cwd).stat().st_size
    except OSError:
        return 0


def _words(segment: str) -> list[str]:
    """Quote-aware words; non-POSIX so a Windows path keeps its backslashes."""
    try:
        words = shlex.split(segment, posix=False)
    except ValueError:
        words = segment.split()
    return [w[1:-1] if len(w) > 1 and w[0] == w[-1] and w[0] in "'\"" else w for w in words]


# ---------- PreToolUse ----------

def check_read(tool_input: dict, cwd: str) -> str | None:
    path = str(tool_input.get("file_path") or "")
    if not is_doc(path) or not tool_input.get("limit"):
        return None
    offset = tool_input.get("offset") or 0
    if int(offset) > 1:
        return None  # a continuation page; the end-of-turn check covers completeness
    size = _size(path, cwd)
    if size and size > ONE_READ_MAX_BYTES:
        return None  # too big for one Read: paging is required, the end-of-turn check follows it
    return (f"read-guard: {Path(path).name} is a document and fits in one Read ({size:,} bytes). "
            "Read it whole: call Read again without `limit` or `offset`. When the user asks for a "
            "document to be read, every word is read, first line to last.")


def _outputs(command: str) -> set[str]:
    """Files this command writes: by redirection, or edited in place with `sed -i`. Printing
    part of one is looking at the command's own output or checking its own edit, not reading
    a document — the same reason the end-of-turn check skips a document the session wrote."""
    out: set[str] = set()
    for seg, _ in segments(command):
        words = _words(seg)
        if words and Path(words[0]).name.lower() == "sed" and any(w.startswith("-i") for w in words):
            out.update(w for w in _operands(words) if is_doc(w))
        for i, w in enumerate(words):
            m = _REDIRECT_TO_FILE.match(w)
            if not m:
                continue
            target = m.group(1) or (words[i + 1] if i + 1 < len(words) else "")
            if target:
                out.add(target.strip("'\""))
    return out


_SHELL_VAR = re.compile(r"\$\{?\w+\}?")


def _is_output(path: str, outputs: set[str]) -> bool:
    """`path` is one of the command's outputs; an output path built from a variable
    (`skills/$s/README.md` in a loop) matches any path of its shape."""
    return path in outputs or any(
        "$" in o and re.fullmatch(".*?".join(re.escape(x) for x in _SHELL_VAR.split(o)), path)
        for o in outputs)


def check_shell(command: str, cwd: str) -> str | None:
    docs_so_far: list[str] = []  # documents flowing into this command through a pipe
    cat_docs: list[str] = []
    own_output = _outputs(command)
    for seg, piped in segments(command):
        if not piped:
            docs_so_far = []
        words = _words(seg)
        if not words:
            continue
        cmd = Path(words[0]).name.lower()
        docs = [w for w in _operands(words) if is_doc(w) and not _is_output(w, own_output)]
        partial_unix = cmd in ("head", "tail") or (cmd == "sed" and "-n" in words and "-i" not in words)
        if partial_unix and (docs or docs_so_far):
            names = ", ".join(Path(d).name for d in (docs or docs_so_far))
            return (f"read-guard: `{cmd}` would show only part of {names}. Documents are read whole: "
                    "use the Read tool with no `limit` (it pages a large file; read every page).")
        if cmd in ("get-content", "gc", "type", "cat") and _PARTIAL_PS.search(seg) and docs:
            return (f"read-guard: this Get-Content prints only part of {', '.join(Path(d).name for d in docs)}. "
                    "Use the Read tool with no `limit`.")
        if cmd in ("select-object", "select") and _PARTIAL_PS.search(seg) and docs_so_far:
            return (f"read-guard: Select-Object would keep only part of {', '.join(Path(d).name for d in docs_so_far)}. "
                    "Use the Read tool with no `limit`.")
        if cmd in ("cat", "type", "get-content", "gc", "more", "less"):
            docs_so_far = docs
            cat_docs += docs
        elif docs:
            docs_so_far = []  # grep, wc, cp, ... on a document are not reads of it
    total = sum(_size(d, cwd) for d in cat_docs)
    if total > SHELL_OUTPUT_MAX_BYTES:
        return (f"read-guard: printing {', '.join(Path(d).name for d in cat_docs)} ({total:,} bytes) through "
                "the shell would come back truncated to a preview. Use the Read tool on each document instead.")
    return None


def pre_tool_use(data: dict) -> dict | None:
    tool, tin, cwd = data.get("tool_name"), data.get("tool_input") or {}, data.get("cwd") or ""
    if tool == "Read":
        reason = check_read(tin, cwd)
    elif tool in ("Bash", "PowerShell"):
        command = str(tin.get("command") or "")
        reason = check_shell(command, cwd) or check_filing(
            command, data.get("transcript_path"), data.get("agent_transcript_path"))
    else:
        reason = None
    if not reason:
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


# ---------- Stop / SubagentStop ----------

def _is_prompt(entry: dict) -> bool:
    """A user turn typed (or sent) by the user, not a tool result or meta entry."""
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    return isinstance(content, list) and any(isinstance(x, dict) and x.get("type") == "text" for x in content)


def _entries(transcript: Path) -> list[dict]:
    entries = []
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


class Reads:
    """What a set of transcripts read: each document's line ranges and length, the documents
    written, and the documents printed whole through the shell (`cat`, `type`, Get-Content)."""

    def __init__(self):
        self.ranges: dict[str, list[tuple[int, int]]] = {}
        self.total: dict[str, int] = {}
        self.written: set[str] = set()
        self.printed: set[str] = set()  # file names (lower case; may hold a shell `$var`)
        self.made: set[str] = set()     # file names a shell command wrote or moved into place
        self.requested: set[str] = set()  # file names asked of the Read tool, result recorded or not
        self._asked: dict[str, str] = {}  # Read call id -> document, until its result is seen

    _NUMBERED = re.compile(r"^\s*(\d+)\t", re.M)

    def _numbered(self, key: str, content) -> None:
        """A Read result with no toolUseResult record (a headless session's helper transcripts, 2026-10-15):
        its range is its first and last numbered line; its length the longest known, else the file's on disk."""
        if isinstance(content, list):
            content = "\n".join(str(c.get("text") or "") for c in content if isinstance(c, dict))
        nums = [int(n) for n in self._NUMBERED.findall(str(content or ""))]
        if not nums:
            return
        self.ranges.setdefault(key, []).append((nums[0], nums[-1]))
        if not self.total.get(key):
            try:
                with open(key, encoding="utf-8", errors="replace") as f:
                    self.total[key] = sum(1 for _ in f)
            except OSError:
                self.total[key] = nums[-1]

    def add(self, entries: list[dict], cwd: str = "") -> list[str]:
        """Pools `entries` in; returns the document read by each entry ("" for none), in order."""
        keys = []
        for e in entries:
            msg = e.get("message") or {}
            content = msg.get("content") if isinstance(msg.get("content"), list) else []
            for x in content:
                if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("tool_use_id") in self._asked \
                        and not isinstance(e.get("toolUseResult"), dict):
                    self._numbered(self._asked.pop(x["tool_use_id"]), x.get("content"))
                if not (isinstance(x, dict) and x.get("type") == "tool_use"):
                    continue
                tin = x.get("input") or {}
                if x.get("name") == "Write":
                    self.written.add(os.path.normcase(str(tin.get("file_path") or "")))
                elif x.get("name") == "Read":
                    self.requested.add(_name(str(tin.get("file_path") or "")))
                    if is_doc(str(tin.get("file_path") or "")):
                        self._asked[x.get("id")] = os.path.normcase(str(tin["file_path"]))
                elif x.get("name") in ("Bash", "PowerShell"):
                    command = str(tin.get("command") or "")
                    self.printed.update(_printed_whole(command))
                    self.made.update(_made(command))
            result = e.get("toolUseResult")
            f = result.get("file") if isinstance(result, dict) and result.get("type") == "text" else None
            if not isinstance(f, dict) or not is_doc(str(f.get("filePath") or "")):
                keys.append("")
                continue
            key = os.path.normcase(str(f["filePath"]))
            start, num, tot = int(f.get("startLine") or 1), int(f.get("numLines") or 0), int(f.get("totalLines") or 0)
            self.total[key] = tot or self.total.get(key, 0)
            if num:
                self.ranges.setdefault(key, []).append((start, start + num - 1))
            keys.append(key)
        return keys

    def gaps(self, key: str) -> list[tuple[int, int]]:
        gaps, nxt = [], 1
        for a, b in sorted(self.ranges.get(key, [])):
            if a > nxt:
                gaps.append((nxt, a - 1))
            nxt = max(nxt, b + 1)
        if nxt <= self.total.get(key, 0):
            gaps.append((nxt, self.total[key]))
        return gaps

    def find(self, rel: str) -> list[str]:
        """Read or written documents whose path ends with `rel` (forward slashes, any case)."""
        tail = rel.strip("'\"").replace("\\", "/").lstrip("./").lower()
        seen = set(self.total) | self.written
        return [k for k in seen if (p := k.replace("\\", "/").lower()) == tail or p.endswith("/" + tail)]


def _printed_whole(command: str) -> set[str]:
    """Documents a shell command prints whole: operands of cat / type / Get-Content with no
    partial flag and nothing after them in a pipe that cuts the output."""
    out: set[str] = set()
    segs = segments(command)
    for n, (seg, _) in enumerate(segs):
        words = _words(seg)
        while words and words[0] in ("do", "then", "else", "{", "("):  # a loop or if body
            words = words[1:]
        if not words or Path(words[0]).name.lower() not in ("cat", "type", "get-content", "gc"):
            continue
        if _PARTIAL_PS.search(seg) or (n + 1 < len(segs) and segs[n + 1][1]):
            continue  # a partial flag, or piped on (head, grep, ...): not a whole read
        out.update(_name(w) for w in _operands(words) if is_doc(w))
    return out


def _name(path: str) -> str:
    return path.strip("'\"").replace("\\", "/").rsplit("/", 1)[-1].lower()


_ASSIGN = re.compile(r"^(\w+)=(.+)$")


def _made(command: str) -> set[str]:
    """Names of the documents a shell command writes (a redirect, `sed -i`) or moves or copies into
    place (`mv`, `cp`): a raw the session built or renamed itself. A redirect to a variable set in
    the same command (`OUT=raw/x.md; ... > "$OUT"`) counts as that file."""
    names: dict[str, str] = {}
    out: set[str] = set()
    for seg, _ in segments(command):
        words = _words(seg)
        for w in words:
            m = _ASSIGN.match(w)
            if m:
                names[m.group(1)] = m.group(2).strip("'\"")
        if words and Path(words[0]).name.lower() in ("mv", "cp", "move", "copy", "move-item", "copy-item"):
            ops = _operands(words)
            if ops:
                out.add(_name(ops[-1]))
    for target in _outputs(command):
        resolved = _SHELL_VAR.sub(lambda m: names.get(m.group(0).strip("${}"), m.group(0)), target)
        if is_doc(resolved):
            out.add(_name(resolved))
    return out


def _matches(pattern: str, name: str) -> bool:
    """A file name against a name from a command, where a shell `$var` stands for any text."""
    if "$" not in pattern:
        return pattern == name
    return re.fullmatch(".*?".join(re.escape(x) for x in _SHELL_VAR.split(pattern)), name) is not None


def family(transcript: Path, checked: Path | None = None) -> list[Path]:
    """The session's transcripts other than `checked`: Claude Code keeps a session's subagents
    in <session>/subagents/agent-*.jsonl beside <session>.jsonl (task #150, 2026-10-15)."""
    main = transcript
    if transcript.parent.name == "subagents":  # given a subagent's own transcript
        main = transcript.parent.parent.with_suffix(".jsonl")
    sub = main.with_suffix("") / "subagents"
    found = [main] if main.is_file() else []
    if sub.is_dir():
        found += sorted(sub.glob("agent-*.jsonl"))
    skip = os.path.normcase(str(checked)) if checked else None
    return [p for p in found if os.path.normcase(str(p)) != skip]


# Filing an entry (task #149, 2026-10-15): wiki-update.py with --raw-path files or stages an entry
# from that raw. These flags make a call that files nothing, or one the user allowed to file from
# part of its source.
_NOT_FILING = {"--fetch-only", "--regate", "--check-duplicate", "--slug-for", "--partial-source"}


def _flag(words: list[str], flag: str) -> str | None:
    for i, w in enumerate(words):
        if w == flag and i + 1 < len(words):
            return words[i + 1]
        if w.startswith(flag + "="):
            return w.split("=", 1)[1]
    return None


def _filing(command: str) -> tuple[str, str] | None:
    """(--raw-path, --source-url) of a wiki-update.py call that files an entry, else None."""
    for seg, _ in segments(command):
        words = _words(seg)
        if not any(Path(w).name.lower() == "wiki-update.py" for w in words):
            continue
        if any(w.split("=", 1)[0] in _NOT_FILING for w in words):
            return None
        raw = _flag(words, "--raw-path")
        return (raw, _flag(words, "--source-url") or "") if raw else None
    return None


def _raw_path_of(command: str) -> str | None:
    """The --raw-path of a wiki-update.py call that files an entry, else None."""
    found = _filing(command)
    return found[0] if found else None


def check_filing(command: str, transcript: str | None, agent_transcript: str | None = None) -> str | None:
    """Refuses to file an entry from a raw that this session and its helper agents have not read
    to its last line. The REA ingest (2026-10-14) filed from a 29,095-line raw read in part; the
    full read afterwards found six wrong claims in the entry."""
    found = _filing(command)
    if not found or not is_doc(found[0]) or not transcript or not Path(transcript).is_file():
        return None
    reads = Reads()
    for p in [Path(transcript)] + family(Path(transcript), Path(transcript)) + (
            [Path(agent_transcript)] if agent_transcript and Path(agent_transcript).is_file() else []):
        try:
            reads.add(_entries(p))
        except OSError:
            continue
    return filing_verdict(found[0], reads, found[1])


def _read_whole(rel: str, reads: Reads) -> bool:
    name = _name(rel)
    if any(_matches(p, name) for p in reads.printed | reads.made):
        return True
    keys = reads.find(rel)
    return any(k in reads.written for k in keys) or any(reads.total.get(k) and not reads.gaps(k) for k in keys)


def filing_verdict(raw: str, reads: Reads, source_url: str = "") -> str | None:
    """The refusal for filing from `raw`, given what was read, else None. A local file named as the
    source (`--source-url file://...`, or a path) that was read whole counts: `--fetch-only` copies
    a local file into raw/ under a dated name."""
    name = _name(raw)
    if source_url.strip("'\"").startswith("internal://"):
        return None  # pasted text or the session's own work: the session wrote the raw's text itself
    local = re.sub(r"^file:/*", "", source_url.strip("'\"")) if source_url else ""
    if local and not re.match(r"^\w+://", local) and is_doc(local) and _read_whole(local, reads):
        return None
    # --fetch-only copies a local file into raw/ as <date>-<its name>: the original read whole counts
    undated = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name)
    if undated != name and _read_whole(undated, reads):
        return None
    if any(_matches(p, name) for p in reads.printed | reads.made):
        return None
    keys = reads.find(raw)
    if any(k in reads.written for k in keys):
        return None
    read = [k for k in keys if reads.total.get(k)]
    if not read and name in reads.requested:
        return None  # Read was called but its result left no line counts (some 2026-10-12 helper transcripts): can't tell
    name = Path(raw).name
    if not read:
        return (f"read-guard: wiki-update.py would file an entry from {name}, which this session and its "
                "helper agents have not read. Read the raw to its last line first (Read with no `limit`, every "
                "page; a raw too big for one context is split with wiki-raw-parts.py across helper agents, one per "
                "part, each reading its range whole), then file.")
    gaps = min((reads.gaps(k) for k in read), key=lambda g: sum(b - a + 1 for a, b in g))
    # a lone last line (a trailing blank line the pages stopped short of) is not an unread passage:
    # two of the eleven refusals in the backtest over saved sessions were that alone
    if gaps and gaps[-1][0] == gaps[-1][1] == max(reads.total.get(k, 0) for k in read):
        gaps = gaps[:-1]
    if not gaps:
        return None
    return (f"read-guard: wiki-update.py would file an entry from {name}, but lines "
            f"{', '.join(f'{a}-{b}' for a, b in gaps)} of it were not read by this session or its helper "
            "agents. Read them first (Read with `offset`, every page to the last line, or split them across "
            "helper agents, each reading its range whole), then file. A source filed from part of its raw "
            "goes only on the user's word, with --partial-source.")


def uncovered(transcript: Path, others: list[Path] | None = None) -> dict[str, list[tuple[int, int]]]:
    """{document path: missing line ranges} for documents Read in the current turn of
    `transcript` and not covered start to end across the whole session. Reads in `others`
    (the session's helper agents, task #150) count toward the coverage too; they are loaded
    only when the session's own reads leave a gap."""
    entries = _entries(transcript)
    turn_start = max((i for i, e in enumerate(entries) if _is_prompt(e)), default=0)
    reads = Reads()
    keys = reads.add(entries)
    in_turn = {k for i, k in enumerate(keys) if k and i > turn_start}

    def missing() -> dict[str, list[tuple[int, int]]]:
        out = {}
        for key in in_turn:
            if key in reads.written or not reads.total.get(key):
                continue
            gaps = reads.gaps(key)
            if gaps:
                out[key] = gaps
        return out

    found = missing()
    if found and others:
        for p in others:
            try:
                reads.add(_entries(p))
            except OSError:
                continue
        found = missing()
    return found


def stop(data: dict) -> dict | None:
    if data.get("stop_hook_active"):
        return None  # already blocked once this turn; never loop
    agent = data.get("agent_transcript_path") if data.get("hook_event_name") == "SubagentStop" else None
    path = agent or data.get("transcript_path")
    if not path or not Path(path).is_file():
        return None
    main = data.get("transcript_path")
    others = family(Path(main) if main else Path(path), Path(path))
    missing = uncovered(Path(path), others)
    if not missing:
        return None
    lines = [f"- {p}: lines {', '.join(f'{a}-{b}' for a, b in gaps)} not read"
             for p, gaps in sorted(missing.items())]
    return {"decision": "block",
            "reason": "read-guard: these documents were read only in part this turn:\n" + "\n".join(lines) +
                      "\nRead the missing lines now (Read with `offset`, every page to the last line), then "
                      "finish. If a document truly cannot be read, tell the user exactly which lines were "
                      "not read, and never describe it as read."}


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
        event = data.get("hook_event_name")
        if event == "PreToolUse":
            out = pre_tool_use(data)
        elif event in ("Stop", "SubagentStop"):
            out = stop(data)
        else:
            out = None
        if out:
            sys.stdout.write(json.dumps(out) + "\n")
    except Exception:  # noqa: BLE001 — a guard bug must never stop work
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
