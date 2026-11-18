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

That report is written by this test, so the checks it decides alone (its sections and their order, the Left undone
section as the file's text; names in COMPOSED) cannot fail here and print "PASS (composed)"; checks that read the
script's wording can fail and print a plain PASS. What /wiki-report itself writes is graded only by a paid session. The wiki-report skill's own text is
checked directly (every Needs-you wording, the no-file lines, the --brief rule), case A's folder is also graded by the
left-undone-verbatim kind, and its section-against-file checks are shown to fail an invented, a reworded and a dropped
queue line. The left-undone-old-run case is not run here (an unpaid smoke of it was run by hand, checkpoints.md).

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
    "the session did not write left-undone.txt itself",  # reads the session's tool calls: empty here
)
# plan, Testing Decisions common-check table: the branch drops these
DROPPED = {"left-undone-planted": ("no --full-only step ran", "pending queue empty", "triage ran: one log row"),
           "left-undone-clean": ("quick steps all wrote their pair", "triage ran: one log row"),
           "left-undone-verbatim": ("no --full-only step ran", "pending queue empty", "triage ran: one log row")}

# "PASS (composed)" marks a check that cannot fail in grade() whatever the script writes: compose_report decides it
# alone (the report's sections and their order, the Left undone section being the file's own text) or it grades the
# composer itself. A check that reads the script's wording (the 'Left undone: nothing' and 'Left undone line: ...'
# checks, the Numbers row, the Needs-you line, which compose_report words from the file's own lines) can fail here
# and prints a plain PASS. Either way, what /wiki-report itself writes is graded only by a paid session. The
# section-against-file checks bite in tamper_checks, where the report is altered first. Each entry is a name prefix
# of check.py's checks (or of this test's own composer checks), and main() fails a prefix that names no check this run
# emitted; the two section-against-file prefixes are the left-undone-verbatim kind's (eval-case-writer's).
SECTION_EQUALS_FILE = "the section's lines are the file's lines"
NO_FOREIGN_QUEUE_LINE = "no queue line (a line starting '- ') in the section that the file does not hold"
COMPOSED = ("compose_report words", SECTION_EQUALS_FILE, NO_FOREIGN_QUEUE_LINE, "the report has a Left undone section",
            "Left undone is the second-to-last section", "the cycle report's last section is Needs you")
emitted: set[str] = set()  # every check name this run printed, for the COMPOSED prefix check in main()

SKILL_TEXT = REPO / "skills" / "wiki-report" / "SKILL.md"
# the Needs-you wordings and the no-file lines of the wiki-report skill, as the skill text writes them
NEEDS_AWAITING = "<N> semantic lint findings awaiting your approval — <run-folder>/lint-semantic.md"
NEEDS_NO_FIX = ("<N> semantic lint findings, applied or declined not recorded (no fix step in this mode)"
                " — <run-folder>/lint-semantic.md")
NEEDS_NOT_RECORDED = "<N> semantic lint findings, applied or declined not recorded — <run-folder>/lint-semantic.md"
NEEDS_GENERIC = "lint fixes awaiting approval — <run-folder>/lint-semantic.md"
NO_FILE = "Left undone: not checked (no left-undone.txt in the run folder)"
NO_FILE_STANDALONE = "Left undone: not checked (standalone report: no run folder)"

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
        emitted.add(r["name"])
        apart = r["name"].startswith(NEEDS_SESSION)
        passed = "PASS (composed)" if r["name"].startswith(COMPOSED) else "PASS"
        tag = "NEEDS-PAID-SESSION" if apart else (passed if r["ok"] else "FAIL")
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
    emitted.add(name)
    passed = "PASS (composed)" if name.startswith(COMPOSED) else "PASS"
    print(f"  {passed if ok else 'FAIL':18} {name}" + ("" if ok else f"\n{'':21}detail: {detail}"), flush=True)
    if not ok:
        failures.append(f"{label}: {name}  [{detail}]")


