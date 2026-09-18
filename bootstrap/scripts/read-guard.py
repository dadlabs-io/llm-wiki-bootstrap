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

  Stop and SubagentStop — at the end of every turn, reads the session's own
  transcript: every Read of a document made in this turn is checked against
  the lines the Read tool reported returning (startLine, numLines, totalLines),
  pooled with every other Read of that file in the session. A document not
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

DOC_EXTS = {".md", ".markdown", ".mdx", ".txt", ".rst", ".adoc", ".org"}
# A Read above this size may need several pages (the Read tool caps one call at
# about 25,000 tokens); a start-capped Read is only allowed above it.
ONE_READ_MAX_BYTES = 60_000
# Claude Code keeps about 30,000 characters of a shell command's output and
# saves the rest to a file behind a short preview. Stay well under it.
SHELL_OUTPUT_MAX_BYTES = 25_000

_PARTIAL_PS = re.compile(r"-(TotalCount|Head|Tail|First|Last)\b", re.I)
_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\s*(?=\n|$)", re.S)
_REDIRECT = re.compile(r"^\d*>>?&?\d*$")


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


def is_doc(path: str) -> bool:
    return Path(path.strip().strip("'\"")).suffix.lower() in DOC_EXTS


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


def check_shell(command: str, cwd: str) -> str | None:
    docs_so_far: list[str] = []  # documents flowing into this command through a pipe
    cat_docs: list[str] = []
    for seg, piped in segments(command):
        if not piped:
            docs_so_far = []
        words = _words(seg)
        if not words:
            continue
        cmd = Path(words[0]).name.lower()
        docs = [w for w in _operands(words) if is_doc(w)]
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
        reason = check_shell(str(tin.get("command") or ""), cwd)
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


def uncovered(transcript: Path) -> dict[str, list[tuple[int, int]]]:
    """{document path: missing line ranges} for documents Read in the current turn
    and not covered start to end across the whole session."""
    entries = []
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    turn_start = max((i for i, e in enumerate(entries) if _is_prompt(e)), default=0)
    ranges: dict[str, list[tuple[int, int]]] = {}
    total: dict[str, int] = {}
    in_turn: set[str] = set()
    written: set[str] = set()
    for i, e in enumerate(entries):
        msg = e.get("message") or {}
        content = msg.get("content") if isinstance(msg.get("content"), list) else []
        for x in content:
            if isinstance(x, dict) and x.get("type") == "tool_use" and x.get("name") == "Write":
                written.add(os.path.normcase(str((x.get("input") or {}).get("file_path") or "")))
        result = e.get("toolUseResult")
        f = result.get("file") if isinstance(result, dict) and result.get("type") == "text" else None
        if not isinstance(f, dict) or not is_doc(str(f.get("filePath") or "")):
            continue
        key = os.path.normcase(str(f["filePath"]))
        start, num, tot = int(f.get("startLine") or 1), int(f.get("numLines") or 0), int(f.get("totalLines") or 0)
        total[key] = tot or total.get(key, 0)
        if num:
            ranges.setdefault(key, []).append((start, start + num - 1))
        if i > turn_start:
            in_turn.add(key)
    missing: dict[str, list[tuple[int, int]]] = {}
    for key in in_turn:
        if key in written or not total.get(key):
            continue
        gaps, nxt = [], 1
        for a, b in sorted(ranges.get(key, [])):
            if a > nxt:
                gaps.append((nxt, a - 1))
            nxt = max(nxt, b + 1)
        if nxt <= total[key]:
            gaps.append((nxt, total[key]))
        if gaps:
            missing[key] = gaps
    return missing


def stop(data: dict) -> dict | None:
    if data.get("stop_hook_active"):
        return None  # already blocked once this turn; never loop
    path = data.get("agent_transcript_path") if data.get("hook_event_name") == "SubagentStop" else None
    path = path or data.get("transcript_path")
    if not path or not Path(path).is_file():
        return None
    missing = uncovered(Path(path))
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
