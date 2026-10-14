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
  python tests/skills/run_skill_test.py wiki-cycle --effort medium     # every session at this effort level
  python tests/skills/run_skill_test.py wiki-update --cases new-case --red-green HEAD   # red on the old, green on the new

What a run does, per model (the models run side by side, each in its own sandbox):
  1. tests/skills/<skill>/check.py builds a fresh sandbox: a throwaway notebook,
     its own registry and its own qmd index. Real notebooks are never touched.
  2. The skill under test is rendered into the sandbox from the working tree (or
     from --skill-ref), with {{WIKI_SCRIPTS_DIR}} pointing at this repo's scripts
     and {{TOOLSET_DIR}} at a global toolset inside the sandbox (this repo's usage
     pages and framework-contract docs, plus any pages the suite puts there): the
     run tests the repo's skill, scripts and docs, never the installed copy.
  3. Each case runs as a headless `claude -p` session in the sandbox with only the
     tools the skill needs. Its event stream is kept; the tool calls show which
     steps actually ran.
  4. check.py checks what the session built; the report compares every check with
     the stored baseline (baseline-<model>.json beside cases.json).

Cases tagged "complex" run only when asked for (--tags complex). A case or a run rule
switched off carries "off_until": "YYYY-MM-DD" (and "off_reason"): it is back on from
that day, and the report lists it either way, so nothing is switched off for good
unseen (task #134). A case that produced no checks fails: a run never says clean when
it checked nothing.

--red-green <ref> (task #134): every selected case runs twice per model, first on an
export of <ref> (its skill AND its scripts, so a change in a script counts), then on
the working tree. A case proves the change only when it fails on the old copy and
passes on the new one; the report says per case and model, and the exit code is 0
only when every case did. Use it on the new or changed cases of a behavioural change.

Every report opens with the same four headings: compared with what, n, cost, and
what the run does not show.

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
TOOLSET_PLACEHOLDER = "{{TOOLSET_DIR}}"
DEFAULT_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep",
    "Bash(python:*)", "Bash(python3:*)", "Bash(uv:*)", "Bash(node:*)", "Bash(cd:*)", "Bash(ls:*)",
    "Bash(mv:*)", "Bash(rm:*)", "Bash(mkdir:*)", "Bash(cp:*)", "Bash(cat:*)",
    "Bash(grep:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)", "Bash(find:*)", "Bash(xargs:*)",
    "Bash(sort:*)", "Bash(echo:*)", "Bash(pwd:*)",
]
# Sessions may read (not only run) this repo's scripts: the first smoke run's
# permission denials were all a session looking at _wiki_config.py and
# _entry_checks.py outside the sandbox, friction a normal session does not have.
EXTRA_DIRS = [REPO / "scripts"]


def load_check(skill: str):
    path = HERE / skill / "check.py"
    if not path.is_file():
        sys.exit(f"no test suite for {skill}: {path} is missing")
    spec = importlib.util.spec_from_file_location(f"check_{skill.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render_skill(skill: str, ref: str | None, dest: Path, replacements: dict | None = None,
                 repo: Path = REPO) -> Path:
    """Copy the skill folder into dest, {{WIKI_SCRIPTS_DIR}} -> the repo's scripts, then
    each of the suite's replacements (e.g. an install path -> its sandbox copy). ``repo``
    is this repo, or an exported old tree for --red-green."""
    scripts = (repo / "scripts").as_posix()
    src_rel = f"skills/{skill}"
    if ref:
        names = subprocess.run(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", ref, src_rel],
                               capture_output=True, text=True, check=True).stdout.split()
        files = {n[len(src_rel) + 1:]: subprocess.run(["git", "-C", str(REPO), "show", f"{ref}:{n}"],
                                                      capture_output=True, check=True).stdout for n in names}
    else:
        root = repo / src_rel
        files = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    if "SKILL.md" not in files:
        sys.exit(f"{src_rel}/SKILL.md not found" + (f" at {ref}" if ref else ""))
    for rel, data in files.items():
        if rel.startswith("wiki-seed/"):
            continue  # the pack page is written for people, not loaded by the model
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = data.decode("utf-8").replace(PLACEHOLDER, scripts)
            for old, new in (replacements or {}).items():
                text = text.replace(old, new)
            out.write_text(text, encoding="utf-8")
        except UnicodeDecodeError:
            out.write_bytes(data)
    return dest


def build_toolset(root: Path, repo: Path = REPO) -> Path:
    """The sandbox's global toolset: the repo's files as an install lays them out (toolset_files()),
    added beside whatever the suite already put there (e.g. another pack's usage pages)."""
    sys.path.insert(0, str(REPO / "scripts"))
    from _install_tooling import toolset_files
    for rel, src in toolset_files(repo).items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, root / rel)
    return root