def needs_you_wordings(skill: str) -> None:
    """The wiki-report skill text carries each Needs-you wording and each no-file line compose_report writes, and
    compose_report writes each branch from the left-undone.txt line the skill says picks it (no model, no sandbox)."""
    label = "T"
    for name, wording in (("awaiting", NEEDS_AWAITING), ("no fix step", NEEDS_NO_FIX),
                          ("not recorded", NEEDS_NOT_RECORDED), ("generic, no left-undone.txt", NEEDS_GENERIC)):
        own(label, f"wiki-report SKILL.md carries the '{name}' Needs-you wording", f"`{wording}`" in skill, wording)
    for name, line in (("no left-undone.txt", NO_FILE), ("standalone report", NO_FILE_STANDALONE)):
        own(label, f"wiki-report SKILL.md names the '{name}' state's line", f"`{line}`" in skill, line)
    brief = next((l for l in skill.splitlines() if l.startswith("If `--brief`")), "")
    own(label, "the --brief rule prints the no-file state's line when left-undone.txt is absent",
        f"`{NO_FILE}`" in brief and f"`{NO_FILE_STANDALONE}`" in brief, brief[-400:])
    own(label, "wiki-report SKILL.md prints nothing for 0 findings, no semantic lint or an unusable list",
        "Nothing for 0 findings" in skill, "")
    sem = {"awaiting": ("- Semantic findings: 2 — awaiting your approval; the findings are in lint-semantic.md (run x)",
                        NEEDS_AWAITING, "2"),
           "no fix step": ("- Semantic findings: 5 — no fix step in this mode; the findings are in lint-semantic.md",
                           NEEDS_NO_FIX, "5"),
           "not recorded": ("- Semantic findings: 5, not checked (the fix step left no lint-fixes.txt: applied and "
                            "declined were not recorded)", NEEDS_NOT_RECORDED, "5")}
    with tempfile.TemporaryDirectory(prefix="lu-needs-") as td:
        rf = Path(td)
        for name, (line, wording, n) in sem.items():
            (rf / "left-undone.txt").write_text(f"Left undone: 1 queue(s)\n{line}\n", encoding="utf-8")
            tail = compose_report(rf, "x").split("## ⚠️ Needs you")[-1].split()
            want = "- " + wording.replace("<N>", n).replace("<run-folder>", rf.as_posix())
            got = " ".join(tail)
            own(label, f"compose_report words the '{name}' branch as the skill does", got == want, (got, want))
        (rf / "left-undone.txt").write_text("Left undone: nothing\n", encoding="utf-8")
        tail = compose_report(rf, "x").split("## ⚠️ Needs you")[-1].split()
        own(label, "compose_report words 'Nothing.' when the file has no semantic line", tail == ["Nothing."], tail)


def tamper_checks(suite, case, ctx, cid, rf, before) -> None:
    """The left-undone-verbatim checks, run over case A's built folder, must fail a section that is not the file word
    for word: an invented queue line, a reworded line, a dropped line. Each is run through check() and put back."""
    lu = (rf / "left-undone.txt").read_text(encoding="utf-8")
    first = next(l for l in lu.splitlines() if l.startswith("- "))
    base = compose_report(rf, cid)
    needs = "## ⚠️ Needs you"
    variants = {"an invented queue line": base.replace(needs, f"- Invented queue: 9 — not in the file\n\n{needs}", 1),
                "a reworded queue line": base.replace(first, first + " (reworded)", 1),
                "a dropped queue line": base.replace(first + "\n", "", 1)}
    report_path = rf / f"{cid}-run-cycle-report.md"
    try:
        for name, text in variants.items():
            report_path.write_text(text, encoding="utf-8")
            res = suite.check(case, before, before, empty_session(), ctx)
            same = next((r for r in res if r["name"].startswith(SECTION_EQUALS_FILE)), None)
            own("A", f"the section-equals-file check fails {name}", same is not None and not same["ok"],
                "check absent" if same is None else "passed")
            if name == "an invented queue line":
                extra = next((r for r in res if r["name"].startswith(NO_FOREIGN_QUEUE_LINE)), None)
                own("A", "the no-extra-queue-line check fails an invented queue line",
                    extra is not None and not extra["ok"], "check absent" if extra is None else "passed")
    finally:
        report_path.write_text(base, encoding="utf-8")


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


