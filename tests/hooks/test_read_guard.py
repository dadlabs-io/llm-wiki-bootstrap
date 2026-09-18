#!/usr/bin/env python3
"""Checks for bootstrap/scripts/read-guard.py, run through its real entry point
(JSON on stdin, as Claude Code calls it). Never shipped.

    python tests/hooks/test_read_guard.py      # exit 0 = every check passed
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

GUARD = Path(__file__).resolve().parents[2] / "bootstrap" / "scripts" / "read-guard.py"
results: list[tuple[bool, str]] = []


def run(data: dict) -> dict | None:
    p = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(data), capture_output=True,
                       text=True, encoding="utf-8", timeout=30)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout) if p.stdout.strip() else None


def denied(out: dict | None) -> bool:
    return bool(out) and out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def check(name: str, ok: bool):
    results.append((ok, name))


def pre(tool: str, tool_input: dict, cwd: Path) -> dict | None:
    return run({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "cwd": str(cwd)})


def read_entry(path: Path, start: int, num: int, total: int) -> dict:
    return {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x",
                                                                      "content": "..."}]},
            "toolUseResult": {"type": "text", "file": {"filePath": str(path), "startLine": start,
                                                       "numLines": num, "totalLines": total}}}


def prompt(text: str = "go") -> dict:
    return {"type": "user", "message": {"role": "user", "content": text}}


def write_entry(path: Path) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": "w", "name": "Write", "input": {"file_path": str(path), "content": "x"}}]}}


def stop(tmp: Path, entries: list[dict], **extra) -> dict | None:
    t = tmp / f"t{len(results)}.jsonl"
    t.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    data = {"hook_event_name": "Stop", "transcript_path": str(t), "stop_hook_active": False}
    data.update(extra)
    return run(data)


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "main").mkdir()
        small = tmp / "main" / "task.md"
        small.write_text("line\n" * 4000, encoding="utf-8")          # 20 KB: one Read
        big = tmp / "big.md"
        big.write_text(("x" * 99 + "\n") * 1000, encoding="utf-8")  # 100 KB: needs paging
        mid = tmp / "mid.md"
        mid.write_text(("y" * 99 + "\n") * 300, encoding="utf-8")   # 30 KB: over the shell cap
        code = tmp / "tool.py"
        code.write_text("print(1)\n" * 50, encoding="utf-8")

        # ---- PreToolUse: Read ----
        check("Read small doc with limit -> deny", denied(pre("Read", {"file_path": str(small), "limit": 50}, tmp)))
        check("Read small doc whole -> allow", not denied(pre("Read", {"file_path": str(small)}, tmp)))
        check("Read continuation page (offset 100) -> allow",
              not denied(pre("Read", {"file_path": str(small), "offset": 100, "limit": 50}, tmp)))
        check("Read first page of a 100 KB doc -> allow (paging needed)",
              not denied(pre("Read", {"file_path": str(big), "limit": 500}, tmp)))
        check("Read code file with limit -> allow", not denied(pre("Read", {"file_path": str(code), "limit": 5}, tmp)))

        # ---- PreToolUse: shell ----
        sh = lambda c, tool="Bash": denied(pre(tool, {"command": c}, tmp))  # noqa: E731
        check("head -c 9000 main/task.md -> deny (the 2026-09-18 read)", sh("head -c 9000 main/task.md"))
        check("cat two docs && head -c 9000 task.md -> deny",
              sh('cd "x" && cat active-context.md main/handoff.md && head -c 9000 main/task.md'))
        check("cat doc | head -40 -> deny", sh("cat main/task.md | head -40"))
        check("sed -n '1,20p' doc -> deny", sh("sed -n '1,20p' CHANGELOG.md"))
        check("tail -2 MEMORY.md -> deny", sh("tail -2 MEMORY.md"))
        check("tail -c +9001 task.md -> deny", sh("tail -c +9001 main/task.md"))
        check("grep doc | head -> allow", not sh("grep -n foo main/task.md | head -2"))
        check("cat small; git log | head -> allow", not sh("cat main/task.md; git log --oneline | head -3"))
        check("cat > new.md heredoc mentioning head -> allow",
              not sh("cat > new.md <<'EOF'\nhead -5 main/task.md is just text here\nEOF"))
        check("commit message mentioning head -5 notes.md -> allow",
              not sh('git commit -m "first line\nhead -5 notes.md is prose"'))
        check("cat a 30 KB doc through the shell -> deny", sh("cat mid.md"))
        check("cat a 20 KB doc -> allow", not sh("cat main/task.md"))
        check("cat 20 KB + 30 KB docs -> deny", sh("cat main/task.md mid.md"))
        check("sed -i on a doc (an edit) -> allow", not sh("sed -i 's/a/b/' main/task.md"))
        check("head -5 on a code file -> allow", not sh("head -5 tool.py"))
        check("echo x > out.md -> allow", not sh("echo x > out.md"))
        check("PowerShell Get-Content -TotalCount -> deny",
              sh(f"Get-Content {tmp}\\main\\task.md -TotalCount 20", "PowerShell"))
        check("PowerShell Get-Content | Select-Object -First -> deny",
              sh("Get-Content main/task.md | Select-Object -First 10", "PowerShell"))
        check("PowerShell Get-Content whole (20 KB) -> allow", not sh("Get-Content main/task.md", "PowerShell"))
        check("Glob/other tools -> allow", not denied(pre("Grep", {"pattern": "x", "path": str(small)}, tmp)))

        # ---- Stop ----
        blocked = lambda o: bool(o) and o.get("decision") == "block"  # noqa: E731
        check("Stop: doc read whole -> allow", not blocked(stop(tmp, [prompt(), read_entry(small, 1, 300, 300)])))
        o = stop(tmp, [prompt(), read_entry(small, 1, 100, 300)])
        check("Stop: doc read 1-100 of 300 -> block", blocked(o))
        check("Stop: block names the missing range 101-300", blocked(o) and "101-300" in o["reason"])
        check("Stop: two pages covering 1-300 -> allow",
              not blocked(stop(tmp, [prompt(), read_entry(big, 1, 150, 300), read_entry(big, 151, 150, 300)])))
        check("Stop: middle slice only -> block with both gaps",
              (lambda o: blocked(o) and "1-13" in o["reason"] and "28-300" in o["reason"])(
                  stop(tmp, [prompt(), read_entry(small, 14, 14, 300)])))
        check("Stop: partial read in an EARLIER turn only -> allow",
              not blocked(stop(tmp, [prompt(), read_entry(small, 1, 100, 300), prompt("next")])))
        check("Stop: earlier full read + this turn's slice -> allow",
              not blocked(stop(tmp, [prompt(), read_entry(small, 1, 300, 300), prompt("next"),
                                     read_entry(small, 20, 10, 300)])))
        check("Stop: stop_hook_active -> allow (no loop)",
              not blocked(stop(tmp, [prompt(), read_entry(small, 1, 100, 300)], stop_hook_active=True)))
        check("Stop: doc the session wrote itself -> allow",
              not blocked(stop(tmp, [prompt(), write_entry(small), read_entry(small, 1, 10, 300)])))
        check("Stop: code file partly read -> allow",
              not blocked(stop(tmp, [prompt(), read_entry(code, 1, 5, 50)])))
        t = tmp / "agent.jsonl"
        t.write_text("\n".join(json.dumps(e) for e in [prompt(), read_entry(small, 1, 100, 300)]) + "\n",
                     encoding="utf-8")
        check("SubagentStop: reads the agent's own transcript -> block",
              blocked(run({"hook_event_name": "SubagentStop", "agent_transcript_path": str(t),
                           "transcript_path": str(tmp / "none.jsonl"), "stop_hook_active": False})))
        check("Garbage input -> no output, exit 0", run({"hook_event_name": "Stop", "transcript_path": 5}) is None)

    for ok, name in results:
        print(("PASS  " if ok else "FAIL  ") + name)
    failed = sum(not ok for ok, _ in results)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
