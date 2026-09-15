#!/usr/bin/env python3
"""
run_skill_test.py — the standing test baseline for a shipped skill.

Usage (from the llm-wiki-bootstrap repo root):
  python tests/skills/run_skill_test.py wiki-update                    # every case, Sonnet and Opus
  python tests/skills/run_skill_test.py wiki-update --models sonnet --cases article-cached-direct
  python tests/skills/run_skill_test.py wiki-update --skill-ref HEAD   # the committed skill (old vs new)
  python tests/skills/run_skill_test.py wiki-update --save-baseline    # accept this run as the baseline
  python tests/skills/run_skill_test.py wiki-update --refresh-fixtures # re-fetch the cached sources (live)
  python tests/skills/run_skill_test.py wiki-update --tags complex     # only the cases carrying a tag

What a run does, per model (the models run side by side, each in its own sandbox):
  1. tests/skills/<skill>/check.py builds a fresh sandbox: a throwaway notebook,
     its own registry and its own qmd index. Real notebooks are never touched.
  2. The skill under test is rendered into the sandbox from the working tree (or
     from --skill-ref), with {{WIKI_SCRIPTS_DIR}} pointing at this repo's scripts:
     the run tests the repo's skill and scripts, never the installed copy.
  3. Each case runs as a headless `claude -p` session in the sandbox with only the
     tools the skill needs. Its event stream is kept; the tool calls show which
     steps actually ran.
  4. check.py checks what the session built; the report compares every check with
     the stored baseline (baseline-<model>.json beside cases.json).

Cases tagged "complex" run only when asked for (--tags complex).
Results: tests/skills/.results/<skill>/<stamp>/ (not committed): report.md,
summary.json, and per model and case the event stream and the checks. A model's
sandbox is removed after a clean run and kept after a failure (or with --keep).
The sessions run on the claude.ai login: ANTHROPIC_API_KEY is removed from
their environment. Exit code 0 when every check passed, 1 otherwise.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PLACEHOLDER = "{{WIKI_SCRIPTS_DIR}}"
DEFAULT_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep",
    "Bash(python:*)", "Bash(python3:*)", "Bash(node:*)", "Bash(cd:*)", "Bash(ls:*)",
    "Bash(mv:*)", "Bash(rm:*)", "Bash(mkdir:*)", "Bash(cp:*)", "Bash(cat:*)",
    "Bash(grep:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)", "Bash(find:*)", "Bash(xargs:*)",
    "Bash(sort:*)", "Bash(echo:*)", "Bash(pwd:*)",
]
# Sessions may read (not only run) this repo's scripts: the first smoke run's
# permission denials were all a session looking at _wiki_config.py and
# _entry_checks.py outside the sandbox, friction a normal session does not have.
EXTRA_DIRS = [REPO / "bootstrap" / "scripts"]


def load_check(skill: str):
    path = HERE / skill / "check.py"
    if not path.is_file():
        sys.exit(f"no test suite for {skill}: {path} is missing")
    spec = importlib.util.spec_from_file_location(f"check_{skill.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render_skill(skill: str, ref: str | None, dest: Path) -> Path:
    """Copy the skill folder into dest, {{WIKI_SCRIPTS_DIR}} -> this repo's scripts."""
    scripts = (REPO / "bootstrap" / "scripts").as_posix()
    src_rel = f"bootstrap/skills/{skill}"
    if ref:
        names = subprocess.run(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", ref, src_rel],
                               capture_output=True, text=True, check=True).stdout.split()
        files = {n[len(src_rel) + 1:]: subprocess.run(["git", "-C", str(REPO), "show", f"{ref}:{n}"],
                                                      capture_output=True, check=True).stdout for n in names}
    else:
        root = REPO / src_rel
        files = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    if "SKILL.md" not in files:
        sys.exit(f"{src_rel}/SKILL.md not found" + (f" at {ref}" if ref else ""))
    for rel, data in files.items():
        if rel.startswith("wiki-seed/"):
            continue  # the pack page is written for people, not loaded by the model
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            out.write_text(data.decode("utf-8").replace(PLACEHOLDER, scripts), encoding="utf-8")
        except UnicodeDecodeError:
            out.write_bytes(data)
    return dest


def parse_events(lines: list[str]) -> dict:
    run = {"tool_calls": [], "texts": [], "tool_errors": 0, "result": {}}
    for line in lines:
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(e, dict):
            continue
        kind = e.get("type")
        msg = e.get("message")
        content = msg.get("content") if isinstance(msg, dict) else None  # some events carry a string
        if kind == "assistant" and isinstance(content, list):
            for c in content:
                if c.get("type") == "tool_use":
                    run["tool_calls"].append({"name": c.get("name"), "input": c.get("input") or {}})
                elif c.get("type") == "text":
                    run["texts"].append(c.get("text") or "")
        elif kind == "user" and isinstance(content, list):
            run["tool_errors"] += sum(1 for c in content if isinstance(c, dict)
                                      and c.get("type") == "tool_result" and c.get("is_error"))
        elif kind == "result":
            run["result"] = {k: e.get(k) for k in ("subtype", "is_error", "num_turns", "duration_ms",
                                                   "total_cost_usd", "permission_denials", "result")}
    run["text"] = "\n".join(run["texts"] + [str(run["result"].get("result") or "")])
    return run