def export_tree(ref: str, dest: Path) -> Path:
    """The repo as committed at ``ref``, unpacked into dest (--red-green's old copy)."""
    import io
    import tarfile
    data = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", ref],
                          capture_output=True, check=True).stdout
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall(dest, filter="data")
    return dest


def is_off(item: dict, today: str) -> bool:
    """A case or run rule is switched off while ``off_until`` (YYYY-MM-DD) is after today. A
    rule's older ``"in_suite": False`` with no date stays off, and the report lists it as undated."""
    until = str(item.get("off_until") or "")
    if until:
        return until > today
    return item.get("in_suite", True) is False


def select_cases(cases: list[dict], wanted: list[str] | None, tags: set[str] | None, today: str):
    """(selected, switched_off, not_selected). Cases tagged complex run only when asked for; a
    switched-off case runs only when named in --cases."""
    selected, off, skipped = [], [], []
    for c in cases:
        if wanted is not None:
            (selected if c["id"] in wanted else skipped).append(c)
        elif is_off(c, today):
            off.append(c)
        elif tags is not None:
            (selected if tags & set(c.get("tags", [])) else skipped).append(c)
        else:
            (skipped if "complex" in c.get("tags", []) else selected).append(c)
    return selected, off, skipped


def red_green(old: dict, new: dict) -> dict:
    """Per case and model: "red-green" (failed on the old copy, passed on the new), "green-green"
    (passed on the old too: the case does not test the change), "new-fails", or "missing"."""
    out = {}
    for m, rs in new.items():
        for cid, r in rs.items():
            o = (old.get(m) or {}).get(cid)
            if o is None:
                verdict = "missing"
            elif not r["passed"]:
                verdict = "new-fails"
            elif o["passed"]:
                verdict = "green-green"
            else:
                verdict = "red-green"
            out[(cid, m)] = verdict
    return out


def parse_events(lines: list[str]) -> dict:
    # error_texts: tool_use_id -> the refused call's error text, so a suite can tell who
    # refused it (the global read-guard hook, a blocked tool, the auto-mode classifier)
    run = {"tool_calls": [], "texts": [], "tool_errors": 0, "error_texts": {}, "result": {}}
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
                    # id and parent_tool_use_id: a spawned agent's own calls carry the id of the call that
                    # spawned it, so a suite can tell one worker's calls from another's (task #91)
                    run["tool_calls"].append({"name": c.get("name"), "input": c.get("input") or {},
                                              "id": c.get("id"), "parent_tool_use_id": e.get("parent_tool_use_id")})
                elif c.get("type") == "text":
                    run["texts"].append(c.get("text") or "")
        elif kind == "user" and isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("is_error"):
                    run["tool_errors"] += 1
                    body = c.get("content")
                    if isinstance(body, list):
                        body = " ".join(str(b.get("text", "")) for b in body if isinstance(b, dict))
                    run["error_texts"][c.get("tool_use_id")] = str(body or "")[:500]
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
    env.update(case.get("env", {}))  # a case's own setting, e.g. wiki-search's keyword-machine case
    # tag this case's searches in the search helper's log, so the checks can count them
    caller = f"{env.get('WIKI_QMD_CALLER', 'skilltest')}-{case['id']}"
    env["WIKI_QMD_CALLER"] = caller
    # auto: the permission mode the user's own sessions run in. The first full run used
    # acceptEdits + the allowlist alone, which refused ordinary agent commands (a `for`
    # loop over searches, multi-line commands, a subshell) and so measured the harness,
    # not the skill; auto sends anything the list does not pre-approve to the same
    # safety classifier a real session uses.
    cmd = [claude_exe(), "-p", "--model", model, "--output-format", "stream-json", "--verbose",
           "--permission-mode", "auto", "--add-dir", str(ctx["sandbox"]),
           *map(str, EXTRA_DIRS + [Path(ctx["repo_root"]) / "scripts"]),
           "--allowedTools", *tools]
    # Without --effort a session takes the user's effortLevel from settings.json, which the event
    # stream does not record (task #83); a run that compares levels names one.
    if ctx.get("effort"):
        cmd += ["--effort", ctx["effort"]]
    # A suite whose skill calls other skills renders them into the sandbox and blocks
    # the Skill tool, so a /wiki-report or a worker's /wiki-update cannot fall through
    # to the installed copy (which a run must never test).
    denied = getattr(check, "DISALLOWED_TOOLS", [])
    if denied:
        cmd += ["--disallowedTools", *denied]
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


