#!/usr/bin/env python3
"""Checks for scripts/read-guard.py, run through its real entry point
(JSON on stdin, as Claude Code calls it). Never shipped.

    python tests/hooks/test_read_guard.py      # exit 0 = every check passed
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

GUARD = Path(__file__).resolve().parents[2] / "scripts" / "read-guard.py"
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
        # 2026-09-18, the first false block: a command's own stderr capture is output, not a document
        check("cmd 2> err.txt; tail -5 err.txt -> allow (own output capture)",
              not sh('python x.py > "$T/out.json" 2> "$T/err.txt"; tail -5 "$T/err.txt"'))
        check("cmd >log.txt && head log.txt -> allow (attached redirect)",
              not sh("python x.py >log.txt && head -20 log.txt"))
        check("cmd 2> err.txt; tail -5 notes.md -> deny (a different file)",
              sh('python x.py 2> err.txt; tail -5 notes.md'))
        # 2026-09-26, the first week's review: 27 false blocks, all output rather than documents
        check("tail an earlier command's .txt output -> allow", not sh("cat -A /tmp/pytest_out.txt | tail -5"))
        check("tail -12 a repo proof-output .txt -> allow",
              not sh("tail -12 .do-code-change/x/round6-proof/proof-output-six-frozen-tests.txt"))
        check("tail a $TEMP .txt capture -> allow", not sh('tail -5 "$TEMP/pytest_out.txt"'))
        check("Read part of Claude Code's saved tool output (.txt) -> allow",
              not denied(pre("Read", {"file_path": str(tmp / "tool-results" / "b1.txt"), "limit": 40}, tmp)))
        check("head a cloned source's README in a scratchpad -> deny (sources are read whole)",
              sh('head -60 "C:/Users/me/AppData/Local/Temp/claude/p/abc/scratchpad/clones/repo/README.md"'))
        check("sed -i on a doc, then head it -> allow (checking its own edit)",
              not sh("sed -i 's/^a$/b/' skills/x/SKILL.md && head -8 skills/x/SKILL.md"))
        check("printf >> skills/$s/README.md in a loop, then tail one -> allow",
              not sh("for s in a b; do printf 'x' >> skills/$s/evals/README.md; done; "
                     "tail -5 skills/b/evals/README.md"))
        check("sed -i one doc, head a different doc -> deny",
              sh("sed -i 's/a/b/' skills/x/SKILL.md && head -8 skills/y/SKILL.md"))
        check("head a file named scratchpad.md in a real folder -> deny",
              sh("sed -n '1,20p' _inbox/reports/2026-09-24-01/scratchpad.md"))
        # 2026-09-26, the user's pick: do-code-change's two append-only logs may be read in part
        check("tail -60 .do-code-change/<run>/doubt-log.md -> allow (append-only log)",
              not sh("tail -60 .do-code-change/schema-names/doubt-log.md"))
        check("tail an archived run's checkpoints.md -> allow",
              not sh('tail -n 150 "C:/github.com/p/.do-code-change/archive/2026-09-24-x/checkpoints.md"'))
        check("Read the first page of .do-code-change/<run>/checkpoints.md -> allow",
              not denied(pre("Read", {"file_path": str(tmp / ".do-code-change" / "r" / "checkpoints.md"),
                                      "limit": 50}, tmp)))
        check("tail a doubt-log.md outside .do-code-change -> deny", sh("tail -5 notes/doubt-log.md"))
        check("tail a run's plan.md -> deny (only the two logs)",
              sh("tail -20 .do-code-change/schema-names/plan.md"))
        check("cmd 2>&1 | tail; tail -2 task.md -> deny (2>&1 names no file)",
              sh("python x.py 2>&1 | tail -3; tail -2 main/task.md"))
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
        check("Stop: the end of a run's doubt-log.md read -> allow (append-only log)",
              not blocked(stop(tmp, [prompt(), read_entry(tmp / ".do-code-change" / "r" / "doubt-log.md",
                                                            400, 60, 460)])))
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