def claude_exe() -> str:
    """The claude program itself. On Windows `claude` resolves to npm's claude.cmd, and
    cmd.exe cuts a command line at the first newline and can mangle ( * | in arguments
    (the first smoke run lost everything after the prompt's first line, flags included);
    the shim only starts node_modules/@anthropic-ai/claude-code/bin/claude.exe, so start
    that directly. The prompt goes on stdin, never as an argument."""
    found = shutil.which("claude")
    if found and found.lower().endswith((".cmd", ".bat")):
        exe = Path(found).parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
        if exe.is_file():
            return str(exe)
    return found or "claude"


def run_case(case: dict, model: str, ctx: dict, check, out_dir: Path, tools: list[str], timeout: int) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    env.update(ctx.get("env", {}))
    # tag this case's searches in the search helper's log, so the checks can count them
    caller = f"{env.get('WIKI_QMD_CALLER', 'skilltest')}-{case['id']}"
    env["WIKI_QMD_CALLER"] = caller
    # auto: the permission mode the user's own sessions run in. The first full run used
    # acceptEdits + the allowlist alone, which refused ordinary agent commands (a `for`
    # loop over searches, multi-line commands, a subshell) and so measured the harness,
    # not the skill; auto sends anything the list does not pre-approve to the same
    # safety classifier a real session uses.
    cmd = [claude_exe(), "-p", "--model", model, "--output-format", "stream-json", "--verbose",
           "--permission-mode", "auto", "--add-dir", str(ctx["sandbox"]), *map(str, EXTRA_DIRS),
           "--allowedTools", *tools]
    events_path = out_dir / f"{case['id']}.events.jsonl"
    t0 = time.monotonic()
    stderr = ""
    try:
        with open(events_path, "w", encoding="utf-8") as f:
            p = subprocess.run(cmd, cwd=ctx["project"], env=env, input=check.prompt(case, ctx), stdout=f,
                               stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                               timeout=timeout)
        stderr = p.stderr or ""
    except subprocess.TimeoutExpired:
        stderr = f"timed out after {timeout}s"
    run = parse_events(events_path.read_text(encoding="utf-8", errors="replace").splitlines())
    run["wall_s"] = round(time.monotonic() - t0, 1)
    run["caller"] = caller
    run["stderr_tail"] = stderr[-500:]
    return run