def load_rules(skill: str) -> list[dict]:
    path = HERE / skill / "trajectory_rules.py"
    if not path.is_file():
        return []
    spec = importlib.util.spec_from_file_location(f"rules_{skill.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.RULES)


def trajectory_checks(skill: str, run: dict, today: str) -> list[dict]:
    """The skill's own read-first and never rules, checked on the run (task #99): every case of a
    suite with `<skill>/trajectory_rules.py` gets them, named `run: <rule>`. A rule switched off
    (`off_until` after today, or the older `"in_suite": False`) is scored only by score_trajectory.py,
    until its false alarms are fixed."""
    rules = [r for r in load_rules(skill) if not is_off(r, today)]
    if not rules:
        return []
    sys.path.insert(0, str(HERE))
    import _trajectory
    return _trajectory.check(run, rules)


def run_model(model: str, cases: list[dict], args, check, stamp_dir: Path, tools: list[str],
              repo: Path = REPO, label: str = "") -> dict:
    """Every case on one model. ``repo`` is this repo, or --red-green's export of the old ref
    (``label`` "-old"), whose skill, scripts, agents and docs the sandbox then uses."""
    ref = None if repo != REPO else args.skill_ref
    out_dir = stamp_dir / f"{model}{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx = check.setup(model, stamp_dir / f"sandbox-{model}{label}", repo)
    ctx["effort"] = args.effort
    ctx["repo_root"] = repo
    ctx["toolset"] = Path(ctx.get("toolset") or ctx["sandbox"] / "global-toolset")
    if ctx["toolset"].resolve().is_relative_to(Path(ctx["sandbox"]).resolve()):  # never write outside the sandbox
        build_toolset(ctx["toolset"], repo)
    repl = {TOOLSET_PLACEHOLDER: ctx["toolset"].as_posix(),
            **(check.render_replacements(ctx) if hasattr(check, "render_replacements") else {})}
    render_skill(args.skill, ref, ctx["skill_dir"], repl, repo)
    for extra in getattr(check, "EXTRA_SKILLS", []):  # the skills this one calls, beside it
        render_skill(extra, ref, ctx["skill_dir"].parent / extra, repl, repo)
    results = {}
    for case in cases:
        before = check.snapshot(ctx)
        run = run_case(case, model, ctx, check, out_dir, tools, case.get("timeout", args.timeout))
        after = check.snapshot(ctx)
        checks = check.check(case, before, after, run, ctx)
        checks += trajectory_checks(args.skill, run, args.today)
        if not checks:  # a run never says clean when it checked nothing (task #134)
            checks = [{"name": "the case produced checks", "ok": False,
                       "detail": "check() returned no checks for this case: nothing was checked"}]
        rec = {"case": case["id"], "model": model, "passed": all(c["ok"] for c in checks), "checks": checks,
               "turns": run["result"].get("num_turns"), "cost_usd": run["result"].get("total_cost_usd"),
               "wall_s": run["wall_s"], "tool_errors": run["tool_errors"],
               "permission_denials": run["result"].get("permission_denials") or [],
               "stderr_tail": run["stderr_tail"]}
        (out_dir / f"{case['id']}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
        print(f"[{model}{label}] {case['id']}: {'PASS' if rec['passed'] else 'FAIL'} "
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


def report_header(args, models: list[str], cases: list[dict], results: dict, info: dict) -> list[str]:
    """The four headings every report opens with (task #134, from the Ruflo deep dive: write-ups that
    can be compared): what the run was compared with, n, cost, and what it does not show. The same
    headings are the template for a measurement written by hand (README, Reporting a measurement)."""
    rg = info.get("red_green") or {}
    old = info.get("old") or {}
    if args.red_green:
        compared = (f"Red then green: each case ran on an export of `{args.red_green}` (its skill and scripts), "
                    f"then on {'git ' + args.skill_ref if args.skill_ref else 'the working tree'}.")
    else:
        bases = [m for m in models if load_baseline(args.skill, m)]
        compared = (f"The stored baseline (`baseline-<model>.json`) for {', '.join(bases)}." if bases
                    else "Nothing: no baseline exists for these models yet.")
        missing = [m for m in models if m not in bases]
        if bases and missing:
            compared += f" No baseline for {', '.join(missing)}."
    n_runs = sum(len(rs) for rs in results.values()) + sum(len(rs) for rs in old.values())
    cost = (sum(r["cost_usd"] or 0 for rs in results.values() for r in rs.values())
            + sum(r["cost_usd"] or 0 for rs in old.values() for r in rs.values()))
    minutes = (sum(r["wall_s"] for rs in results.values() for r in rs.values())
               + sum(r["wall_s"] for rs in old.values() for r in rs.values())) / 60
    lines = ["## Compared with", "", compared, "",
             "## n", "",
             f"{len(cases)} case(s) x {len(models)} model(s), one session each"
             + (", on the old copy and on the new" if args.red_green else "") + f": {n_runs} session(s).", "",
             "## Cost", "", f"${cost:.2f} in all, {minutes:.0f} min of sessions.", "",
             "## What this does not show", "",
             "- One session per case and model: a single pass or fail can be noise; a flip needs a rerun before it counts."]
    if info.get("not_selected"):
        lines.append(f"- Cases not run: {', '.join(c['id'] for c in info['not_selected'])}.")
    for c in info.get("off", []):
        lines.append(f"- Case switched off: {c['id']}, until {c.get('off_until') or '(no date: give it one)'}"
                     + (f" ({c['off_reason']})" if c.get("off_reason") else "") + ".")
    for r in info.get("off_rules", []):
        lines.append(f"- Run rule switched off: \"{r['id']}\", until {r.get('off_until') or '(no date: give it one)'}.")
    for c in info.get("back_on", []):
        lines.append(f"- Back on since {c['off_until']} (its switch-off date passed): {c['id']}.")
    for note in info.get("not_covered", []):
        lines.append(f"- {note}")
    if args.red_green and rg:
        weak = sorted({f"{cid} ({m})" for (cid, m), v in rg.items() if v == "green-green"})
        if weak:
            lines.append(f"- Passed on the old copy too, so they do not test this change: {', '.join(weak)}.")
    return lines + [""]


def write_report(stamp_dir: Path, args, models: list[str], cases: list[dict], results: dict, fixtures: list,
                 info: dict | None = None) -> Path:
    info = info or {}
    src = f"git {args.skill_ref}" if args.skill_ref else "the working tree"
    effort = f"effort {args.effort}" if args.effort else "effort from settings.json"
    lines = [f"# Skill test — {args.skill}", "",
             f"Run `{stamp_dir.name}`; skill from {src}; models: {', '.join(models)}; {effort}.", ""]
    lines += report_header(args, models, cases, results, info)
    if info.get("red_green"):
        names = {"red-green": "red then green: proves the change", "green-green": "**passes on the old copy too**",
                 "new-fails": "**fails on the new copy**", "missing": "**no old run**"}
        lines += ["## Red then green", "", "| Case | " + " | ".join(models) + " |", "|---|" + "---|" * len(models)]
        for case in cases:
            cells = []
            for m in models:
                v = info["red_green"].get((case["id"], m), "missing")
                o = (info["old"].get(m) or {}).get(case["id"])
                why = (" (old failed: " + "; ".join(c["name"] for c in o["checks"] if not c["ok"])[:200] + ")"
                       if o and not o["passed"] else "")
                cells.append(names[v] + why)
            lines.append(f"| {case['id']} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## Results", "", "| Case | " + " | ".join(models) + " |", "|---|" + "---|" * len(models)]
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
    ap.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"],
                    help="each session's effort level (default: the user's settings.json)")
    ap.add_argument("--red-green", metavar="REF",
                    help="run each selected case on an export of REF (skill and scripts) first, then on the "
                         "working tree; exit 0 only when every case fails on the old copy and passes on the new")
    args = ap.parse_args()
    args.today = datetime.now().strftime("%Y-%m-%d")

    check = load_check(args.skill)
    suite = json.loads((HERE / args.skill / "cases.json").read_text(encoding="utf-8"))
    wanted = [c.strip() for c in args.cases.split(",")] if args.cases else None
    tags = {t.strip() for t in args.tags.split(",")} if args.tags and not wanted else None
    cases, off, not_selected = select_cases(suite["cases"], wanted, tags, args.today)
    if not cases:
        sys.exit("no cases selected: a run with zero cases checks nothing")  # exit 1, never a clean run
    rules = load_rules(args.skill)
    info = {"off": off, "not_selected": not_selected, "not_covered": suite.get("not_covered", []),
            "off_rules": [r for r in rules if is_off(r, args.today)],
            "back_on": [c for c in suite["cases"] + rules
                        if c.get("off_until") and not is_off(c, args.today)]}
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    stamp = (datetime.now().strftime("%Y%m%d-%H%M%S") + (f"-{args.skill_ref}" if args.skill_ref else "")
             + (f"-red-green-{args.red_green}" if args.red_green else "")
             + (f"-effort-{args.effort}" if args.effort else ""))
    stamp_dir = HERE / ".results" / args.skill / re.sub(r"[^\w.-]", "_", stamp)
    stamp_dir.mkdir(parents=True)
    print(f"skill test: {args.skill}, {len(cases)} cases x {len(models)} models"
          + (f", red then green against {args.red_green}" if args.red_green else "") + f" -> {stamp_dir}", flush=True)

    fixtures = check.prepare_fixtures(REPO, refresh=args.refresh_fixtures)
    for f in fixtures:
        print(f"fixture {f['source']}: {f['status']}", flush=True)
    tools = getattr(check, "ALLOWED_TOOLS", DEFAULT_TOOLS)
    old_repo = export_tree(args.red_green, stamp_dir / "old-tree") if args.red_green else None

    def both(m):  # the old copy first, then the new, each in its own sandbox
        old = run_model(m, cases, args, check, stamp_dir, tools, old_repo, "-old") if old_repo else None
        return old, run_model(m, cases, args, check, stamp_dir, tools)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(models)) as ex:
        futures = {m: ex.submit(both, m) for m in models}
        pairs = {m: f.result() for m, f in futures.items()}
    results = {m: new for m, (_old, new) in pairs.items()}
    if old_repo:
        info["old"] = {m: old for m, (old, _new) in pairs.items()}
        info["red_green"] = red_green(info["old"], results)

    report = write_report(stamp_dir, args, models, cases, results, fixtures, info)
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
    if old_repo:
        ok = all(v == "red-green" for v in info["red_green"].values())
        print(f"{'RED THEN GREEN' if ok else 'NOT RED THEN GREEN'} — report: {report}")
        return 0 if ok else 1
    print(f"{'ALL PASSED' if ok else 'FAILURES'} — report: {report}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
