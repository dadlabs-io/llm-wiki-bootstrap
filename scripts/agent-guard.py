#!/usr/bin/env python3
"""
PreToolUse hook: holds an agent to the commands its job needs (task #145, 2026-10-14).

An ingest worker reads untrusted pages, transcripts and repositories, and it runs in a session that
can push to git and post to Discord: private data, untrusted content and a way out, the "lethal
trifecta" (Kim Maida, Keycard, AI Engineer 2026). Its definition already leaves out every MCP tool,
so it cannot post; its Bash is needed for the wiki scripts and `git clone --depth 1`. This hook
refuses the rest of what Bash could do for it: git commands that write or publish, and the network
and remote-shell tools the wiki scripts make unnecessary.

Claude Code sends `agent_type` with every tool call a subagent makes, so the rules apply to that agent
only (RULES below); the main session and every other agent are untouched. Any error, an unknown
agent or an unparsable input allows the call: a guard that broke would otherwise block every command.

    stdin: the hook input (tool_name, tool_input.command, agent_type)
    stdout: a PreToolUse deny decision, or nothing
"""
from __future__ import annotations

import json
import re
import shlex
import sys

# git subcommands an ingest worker may run: reading a clone and making one
GIT_READ = {"clone", "log", "show", "status", "diff", "rev-parse", "ls-files", "ls-tree", "cat-file",
            "branch", "describe", "blame", "grep", "shortlog", "version", "help", "--version"}
# programs that reach the network or another machine on their own; the wiki scripts do the fetching
NETWORK = {"curl", "wget", "invoke-webrequest", "invoke-restmethod", "iwr", "irm", "scp", "sftp", "ssh",
           "rsync", "ftp", "nc", "ncat", "netcat", "telnet", "gh", "start-bitstransfer"}

RULES = {
    # agent_type -> why, shown to the agent when a command is refused
    "wiki-ingester": "an ingest worker reads untrusted sources, so it may not write to git or reach the "
                     "network except through the wiki scripts (task #145). The orchestrator owns git; "
                     "fetching is wiki-update.py's, wiki-transcribe.py's and the other fetchers' job",
}

SPLIT = re.compile(r"\|\||&&|[;|&\n]")


def _words(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def _prog(word: str) -> str:
    name = re.split(r"[\\/]", word)[-1].lower()
    return name[:-4] if name.endswith(".exe") else name


def refused(command: str) -> str | None:
    """The first part of the command the rules refuse, with why; None when every part is allowed."""
    for seg in SPLIT.split(command or ""):
        w = [x for x in _words(seg.strip()) if x]
        while w and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w[0]):  # VAR=value prefixes
            w = w[1:]
        if w and _prog(w[0]) in {"sudo", "env", "command", "exec", "nohup", "time"}:
            w = w[1:]
        if not w:
            continue
        prog = _prog(w[0])
        if prog in NETWORK:
            return f"`{prog}` reaches the network or another machine"
        if prog == "git":
            rest, i = w[1:], 0
            while i < len(rest) and rest[i].startswith("-"):  # git -C <dir>, -c k=v, --no-pager
                i += 2 if rest[i] in ("-C", "-c", "--git-dir", "--work-tree") else 1
            sub = rest[i].lower() if i < len(rest) else ""
            if sub and sub not in GIT_READ:
                return f"`git {sub}` writes to or publishes from a repository"
            if sub == "branch" and any(a in ("-d", "-D", "-m", "-M", "--delete", "--move") for a in rest[i + 1:]):
                return "`git branch` with a change"
        if prog in {"powershell", "pwsh", "bash", "sh", "cmd"}:
            inner = " ".join(w[1:])
            why = refused(re.sub(r"^(-c|-command|/c)\s+", "", inner, flags=re.I).strip("'\""))
            if why:
                return why
    return None


def decide(data: dict) -> dict | None:
    agent = data.get("agent_type")
    if agent not in RULES or data.get("tool_name") not in ("Bash", "PowerShell"):
        return None
    why = refused(str((data.get("tool_input") or {}).get("command") or ""))
    if not why:
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": f"agent-guard: {why}; {RULES[agent]}."}}


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
        out = decide(data) if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001 - a broken guard must never block every call
        return 0
    if out:
        sys.stdout.write(json.dumps(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
