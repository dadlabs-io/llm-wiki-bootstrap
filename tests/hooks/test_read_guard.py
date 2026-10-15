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

        # ---- 2026-10-15, task #150: reads done by the session's helper agents count ----
        # Claude Code keeps a session's subagent transcripts in <session>/subagents/agent-*.jsonl
        # beside <session>.jsonl. The REA ingest (2026-10-14): helpers read the ranges the main
        # session had not, and the Stop hook blocked over them six times.
        fam = tmp / "fam"
        fam.mkdir()

        def family(main_entries: list[dict], agents: dict[str, list[dict]]) -> Path:
            sid = f"s{len(results)}"
            main_t = fam / f"{sid}.jsonl"
            main_t.write_text("\n".join(json.dumps(e) for e in main_entries) + "\n", encoding="utf-8")
            sub = fam / sid / "subagents"
            sub.mkdir(parents=True)
            for name, entries in agents.items():
                (sub / f"agent-{name}.jsonl").write_text(
                    "\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
            return main_t

        def stop_t(t: Path, **extra) -> dict | None:
            data = {"hook_event_name": "Stop", "transcript_path": str(t), "stop_hook_active": False}
            data.update(extra)
            return run(data)

        t = family([prompt(), read_entry(big, 1, 100, 300)],
                   {"a1": [prompt("brief"), read_entry(big, 101, 200, 300)]})
        check("Stop: main read 1-100, a helper read 101-300 -> allow", not blocked(stop_t(t)))
        t = family([prompt(), read_entry(big, 1, 100, 300)],
                   {"a1": [prompt("brief"), read_entry(big, 101, 100, 300)],
                    "a2": [prompt("brief"), read_entry(big, 251, 50, 300)]})
        o = stop_t(t)
        check("Stop: helpers leave 201-250 unread -> block naming only 201-250",
              blocked(o) and "201-250" in o["reason"] and "101" not in o["reason"])
        t = family([prompt(), read_entry(big, 1, 100, 300)],
                   {"a1": [prompt("brief"), read_entry(small, 1, 300, 300)]})
        check("Stop: a helper read a different doc -> still block", blocked(stop_t(t)))
        t = family([prompt(), read_entry(big, 1, 100, 300)], {})
        check("Stop: an empty subagents folder -> block as before", blocked(stop_t(t)))
        # a helper stopping: its siblings' and the main session's reads count too
        t = family([prompt(), read_entry(big, 1, 150, 300)],
                   {"a1": [prompt("brief"), read_entry(big, 151, 150, 300)]})
        check("SubagentStop: helper read 151-300, main read 1-150 -> allow",
              not blocked(run({"hook_event_name": "SubagentStop", "stop_hook_active": False,
                               "transcript_path": str(t),
                               "agent_transcript_path": str(t.with_suffix("") / "subagents" / "agent-a1.jsonl")})))

        # ---- 2026-10-15, task #149: never file an entry from a raw not read to its last line ----
        # The REA entry was filed from a 29,095-line raw read in part; the full read found 6 wrong claims.
        nb = tmp / "nb"
        (nb / "raw").mkdir(parents=True)
        raw = nb / "raw" / "2026-10-15-some-repo.md"
        raw.write_text(("r" * 60 + "\n") * 300, encoding="utf-8")
        file_cmd = ("uv run --project ~/.claude/wiki-scripts python ~/.claude/wiki-scripts/wiki-update.py "
                    "--topic nb --folder research/x --source nb/_inbox/temp/s.md --source-url https://x.y "
                    "--raw-path raw/2026-10-15-some-repo.md --ingested-by claude-code --tier 3 "
                    "--confidence medium --title \"T\" --tags \"a,b,c\"")

        def file_with(t: Path, command: str = file_cmd) -> dict | None:
            return run({"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command},
                        "cwd": str(tmp), "transcript_path": str(t)})

        def bash_entry(command: str) -> dict:
            return {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "b", "name": "Bash", "input": {"command": command}}]}}

        t = family([prompt(), read_entry(raw, 1, 300, 300)], {})
        check("File: raw read whole -> allow", not denied(file_with(t)))
        t = family([prompt(), read_entry(raw, 1, 120, 300)], {})
        o = file_with(t)
        check("File: raw read 1-120 of 300 -> deny", denied(o))
        check("File: the refusal names the unread lines 121-300",
              denied(o) and "121-300" in o["hookSpecificOutput"]["permissionDecisionReason"])
        t = family([prompt(), read_entry(raw, 1, 120, 300)],
                   {"a1": [prompt("brief"), read_entry(raw, 121, 180, 300)]})
        check("File: main read 1-120, a helper read 121-300 -> allow", not denied(file_with(t)))
        t = family([prompt(), read_entry(raw, 1, 299, 300)], {})
        check("File: all but a lone last line read -> allow (a trailing blank line)", not denied(file_with(t)))
        t = family([prompt(), read_entry(raw, 1, 298, 300)], {})
        check("File: the last two lines unread -> deny", denied(file_with(t)))
        t = family([prompt(), {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": "r", "name": "Read", "input": {"file_path": str(raw)}}]}}], {})
        check("File: Read called but no result recorded (old transcripts) -> allow (can't tell)",
              not denied(file_with(t)))
        # the live suite run (2026-10-15, wiki-update 20261015-011332): a headless session's helper transcripts
        # carry the Read call and its numbered text, but no toolUseResult line counts
        def bare_read(path: Path, first: int, last: int, rid: str) -> list[dict]:
            return [{"type": "assistant", "message": {"role": "assistant", "content": [
                        {"type": "tool_use", "id": rid, "name": "Read",
                         "input": {"file_path": str(path), "offset": first, "limit": last - first + 1}}]}},
                    {"type": "user", "message": {"role": "user", "content": [
                        {"type": "tool_result", "tool_use_id": rid,
                         "content": "\n".join(f"{n}\tr" for n in range(first, last + 1))}]}}]
        t = family([prompt(), read_entry(raw, 1, 120, 300)],
                   {"a1": [prompt("brief")] + bare_read(raw, 121, 210, "r1") + bare_read(raw, 211, 300, "r2")})
        check("File: helpers' reads with no toolUseResult (headless) counted from their numbered text -> allow",
              not denied(file_with(t)))
        t = family([prompt(), read_entry(raw, 1, 120, 300)],
                   {"a1": [prompt("brief")] + bare_read(raw, 121, 210, "r1")})
        o = file_with(t)
        check("File: those helpers leave 211-300 unread -> deny naming 211-300",
              denied(o) and "211-300" in o["hookSpecificOutput"]["permissionDecisionReason"])
        t = family([prompt()], {})
        check("File: raw never read -> deny", denied(file_with(t)))
        t = family([prompt(), bash_entry(f"cat {raw}")], {})
        check("File: raw printed whole with cat -> allow", not denied(file_with(t)))
        # the backtest over saved transcripts (2026-10-15): ingest workers print raws in a loop
        t = family([prompt(), bash_entry("cd nb/raw && for f in some-repo other; do cat 2026-10-15-$f.md; done")], {})
        check("File: raw printed by a cat loop over a variable -> allow", not denied(file_with(t)))
        t = family([prompt(), bash_entry("cd nb/raw && cat 2026-10-15-some-repo.md | head -50")], {})
        check("File: raw cat piped into head -> deny", denied(file_with(t)))
        t = family([prompt(), bash_entry('OUT=nb/raw/2026-10-15-some-repo.md; for p in a b; do cat "$p"; done > "$OUT"')], {})
        check("File: raw built by the session through a shell redirect -> allow", not denied(file_with(t)))
        t = family([prompt(), bash_entry("cd nb/raw && mv 2026-10-15-untitled.md 2026-10-15-some-repo.md")], {})
        check("File: raw renamed by the session (mv) -> allow", not denied(file_with(t)))
        t = family([prompt(), {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": "g", "name": "Grep", "input": {"pattern": "x", "path": str(raw)}}]}}], {})
        check("File: raw only grepped -> deny", denied(file_with(t)))
        # a local file read whole, then copied into raw/ under a dated name by --fetch-only (suite runs)
        src = tmp / "inputs" / "field-report.md"
        src.parent.mkdir()
        src.write_text("s\n" * 40, encoding="utf-8")
        local_cmd = file_cmd.replace("--source-url https://x.y", f'--source-url "file://{src}"')
        t = family([prompt(), read_entry(src, 1, 40, 40)], {})
        check("File: the local source file read whole -> allow", not denied(file_with(t, local_cmd)))
        t = family([prompt(), read_entry(src, 1, 10, 40)], {})
        check("File: the local source file read in part -> deny", denied(file_with(t, local_cmd)))
        t = family([prompt()], {})
        check("File: pasted text (internal:// source) -> allow (the session wrote it)",
              not denied(file_with(t, file_cmd.replace("https://x.y", "internal://paste/2026-10-15-notes"))))
        undated = tmp / "inputs" / "some-repo.md"  # --fetch-only saved it as raw/2026-10-15-some-repo.md
        undated.write_text("u\n" * 30, encoding="utf-8")
        t = family([prompt(), bash_entry(f"cat inputs/some-repo.md")], {})
        check("File: the undated original of a dated raw printed whole -> allow", not denied(file_with(t)))
        t = family([prompt(), read_entry(undated, 1, 5, 30)], {})
        check("File: the undated original read in part -> deny", denied(file_with(t)))
        t = family([prompt(), read_entry(raw, 1, 120, 300)], {})
        check("File: --regate re-checks a filed entry -> allow",
              not denied(file_with(t, "uv run python wiki-update.py --topic nb --regate some-slug")))
        check("File: --fetch-only -> allow",
              not denied(file_with(t, "uv run python wiki-update.py --topic nb --source https://x.y --fetch-only")))
        check("File: --partial-source on the user's word -> allow",
              not denied(file_with(t, file_cmd + " --partial-source 'Mark: file the preview'")))
        check("File: a different raw than the one read -> deny",
              denied(file_with(family([prompt(), read_entry(raw, 1, 300, 300)], {}),
                               file_cmd.replace("some-repo", "other-repo"))))
        check("File: raw path given with = -> deny when unread",
              denied(file_with(family([prompt()], {}),
                               file_cmd.replace("--raw-path raw/", "--raw-path=raw/"))))
        check("File: a .txt raw (not a document) -> allow",
              not denied(file_with(family([prompt()], {}), file_cmd.replace(".md", ".txt"))))
        check("File: no transcript -> allow (never stops work)",
              not denied(run({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                              "tool_input": {"command": file_cmd}, "cwd": str(tmp)})))

    for ok, name in results:
        print(("PASS  " if ok else "FAIL  ") + name)
    failed = sum(not ok for ok, _ in results)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
