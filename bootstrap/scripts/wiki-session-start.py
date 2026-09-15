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
  - prints the paths of sessions/active-context.md, sessions/<persona>/handoff.md
    and sessions/<persona>/task.md (each if present) with the instruction to
    read them before the first reply

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


def resume_text(start: Path) -> str:
    cfg_path = project_config(start)
    if not cfg_path:
        return ""
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        return ""
    root = cfg_path.parent.parent
    from _wiki_config import wiki_dir  # the resolution every wiki script uses
    wiki = Path(wiki_dir(cwd=root))
    if not wiki.is_dir():
        return ""
    persona = str(cfg.get("persona") or "main").strip().lower()
    sessions = wiki / "sessions"
    files = [f for f in (sessions / "active-context.md", sessions / persona / "handoff.md",
                         sessions / persona / "task.md") if f.is_file()]
    if not files:
        return ""
    name = cfg.get("project_name") or root.name
    lines = [f"llm-wiki SessionStart hook: resume files for {name} (persona: {persona}). Before your first "
             "reply, read them in this order, then open the reply, whatever the user said, with one paragraph "
             "on where we left off and what is next:"]
    lines += [f"{i}. {f} ({f.stat().st_size / 1024:.1f} KB)" for i, f in enumerate(files, 1)]
    return "\n".join(lines) + "\n"


def main() -> int:
    try:
        out = resume_text(session_cwd(sys.argv[1:]).resolve())
        if out:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stdout.write(out)
    except Exception:  # noqa: BLE001 — a resume hook must never break a session start
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
