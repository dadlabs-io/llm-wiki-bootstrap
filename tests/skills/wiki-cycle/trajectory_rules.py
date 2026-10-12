"""wiki-cycle's own read-first and never rules, as run checks (task #99; tests/skills/_trajectory.py).

Each rule quotes the SKILL.md line it tests. The ingest workers' calls are held to wiki-update's
rules (scope "workers"), since each worker "runs the full /wiki-update flow per source".
"""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "wiki_update_trajectory_rules", Path(__file__).resolve().parents[1] / "wiki-update" / "trajectory_rules.py")
_wu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wu)

RULES = [
    {"id": "read reference.md before writing the scratchpad", "kind": "read_before",
     "rule": "Create ... `scratchpad.md` from the template in reference.md",
     "path": r"/wiki-cycle/reference\.md$", "action": r"file_path=\S*scratchpad\.md", "tool": "Write"},
    {"id": "read the ingester config before spawning workers", "kind": "read_before",
     "rule": "Before spawning, read `~/.claude/agents/wiki-ingester-config.json`",
     "path": r"wiki-ingester-config\.json$", "action": r"wiki-ingester|ingest", "tool": ["Agent", "Task"]},
    {"id": "helpers are spawned unnamed", "kind": "never",
     "rule": "spawn every one unnamed",
     "pattern": r"\nname=\S", "tool": ["Agent", "Task"]},
    {"id": "no wake-up or loop scheduled", "kind": "never",
     "rule": "Don't schedule a wake-up or a loop (ScheduleWakeup, `/loop`)",
     "pattern": r".", "tool": ["ScheduleWakeup", "CronCreate"]},
    {"id": "workers never write update.json", "kind": "never", "scope": "workers",
     "rule": "Workers never write `update.json`",
     "pattern": r"file_path=\S*update\.(json|md)\b|>\s*\S*update\.(json|md)\b", "tool": ["Write", "Bash", "PowerShell"]},
    *_wu.rules("workers"),
]
