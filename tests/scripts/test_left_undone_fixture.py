#!/usr/bin/env python3
"""The unpaid test of the wiki-cycle suite's two Left undone cases (task #240, plan step 7). Never shipped.

    uv run python tests/scripts/test_left_undone_fixture.py    # exit 0 = every check passed

Builds each case's sandbox with the suite's own `setup` and `prompt()` (needs `qmd` on PATH; the embed takes up to
600 s), then does by script what a paid session would do, and runs the suite's own `check()` over the folder:

- case B (`left-undone-clean`, a `--lint-only` run): the three integration scripts, then the real mechanical lint
  with the sandbox's `ctx["env"]`; asserts `lint-mechanical.json` is `completed` with every finding count 0 (it
  names the `not_checked` reasons when it is `partial`);
- both: `wiki-cycle-scope.py left-undone`, a minimal report composed from `left-undone.txt` (Numbers row by the
  Decisions-needed-11 rule, Left undone verbatim, Needs you last, its semantic line as the wiki-report skill words
  it), the scratchpad's Phase 8 and 9 set to done, then `check()` with an empty session.

Checks that read the model's session (completed, denials, workers spawned, Phase 8 and 9 done) cannot be graded
here: they are listed apart as "needs the paid session" and are not failures. The sandbox is torn down at the end.
The case files are the eval-case-writer's and are read, never edited, by this test.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUITE = REPO / "tests" / "skills" / "wiki-cycle"

# graded by the model's session, so reported apart (their `run` input here is an empty event stream)
NEEDS_SESSION = (
    "session completed",
    "no permission denials",
    "no wiki-ingester spawned",
    "scratchpad: Phase 8 done",
    "scratchpad: Phase 9 done",
    "committed at the end",  # cycle Step 9's commit is the session's
    "nothing left uncommitted",  # the same: only the session commits the integration scripts' and the report's files
)
# plan, Testing Decisions common-check table: the branch drops these
DROPPED = {"left-undone-planted": ("no --full-only step ran", "pending queue empty", "triage ran: one log row"),
           "left-undone-clean": ("quick steps all wrote their pair", "triage ran: one log row")}

failures: list[str] = []


def load_suite():
    spec = importlib.util.spec_from_file_location("check_wiki_cycle", SUITE / "check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def case_of(kind: str) -> dict:
    cases = json.loads((SUITE / "cases.json").read_text(encoding="utf-8"))["cases"]
    return next(c for c in cases if c["kind"] == kind)


def run_script(suite, ctx, name: str, *args: str):
    return suite._script(ctx, name, *args)


def compose_report(rf: Path, cid: str) -> str:
    """The minimal report a /wiki-report run writes from left-undone.txt (wiki-report SKILL.md, the Numbers rule,
    `## Left undone` verbatim, Needs you last with the semantic line worded from the file's own line)."""
    lu = (rf / "left-undone.txt").read_text(encoding="utf-8")
    past = re.search(r"^- Past review_after: (\d+)", lu, re.M)
    stale = past.group(1) if past else "0"
    sem = re.search(r"^- Semantic findings: (\d+)(.*)$", lu, re.M)
    needs = ["Nothing."]
    if sem and int(sem.group(1)) > 0:
        n, rest = sem.group(1), sem.group(2)
        path = f"{rf.as_posix()}/lint-semantic.md"
        if "awaiting your approval" in rest:
            needs = [f"- {n} semantic lint findings awaiting your approval — {path}"]
        elif "no fix step in this mode" in rest:
            needs = [f"- {n} semantic lint findings, applied or declined not recorded (no fix step in this mode) — {path}"]
        else:
            needs = [f"- {n} semantic lint findings, applied or declined not recorded — {path}"]
    parts = [f"# Run cycle report - {cid}", "", "## Numbers", "", "| Metric | Value |", "|---|---|",
             f"| Stale (past review_after) | {stale} |", ""]
    fb = rf / "fallbacks.txt"
    if fb.is_file():
        parts += ["## Fallbacks", "", fb.read_text(encoding="utf-8").rstrip(), ""]
    parts += ["## Left undone", "", lu.rstrip(), "", "## ⚠️ Needs you", "", *needs, ""]
    return "\n".join(parts)


def finish_scratchpad(rf: Path) -> None:
    p = rf / "scratchpad.md"
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"(\*\*Status\*\*:\s*)interrupted", r"\1completed", t, count=1)
    for ph in ("8: Report", "9: Commit"):
        t = re.sub(rf"(### Phase {ph}\n- \*\*Status\*\*: )pending", r"\1done", t)
    p.write_text(t, encoding="utf-8")


