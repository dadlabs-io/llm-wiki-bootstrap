#!/usr/bin/env python3
"""Score a suite's run rules (`<skill>/trajectory_rules.py`) over its saved runs, at no model cost.

Every suite run keeps each session's event stream under tests/skills/.results/<skill>/<stamp>/<model>/.
This reads them all and says, per rule, how many sessions it applied to and which broke it, so a
rule can be judged against months of real runs before it joins a suite (task #99).

  uv run python tests/skills/score_trajectory.py wiki-update
  uv run python tests/skills/score_trajectory.py wrap-up --since 20261001   # runs from that stamp on
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _trajectory  # noqa: E402
from run_skill_test import parse_events  # noqa: E402


def load_rules(skill: str) -> list[dict]:
    path = HERE / skill / "trajectory_rules.py"
    spec = importlib.util.spec_from_file_location(f"rules_{skill.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.RULES


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("skill")
    ap.add_argument("--since", default="", help="only runs whose stamp sorts at or after this (e.g. 20261001)")
    ap.add_argument("--examples", type=int, default=3, help="breaches shown per rule (default 3)")
    ap.add_argument("--rule", default="", help="only rules whose id contains this")
    ap.add_argument("--width", type=int, default=160, help="characters of each breach shown (default 160)")
    args = ap.parse_args()

    rules = [r for r in load_rules(args.skill) if args.rule in r["id"]]
    root = HERE / ".results" / args.skill
    applied, broke = defaultdict(lambda: defaultdict(int)), defaultdict(list)
    sessions = 0
    for events in sorted(root.glob("*/*/*.events.jsonl")):
        stamp, model, case = events.parts[-3], events.parts[-2], events.name[: -len(".events.jsonl")]
        if stamp < args.since:
            continue
        run = parse_events(events.read_text(encoding="utf-8", errors="replace").splitlines())
        if not run["tool_calls"]:
            continue
        sessions += 1
        for r in _trajectory.check(run, rules):
            applied[r["name"]][model] += 1
            if not r["ok"]:
                broke[r["name"]].append((stamp, model, case, r["detail"]))

    print(f"{args.skill}: {sessions} sessions{' since ' + args.since if args.since else ''}\n")
    for r in rules:
        name = f"run: {r['id']}"
        n = applied.get(name, {})
        if not n:
            print(f"- {r['id']}: never applied\n")
            continue
        bad = broke.get(name, [])
        per_model = ", ".join(f"{m} {sum(1 for b in bad if b[1] == m)}/{c}" for m, c in sorted(n.items()))
        print(f"- {r['id']}: {len(bad)} of {sum(n.values())} broke it ({per_model})")
        for stamp, model, case, detail in bad[-args.examples:]:
            print(f"    {stamp} {model} {case}: {detail[:args.width]}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