def run_model(model: str, cases: list[dict], args, check, stamp_dir: Path, tools: list[str]) -> dict:
    out_dir = stamp_dir / model
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx = check.setup(model, stamp_dir / f"sandbox-{model}", REPO)
    render_skill(args.skill, args.skill_ref, ctx["skill_dir"])
    results = {}
    for case in cases:
        before = check.snapshot(ctx)
        run = run_case(case, model, ctx, check, out_dir, tools, case.get("timeout", args.timeout))
        after = check.snapshot(ctx)
        checks = check.check(case, before, after, run, ctx)
        rec = {"case": case["id"], "model": model, "passed": all(c["ok"] for c in checks), "checks": checks,
               "turns": run["result"].get("num_turns"), "cost_usd": run["result"].get("total_cost_usd"),
               "wall_s": run["wall_s"], "tool_errors": run["tool_errors"],
               "permission_denials": run["result"].get("permission_denials") or [],
               "stderr_tail": run["stderr_tail"]}
        (out_dir / f"{case['id']}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
        print(f"[{model}] {case['id']}: {'PASS' if rec['passed'] else 'FAIL'} "
              f"({rec['wall_s']:.0f}s, {rec['turns']} turns, ${rec['cost_usd'] or 0:.2f})", flush=True)
        results[case["id"]] = rec
    if all(r["passed"] for r in results.values()) and not args.keep:
        check.teardown(ctx)
    return results


def load_baseline(skill: str, model: str) -> dict | None:
    p = HERE / skill / f"baseline-{model}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def as_baseline(results: dict) -> dict:
    return {cid: {c["name"]: c["ok"] for c in r["checks"]} for cid, r in results.items()}


def write_report(stamp_dir: Path, args, models: list[str], cases: list[dict], results: dict, fixtures: list) -> Path:
    src = f"git {args.skill_ref}" if args.skill_ref else "the working tree"
    lines = [f"# Skill test — {args.skill}", "",
             f"Run `{stamp_dir.name}`; skill from {src}; models: {', '.join(models)}.", "",
             "| Case | " + " | ".join(models) + " |", "|---|" + "---|" * len(models)]
    for case in cases:
        cells = []
        for m in models:
            r = results[m].get(case["id"])
            if not r:
                cells.append("—")
                continue
            fails = sum(not c["ok"] for c in r["checks"])
            cells.append(("PASS" if r["passed"] else f"**FAIL ({fails})**")
                         + f" · {r['turns']} turns · ${r['cost_usd'] or 0:.2f} · {r['wall_s'] / 60:.1f} min")
        lines.append(f"| {case['id']} | " + " | ".join(cells) + " |")
    lines.append("")
    for m in models:
        rs = results[m].values()
        lines.append(f"- **{m}**: {sum(r['passed'] for r in rs)}/{len(rs)} cases passed; "
                     f"${sum(r['cost_usd'] or 0 for r in rs):.2f}; {sum(r['wall_s'] for r in rs) / 60:.0f} min; "
                     f"{sum(r['turns'] or 0 for r in rs)} turns.")
    lines += ["", "## Against the baseline", ""]
    for m in models:
        base = load_baseline(args.skill, m)
        if not base:
            lines.append(f"- **{m}**: no baseline yet (accept a run with `--save-baseline`).")
            continue
        now = as_baseline(results[m])
        lost = [f"{cid}: {n}" for cid, cs in now.items() for n, ok in cs.items() if not ok and base.get(cid, {}).get(n)]
        gained = [f"{cid}: {n}" for cid, cs in now.items() for n, ok in cs.items()
                  if ok and base.get(cid, {}).get(n) is False]
        lines.append(f"- **{m}**: {len(lost)} regressions, {len(gained)} newly passing.")
        lines += [f"  - regressed: {x}" for x in lost] + [f"  - now passing: {x}" for x in gained]
    lines += ["", "## Failed checks", ""]
    for m in models:
        for cid, r in results[m].items():
            for c in r["checks"]:
                if not c["ok"]:
                    lines.append(f"- {m} · {cid} · {c['name']}: {c['detail']}")
            if r["permission_denials"]:
                lines.append(f"- {m} · {cid} · permission denials: {json.dumps(r['permission_denials'])[:300]}")
    if fixtures:
        lines += ["", "## Live fetches (fixture sources)", ""]
        lines += [f"- {f['source']}: {f['status']}" + (f", {f['bytes']:,} bytes" if f.get("bytes") else "")
                  + (f" — {f['detail']}" if f.get("detail") else "") for f in fixtures]
    report = stamp_dir / "report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("skill")
    ap.add_argument("--models", default="sonnet,opus", help="comma-separated model aliases (default sonnet,opus)")
    ap.add_argument("--cases", help="comma-separated case ids (default: every case not tagged complex)")
    ap.add_argument("--tags", help="comma-separated tags; only cases carrying one of them")
    ap.add_argument("--skill-ref", help="test the skill as committed at this git ref (e.g. HEAD)")
    ap.add_argument("--save-baseline", action="store_true", help="store this run as the baseline per model")
    ap.add_argument("--refresh-fixtures", action="store_true", help="re-fetch the cached sources")
    ap.add_argument("--keep", action="store_true", help="keep the sandboxes even after a clean run")
    ap.add_argument("--timeout", type=int, default=1200, help="seconds per case (default 1200)")
    args = ap.parse_args()

    check = load_check(args.skill)
    cases = json.loads((HERE / args.skill / "cases.json").read_text(encoding="utf-8"))["cases"]
    if args.cases:
        wanted = [c.strip() for c in args.cases.split(",")]
        cases = [c for c in cases if c["id"] in wanted]
    elif args.tags:
        tags = {t.strip() for t in args.tags.split(",")}
        cases = [c for c in cases if tags & set(c.get("tags", []))]
    else:
        cases = [c for c in cases if "complex" not in c.get("tags", [])]
    if not cases:
        sys.exit("no cases selected")
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + (f"-{args.skill_ref}" if args.skill_ref else "")
    stamp_dir = HERE / ".results" / args.skill / re.sub(r"[^\w.-]", "_", stamp)
    stamp_dir.mkdir(parents=True)
    print(f"skill test: {args.skill}, {len(cases)} cases x {len(models)} models -> {stamp_dir}", flush=True)

    fixtures = check.prepare_fixtures(REPO, refresh=args.refresh_fixtures)
    for f in fixtures:
        print(f"fixture {f['source']}: {f['status']}", flush=True)
    tools = getattr(check, "ALLOWED_TOOLS", DEFAULT_TOOLS)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(models)) as ex:
        futures = {m: ex.submit(run_model, m, cases, args, check, stamp_dir, tools) for m in models}
        results = {m: f.result() for m, f in futures.items()}

    report = write_report(stamp_dir, args, models, cases, results, fixtures)
    (stamp_dir / "summary.json").write_text(json.dumps(
        {m: {cid: {"passed": r["passed"], "failed": [c["name"] for c in r["checks"] if not c["ok"]],
                   "turns": r["turns"], "cost_usd": r["cost_usd"], "wall_s": r["wall_s"]}
             for cid, r in rs.items()} for m, rs in results.items()}, indent=2), encoding="utf-8")
    if args.save_baseline:
        for m in models:
            (HERE / args.skill / f"baseline-{m}.json").write_text(
                json.dumps(as_baseline(results[m]), indent=2) + "\n", encoding="utf-8")
        print("baseline saved for: " + ", ".join(models))
    ok = all(r["passed"] for rs in results.values() for r in rs.values())
    print(f"{'ALL PASSED' if ok else 'FAILURES'} — report: {report}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
