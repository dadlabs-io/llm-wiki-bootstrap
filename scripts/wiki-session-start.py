#!/usr/bin/env python3
"""
wiki-session-start.py — the SessionStart hook that points a new session at its
wiki project's resume files, so the Resuming read is an event, not a prose rule.

The tooling install adds it to ~/.claude/settings.json under SessionStart
(matcher startup|clear: a new session, and after /clear wipes the context).
Claude Code adds what it prints to the session's context. For each session:

  - finds the project's own .claude/wiki-config.json, walking up from the
    session's folder; the machine config in the home folder is NOT a project
    (without that rule every folder under the home folder — Desktop, Downloads —
    would look like a wiki project)
  - resolves the project's wiki the way every wiki script does (_wiki_config:
    a registry notebook, or an in-project llm-wiki/)
  - prints, as the hook's JSON output, the paths of sessions/active-context.md,
    sessions/<persona>/handoff.md and sessions/<persona>/task.md (each if present)
    with the startup checklist to run before the first reply (additionalContext,
    for Claude), and one line for the user — the handoff's GOAL — shown in the
    terminal at startup (systemMessage)

The user line (2026-09-15): a hook cannot start a model turn, so the recap
only comes with the user's first message, and plain stdout reaches Claude
alone — the user saw a blank prompt and thought the hook had not run. The
systemMessage shows where things stand before anything is typed; the full
recap needs a first message (or a launch with one, e.g. `claude "resume"`).

Paths, not contents: Claude Code keeps only a ~2 KB preview of a hook's output
in context and saves the rest to a file. In the first real session (2026-09-14)
the 18.3 KB of printed file contents arrived as a 2 KB preview that stopped
inside active-context.md, so the session would have resumed from a fragment.

Anything else prints nothing and exits 0: no project config, a wiki that does
not exist, no resume files yet, an unreadable config, any error. It never
blocks a session start. (User decision 2026-09-14: "if there's a wiki config we
do that, otherwise do nothing, not even a message".)

persona: the project config's "persona" key, lower-cased; default "main"
(agent-builder-bootstrap's sessions work as ARCH, in sessions/arch/).

Usage (Claude Code passes the hook input as JSON on stdin, including "cwd"):
  python wiki-session-start.py              # as the hook runs it
  python wiki-session-start.py --cwd <dir>  # by hand, to see what a session there gets
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def session_cwd(argv: list[str]) -> Path:
    if "--cwd" in argv:
        return Path(argv[argv.index("--cwd") + 1])
    if not sys.stdin.isatty():
        try:
            data = json.loads(sys.stdin.read() or "{}")
            if isinstance(data, dict) and data.get("cwd"):
                return Path(data["cwd"])
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            pass
    return Path.cwd()


def project_config(start: Path) -> Path | None:
    """The nearest .claude/wiki-config.json above start, skipping the home folder's."""
    home = os.path.normcase(str(Path.home().resolve()))
    for d in [start, *start.parents]:
        if os.path.normcase(str(d)) == home:
            continue  # ~/.claude/wiki-config.json is the machine config, not a project's
        p = d / ".claude" / "wiki-config.json"
        if p.is_file():
            return p
    return None


def handoff_goal(handoff: Path) -> str:
    """The GOAL line of a /wrap-up handoff.md ("GOAL: <one sentence>"), or ""."""
    try:
        for line in handoff.read_text(encoding="utf-8").splitlines():
            if line.startswith("GOAL:"):
                return line[len("GOAL:"):].strip()
    except (OSError, UnicodeDecodeError):
        pass
    return ""


def hook_output(start: Path) -> dict | None:
    """The hook's JSON: the resume instruction for Claude, one line for the user."""
    cfg_path = project_config(start)
    if not cfg_path:
        return None
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        return None
    root = cfg_path.parent.parent
    from _wiki_config import wiki_dir  # the resolution every wiki script uses
    wiki = Path(wiki_dir(cwd=root))
    if not wiki.is_dir():
        return None
    persona = str(cfg.get("persona") or "main").strip().lower()
    sessions = wiki / "sessions"
    files = [f for f in (sessions / "active-context.md", sessions / persona / "handoff.md",
                         sessions / persona / "task.md") if f.is_file()]
    if not files:
        return None
    name = cfg.get("project_name") or root.name
    # A checklist, not a sentence (2026-09-18): "read them" let a session cap a file at 9 KB, skip the
    # project's own Resuming steps and answer the launch line; another started a long run before its recap
    lines = [f"llm-wiki SessionStart hook: startup for {name} (persona: {persona}). The user's first message, "
             "whatever it says (often a launch line such as \"Ready to start Claude!\"), is the signal to run "
             "this startup, not a request to answer. Do every step, in order, before your first reply:",
             "1. Read each of these files in full: the whole file, no head/tail or byte or line limit, and "
             "every part if it comes back in parts:"]
    lines += [f"   {i}. {f} ({f.stat().st_size / 1024:.1f} KB)" for i, f in enumerate(files, 1)]
    lines += ["2. Read in full each memory file the MEMORY.md index in your context points to.",
              "3. Do every other step in the project CLAUDE.md's Resuming section (e.g. the intake inbox, the "
              "Discord channel catch-up).",
              "4. Start no other work (no runs, no edits) until the recap is given.",
              "5. Open the first reply with one paragraph on where we left off and what is next, then say what "
              "steps 1-3 found."]
    goal = handoff_goal(sessions / persona / "handoff.md")
    # Layout the user drew (2026-09-15): "Next:" on its own line, the goal's lead ("Start QUEUE 6:") above the rest
    head, sep, rest = goal.partition(": ")
    goal = f"{head}:\n{rest}" if sep else goal
    user_line = f"llm-wiki: {name} resume files are loaded.\n\n" + (f"Next:\n\n{goal} " if goal else "")
    user_line += "Send any message for the full recap.\n\n\n"
    return {"systemMessage": user_line,
            "hookSpecificOutput": {"hookEventName": "SessionStart",
                                   "additionalContext": "\n".join(lines) + "\n"}}


def main() -> int:
    try:
        out = hook_output(session_cwd(sys.argv[1:]).resolve())
        if out:
            sys.stdout.write(json.dumps(out) + "\n")  # ASCII-escaped, so no console encoding trap
    except Exception:  # noqa: BLE001 — a resume hook must never break a session start
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
