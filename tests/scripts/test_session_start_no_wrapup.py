#!/usr/bin/env python3
"""Checks that the SessionStart hook flags a previous session that ended without /wrap-up (task #182 row 33).
Never shipped.

    uv run python tests/scripts/test_session_start_no_wrapup.py    # exit 0 = every check passed

The resume files are written by /wrap-up. A session that ends without one leaves them describing the session
before it, and nothing said so (startup-launch decision, 2026-09-18, Caveats: "Nothing flags that yet"), so the
next session resumes from a stale handoff without knowing. Claude Code passes the hook the new session's
transcript_path; the previous session's transcript sits beside it. When that transcript was still being written
well after handoff.md (30 minutes), the hook says the previous session may have ended without a wrap-up.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "scripts" / "wiki-session-start.py"
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    proj = td / "proj"
    wiki = proj / "llm-wiki" / "wiki"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps({"vault_root": str(proj), "wiki_topic": "llm-wiki"}),
                                                       encoding="utf-8")
    (wiki / "sessions" / "main").mkdir(parents=True)
    handoff = wiki / "sessions" / "main" / "handoff.md"
    handoff.write_text("GOAL: carry on\n", encoding="utf-8")
    transcripts = td / "projects" / "proj"
    transcripts.mkdir(parents=True)
    current = transcripts / "cccc-current.jsonl"
    current.write_text("{}\n", encoding="utf-8")
    previous = transcripts / "pppp-previous.jsonl"
    previous.write_text("{}\n", encoding="utf-8")
    (transcripts / "pppp-previous").mkdir()  # its subagents' folder: never taken for a session
    t0 = time.time() - 6 * 3600

    def stamp(path: Path, minutes_after_t0: float):
        os.utime(path, (t0 + minutes_after_t0 * 60, t0 + minutes_after_t0 * 60))

    def hook(with_transcript: bool = True) -> tuple[str, str]:
        data = {"cwd": str(proj), "session_id": "cccc-current", "hook_event_name": "SessionStart"}
        if with_transcript:
            data["transcript_path"] = str(current)
        p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(data), capture_output=True, text=True,
                           encoding="utf-8")
        out = json.loads(p.stdout) if p.stdout.strip() else {}
        return out.get("hookSpecificOutput", {}).get("additionalContext", ""), out.get("systemMessage", "")

    # 1. the previous session ran on for two hours after the handoff was written: flagged
    stamp(handoff, 0)
    stamp(previous, 120)
    stamp(current, 300)
    ctx, user = hook()
    check("flagged: the context says the previous session may have ended without /wrap-up",
          "without /wrap-up" in ctx and "pppp-previous" in ctx, ctx[-600:])
    check("... names its transcript, so the recap can say what it was", str(previous) in ctx, ctx[-600:])
    check("... and the step-5 recap is told to say so", "say so" in ctx.lower(), ctx[-600:])
    check("... the user's startup line says it too", "wrap-up" in user.lower(), user)

    # 2. the previous session ended a few minutes after its wrap-up wrote the handoff: nothing said
    stamp(previous, 8)
    ctx, user = hook()
    check("a session that ended right after its wrap-up is not flagged", "without /wrap-up" not in ctx
          and "wrap-up" not in user.lower(), ctx[-300:])

    # 3. no previous session at all, or no transcript_path in the input: the hook works as before
    previous.unlink()
    ctx, user = hook()
    check("no previous transcript: no flag, the usual startup", "without /wrap-up" not in ctx and "handoff.md" in ctx, ctx[-300:])
    previous.write_text("{}\n", encoding="utf-8")
    stamp(previous, 120)
    ctx, user = hook(with_transcript=False)
    check("no transcript_path in the input: no flag, the usual startup", "without /wrap-up" not in ctx
          and "handoff.md" in ctx, ctx[-300:])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