def case_a_expected(cid: str) -> list[str]:
    """left-undone.txt for case A's planted notebook: the plan's Case A list (2 past with refresh.json deliberately
    absent, 1 with no review_after, 1 malformed, the lint's two kinds, 2 of 5 semantic findings awaiting, the four
    sources with 'already covered' left out, the tickets, the staged entry, the checklist), worded as the script words
    them. Written out in full so a changed count or reason fails here, before a paid session."""
    still = "still present after the cycle Step 5 fixes (not approved, declined, or no fix step covers this kind)"
    src = "https://example.com/skilltest/"
    return [
        "Left undone: 15 queue(s)",
        "- Past review_after: 2, not checked (refresh left no refresh.json)",
        "- No review_after: 1 — refresh cannot see an entry with no review_after; add the date (the lint lists them "
        "under Missing lifecycle fields)",
        "- review_after not a date: 1 — refresh cannot read it; correct the date (the lint lists them under Dates not "
        "in ISO form)",
        f"- Lint broken links: 2 — {still}",
        f"- Lint unquoted yaml: 1 — {still}",
        f"- Semantic findings: 2 — awaiting your approval; the findings are in lint-semantic.md (run {cid}); no later "
        "cycle step shows them again",
        f"- Source {src}lu-skipped-page: skipped — near-duplicate of an entry already in the wiki (duplicate gate)",
        f"- Source {src}lu-deferred-page: deferred — worker ran out of its turn budget; deferred to the next run",
        f"- Source {src}lu-failed-page: failed — fetch returned 404 not found",
        f"- Source {src}lu-low-tier-page: skipped — tier LOW: promotional page, not queued",
        "- Tickets in _inbox/pending/: 3 — not triaged: arrived after triage, or triage did not complete",
        "- Tickets in this session's bucket main: 2 — left in the bucket after ingest: dropped, failed, deferred or "
        "not reached",
        "- Other readers' buckets, still to process: security 2, mark 1",
        "- Staged entries: 1 — staged before this run, or held by the checker; /wiki-promote",
        "- Discovery checklists: 1 — still in _inbox/discovered/ (discovery files a processed one in _inbox/done/); "
        "whether it was reviewed is not recorded",
    ]


def grade(suite, case, ctx, cid, rf, label) -> None:
    p = run_script(suite, ctx, "wiki-cycle-scope.py", "--topic", suite.NOTEBOOK, "left-undone", "--run-folder", str(rf))
    own(label, "left-undone exits 0", p.returncode == 0, p.stdout + p.stderr)
    if p.returncode != 0:
        return
    written = (rf / "left-undone.txt").read_text(encoding="utf-8").splitlines()
    print("  left-undone.txt:\n" + "".join(f"      | {l}\n" for l in written), end="", flush=True)
    if case["kind"] == "left-undone-planted":
        want = case_a_expected(cid)
        own(label, "left-undone.txt equals the case-A expected lines", written == want,
            {"missing": [l for l in want if l not in written], "unexpected": [l for l in written if l not in want]})
    (rf / f"{cid}-run-cycle-report.md").write_text(compose_report(rf, cid), encoding="utf-8")
    (rf / f"{cid}-run-cycle-report.json").write_text("{}", encoding="utf-8")
    finish_scratchpad(rf)
    before = suite.snapshot(ctx)
    results = suite.check(case, before, before, empty_session(), ctx)
    report(label, results, case["kind"])
    if case["kind"] == "left-undone-planted":
        verbatim = case_of("left-undone-verbatim")  # the same seeded folder, graded by the section-against-file kind
        report(f"{label} (verbatim)", suite.check(verbatim, before, before, empty_session(), ctx), verbatim["kind"])
        tamper_checks(suite, verbatim, ctx, cid, rf, before)


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
    print("\n=== wiki-report skill text and the composer's Needs-you branches ===", flush=True)
    needs_you_wordings(SKILL_TEXT.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="lu-fixture-") as td:
        tmp = Path(td)
        for name, fn in (("A", case_a), ("B", case_b)):
            t = time.time()
            try:
                fn(suite, tmp)
            except Exception as e:  # deliberately broad: a builder that raises is a result to report, not a crash
                import traceback
                traceback.print_exc()
                failures.append(f"{name}: raised {type(e).__name__}: {e}")
            print(f"\n[{name}] wall {time.time() - t:.0f}s", flush=True)
    print(f"\nwall total {time.time() - t0:.0f}s")
    for prefix in COMPOSED:  # a renamed check must not drop silently out of the composed label
        if not any(n.startswith(prefix) for n in emitted):
            failures.append(f"COMPOSED prefix names no check this run emitted: '{prefix}'")
    if failures:
        print(f"\n{len(failures)} FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nevery check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
