"""wrap-up's own never rules, as run checks (task #99; tests/skills/_trajectory.py).

Each rule quotes the SKILL.md line it tests. Reading a dashboard before rewriting it is not here:
Claude Code's Write tool already refuses to overwrite a file the session has not read, and a first
wrap-up creates the files, so a run check could only add false alarms (scored 2026-10-12: every hit
was a first-run case that looked with ls or Glob).
"""

SHELL = ["Bash", "PowerShell"]

RULES = [
    {"id": "never git add -A or add .", "kind": "never",
     "rule": "Never `git add -A` or `git add .`",
     "pattern": r"\bgit\b[^\n]*\badd\s+(-A\b|--all\b|\.(\s|$))", "tool": SHELL},
    {"id": "never force-pushes, pulls or rebases", "kind": "never",
     "rule": "Never force, never set up a remote, never pull or rebase to make a push go through.",
     "pattern": r"\bgit\b[^\n]*\bpush\b[^\n]*(--force|\s-f\b)|\bgit\b[^\n]*\b(pull|rebase)\b", "tool": SHELL},
    {"id": "never writes auto-memory", "kind": "never",
     "rule": "Don't write to `~/.claude/projects/*/memory/MEMORY.md`",
     "pattern": r"file_path=\S*/memory/MEMORY\.md|>\s*\S*/memory/MEMORY\.md", "tool": ["Write", "Edit", *SHELL]},
    # Listing archive/ is allowed: a dropped note needs a free name there (-2, -3). Reading a note in it is not.
    # (a mv into archive/ is the drop itself, so only the Read tool and shell readers count)
    {"id": "never reads a note in the suggestion archive", "kind": "never",
     "rule": "`archive/` holds dropped ones and is never read",
     "pattern": r"skill-suggestions/archive/[^\s/\"']+\.md", "tool": "Read"},
    {"id": "never prints a note in the suggestion archive", "kind": "never",
     "rule": "`archive/` holds dropped ones and is never read",
     "pattern": r"\b(cat|head|tail|sed|less|type|Get-Content)\b[^\n|;&]*skill-suggestions/archive/\S", "tool": SHELL},
]