def report(label: str, results: list[dict], kind: str) -> None:
    print(f"\n=== {label} ({kind}) ===", flush=True)
    for r in results:
        apart = r["name"].startswith(NEEDS_SESSION)
        tag = "NEEDS-PAID-SESSION" if apart else ("PASS" if r["ok"] else "FAIL")
        if not apart and not r["ok"]:
            failures.append(f"{label}: {r['name']}  [{r['detail']}]")
        print(f"  {tag:18} {r['name']}" + ("" if r["ok"] or apart else f"\n{'':21}detail: {r['detail']}"), flush=True)
    for gone in DROPPED[kind]:
        present = [r["name"] for r in results if r["name"].startswith(gone)]
        ok = not present
        tag = "PASS" if ok else "FAIL"
        if not ok:
            failures.append(f"{label}: the table drops '{gone}' but check() still has {present}")
        print(f"  {tag:18} table: '{gone}' is dropped by the branch", flush=True)


def own(label: str, name: str, ok: bool, detail: object = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL':18} {name}" + ("" if ok else f"\n{'':21}detail: {detail}"), flush=True)
    if not ok:
        failures.append(f"{label}: {name}  [{detail}]")


def build(suite, tmp: Path, kind: str):
    case = case_of(kind)
    ctx = suite.setup("lutest", tmp / kind / "sandbox", REPO)
    ctx["skill_dir"].mkdir(parents=True, exist_ok=True)
    suite.prompt(case, ctx)
    cid = ctx["cycle_id"]
    rf = ctx["notebook"] / "_inbox" / "reports" / cid[:10] / cid
    return case, ctx, cid, rf


def empty_session() -> dict:
    return {"result": {"subtype": "success", "is_error": False, "permission_denials": []}, "tool_calls": [],
            "text": "", "error_texts": {}, "stderr_tail": "", "wall_s": 0}


def grade(suite, case, ctx, cid, rf, label) -> None:
    p = run_script(suite, ctx, "wiki-cycle-scope.py", "--topic", suite.NOTEBOOK, "left-undone", "--run-folder", str(rf))
    own(label, "left-undone exits 0", p.returncode == 0, p.stdout + p.stderr)
    if p.returncode != 0:
        return
    print("  left-undone.txt:\n" + "".join(f"      | {l}\n" for l in (rf / "left-undone.txt").read_text(encoding="utf-8").splitlines()),
          end="", flush=True)
    (rf / f"{cid}-run-cycle-report.md").write_text(compose_report(rf, cid), encoding="utf-8")
    (rf / f"{cid}-run-cycle-report.json").write_text("{}", encoding="utf-8")
    finish_scratchpad(rf)
    before = suite.snapshot(ctx)
    results = suite.check(case, before, before, empty_session(), ctx)
    report(label, results, case["kind"])


def case_a(suite, tmp: Path) -> None:
    case, ctx, cid, rf = build(suite, tmp, "left-undone-planted")
    try:
        print("\n--- case A built: the sandbox holds", sorted(q.name for q in rf.iterdir()), flush=True)
        # the seeded findings must read as findings to the script's own --show (the ids a session would copy)
        p = run_script(suite, ctx, "wiki-cycle-scope.py", "--topic", suite.NOTEBOOK, "lint-fixes", "--run-folder",
                       str(rf), "--show")
        shown = p.stdout.splitlines()
        own("A", "lint-fixes --show prints 5 findings each with category, file and detail",
            p.returncode == 0 and len(shown) == 5 and all(re.match(r"\d+\. \[\w[^\]]*\] \S+ — \S", l) for l in shown),
            shown or p.stderr)
        grade(suite, case, ctx, cid, rf, "A")
    finally:
        suite.teardown(ctx)


def case_b(suite, tmp: Path) -> None:
    case, ctx, cid, rf = build(suite, tmp, "left-undone-clean")
    try:
        rf.mkdir(parents=True, exist_ok=True)
        (rf / "scratchpad.md").write_text(
            f"# Cycle Run — {cid[:10]}\n\n**Status**: completed\n**Started**: {ctx['started']}\n"
            f"**Topic**: {suite.NOTEBOOK}\n**Cycle**: {cid} (--lint-only)\n\n## Run config\n- Mode: --lint-only\n\n"
            f"## Phase log\n\n### Phase 3: Integration scripts, then the mechanical lint\n- **Status**: done\n\n"
            f"### Phase 8: Report\n- **Status**: done\n\n### Phase 9: Commit\n- **Status**: done\n", encoding="utf-8")
        # cycle Step 3, as the skill words it: the three integration scripts, then the lint, once
        for s in ("wiki-reciprocate-backlinks.py", "wiki-index-per-folder.py", "wiki-map-compile.py"):
            p = run_script(suite, ctx, s, "--topic", suite.NOTEBOOK, "--cycle-id", cid, "--run-folder", str(rf))
            own("B", f"{s} exits 0", p.returncode == 0, (p.stdout + p.stderr)[-400:])
        p = run_script(suite, ctx, "wiki-lint-mechanical.py", "--topic", suite.NOTEBOOK, "--cycle-id", cid,
                       "--run-folder", str(rf))
        lj = suite._bl_lint(rf)
        summ = lj.get("summary") or {}
        counts = {k: v for k, v in summ.items() if k not in ("files_scanned", "standalone")
                  and isinstance(v, int) and not isinstance(v, bool)}
        nonzero = {k: v for k, v in counts.items() if v}
        own("B", "premise: the real lint reads completed (exit code and status)",
            lj.get("status") == "completed",
            {"exit": p.returncode, "status": lj.get("status"), "not_checked": lj.get("not_checked"),
             "stderr": p.stderr[-300:]})
        where = {k: v for k, v in lj.items() if k != "summary" and any(n in k for n in nonzero)}
        lr = ctx["notebook"] / "_inbox" / "reports" / "lint-report.md"
        if nonzero and lr.is_file():  # name the pages the lint lists, so a builder gap is found without a rerun
            ls = [l.strip() for l in lr.read_text(encoding="utf-8").splitlines()]
            where["lint-report.md"] = [x for i, l in enumerate(ls) if re.search(r"Missing Frontmatter Fields|Missing tier \(|"
                                       r"Missing confidence \(", l) for x in ls[i:i + 5] if x]
        own("B", "premise: every lint finding count is 0", bool(counts) and not nonzero,
            {"nonzero": nonzero, "where": where, "counts_seen": sorted(counts)})
        grade(suite, case, ctx, cid, rf, "B")
        head = (rf / "left-undone.txt").read_text(encoding="utf-8").splitlines()[:1] \
            if (rf / "left-undone.txt").is_file() else []
        own("B", "left-undone.txt line 1 is 'Left undone: nothing'", head == ["Left undone: nothing"], head)
    finally:
        suite.teardown(ctx)


def main() -> int:
    suite = load_suite()
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="lu-fixture-") as td:
        tmp = Path(td)
        for name, fn in (("A", case_a), ("B", case_b)):
            t = time.time()
            try:
                fn(suite, tmp)
            except Exception as e:  # noqa: BLE001 - a builder that raises is a result to report, not a crash
                import traceback
                traceback.print_exc()
                failures.append(f"{name}: raised {type(e).__name__}: {e}")
            print(f"\n[{name}] wall {time.time() - t:.0f}s", flush=True)
    print(f"\nwall total {time.time() - t0:.0f}s")
    if failures:
        print(f"\n{len(failures)} FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nevery check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
