---
name: verifying-before-done
description: Gates any claim of "done", success, or completion behind fresh, specific evidence — the exact command/check that proves the claim, run fresh, read in full — and applies the same evidentiary bar to a sub-agent's or earlier stage's self-report as to a first-person claim. Use before declaring a pipeline stage, task, or whole change complete or ready to commit. Do not use as a substitute for per-step test-driven checks mid-implementation — this is the final completion gate, not a per-step check.
recommended_agent_type: architect
last_reviewed: 2026-09-23
review_after: 2026-12-13
reviewed_for_model: claude-fable-5-1
---

# Verifying Before Done

## What this does
Gates any claim of "done," success, or completion behind fresh, specific evidence — never accept a
claim (yours, an earlier pipeline stage's, or a sub-agent's self-report) without independently
proving it via the actual command or check that demonstrates it. Also refuses to let one verified
layer imply another — "tests pass" does not prove "the fix is in the diff that will be committed."

## When to use
- Before declaring a pipeline stage, task, or the whole change complete, ready-to-commit, or "done"
- The final gate before finishing-and-committing
- Directly requested: "is this actually done", "verify this works before I say it's finished"

Do NOT use as a substitute for tdd-implementation's own per-step red/green checks — this is
the **final** completion gate, fired once per meaningful completion claim, not on every test run.

## How it works

Low freedom — a fixed, non-negotiable gate.

**The Gate Function** — run before any claim of success, satisfaction, or completion:
1. **IDENTIFY** — name the actual command/check that proves THIS specific claim (the exact test
   suite, build command, or reproduction steps) — not "it should work."
2. **RUN** — execute it fresh and in full. Never reuse a stale prior run's output.
3. **READ** — the full output, not just the exit code or a truncated tail.
4. **VERIFY** — does the output actually confirm the specific claim being made? State the actual
   status either way — a passing build doesn't confirm a bug is fixed unless it's the specific
   reproduction that was failing. A non-zero exit is never re-read as a pass.
5. **ONLY THEN** — make the claim.

**Apply the same evidentiary bar to a sub-agent's or earlier stage's self-report as to a
first-person claim.** "The implementer said it passed" or "the reviewer said it's fine" is not
evidence — check the actual VCS diff, rerun the actual check yourself. Trusting a report without
independently checking it is the single most common way this gate gets skipped.

**Check every layer separately — don't let one imply another.** At minimum, treat these as
separate, independently-verified layers in this pipeline, each reported explicitly (a missing
layer is a gap, never a silent pass):
- Tests pass (the specific proving command, run fresh)
- The fix/change is actually present in the diff that will be committed (not in an untracked file,
  not reverted, not on the wrong branch)
- Code-review findings were actually addressed, not just acknowledged
- **Frozen tests are unmodified.** If a `test-freeze.json` exists for this change (written by
  `tdd-implementation` when each test went red-for-the-right-reason), run
  `python scripts/check-freeze.py <path-to-test-freeze.json>` (bundled with this skill; paths in the
  freeze file resolve from the freeze file's folder or, if not found there, the repo root; `--repo <dir>`
  names it explicitly). It recomputes each entry's SHA-256 — that one test's own source where the entry
  says `hash_of: test` (with, since 2026-09-21, the source of every module-level name that test loads —
  a shared `EXPECTED` constant, a `parametrize` table, a helper assertion — because loosening one of those
  changes what the test asserts while its own body stands still), else the whole file — and exits non-zero
  on any mismatch that has no
  `unfrozen_reason`, printing the offending entries; an `unfrozen_reason` records a deliberate change and
  re-freezes the entry at the new content — it is not a permanent exemption, so the next silent edit still
  fails (2026-09-18). A frozen test **deleted** on purpose, on the user's word, is retired, not left to read as
  lost: `check-freeze.py retire --freeze-file <json> --file <f> --test <name> --reason "<why, on whose word>"`
  keeps the entry with the reason and date, passes it only while the test stays gone, and refuses a test that
  still exists (2026-09-27). The check also fails on an empty freeze file, because a
  check over nothing is not a pass. A match is the specific layer that closes the "the agent edited
  the test instead of fixing the code" loophole — do not accept "tests pass" alone as covering this;
  a test can pass because it's a good implementation *or* because it was quietly weakened, and only
  this check tells them apart. A non-zero exit is a hard fail on this layer, named explicitly — not
  folded into the tests-pass layer, and not waved through because the (modified) test currently
  passes. Paste the script's output as the evidence; do not recompute by hand when the script is
  available. **Check the current change's freeze file, not an archived one**: a freeze file records its
  own change's moment, so only the most recent record is meaningful against HEAD. Re-checking a superseded
  record (`.do-code-change/archive/<date>-<slug>/test-freeze.json`) after later work legitimately touched
  those files is expected to fail and says nothing about the change it recorded; the script names the
  record's date and, for an archived one, says so in its header and its failure line.
- **Every done criterion is pinned by a test that exists today (the coverage map).** One row per
  plan step's "done" criterion (or per requirement, when no plan exists): the rule, the expected
  behaviour including its negative case, the test that pins it, and its status — `existing` (a named
  test in the repo asserts it now, confirmed by reading the test, not by the suite being green),
  `proposed` (recommended, not written), or `none`. A step whose done lists `Expected:` and
  `Failures:` gets one row per bullet, each failure its own row, and each `## Invariants` entry gets a
  row for the test that pins it: a step's success test never stands for its refusal (2026-09-24: the
  only test covered an admin deleting, so removing the admin check left the suite green). Existing is never confused with proposed: a rule
  is not covered until a test actually asserts it. A rule enforced only through an extracted helper
  whose wiring (the route guard, the middleware, the query filter) no test exercises is a *policy
  shadow*: the helper's row may be `existing`, the wiring's row is `none`. A criterion at `none` or
  `proposed` fails this layer unless `plan.md`'s `## Testing Decisions` marked it manual, in which
  case the row says so and the layer names the manual check that was run. Write the map as a table;
  it is the layer's evidence.
- **The bar is unmoved.** If `constraint-driven-development` is installed, run its guard from that
  skill's folder: `python <skills>/constraint-driven-development/scripts/floor-guard.py --base
  <fixed-point>`. Exit `0` passes; exit `1` is a hard fail listing every move that lowered the bar
  (a new suppression, a skipped or deleted test, an assertion removed, a stub, a threshold lowered, a
  new exception); exit `2` means the guard could not check, which is reported as `not checked` — a
  gap, never a pass. A test **file** deleted on the user's word is approved, not argued past:
  `floor-guard.py approve-deletion --record <artifact dir>/floor-approvals.json --file <test file> --reason
  "<why, on whose word>"` (refused while the file exists; 2026-09-28), and when that record exists the guard
  runs with `--approvals <artifact dir>/floor-approvals.json`, which passes only the deletions it names and
  lists each with its reason. If the skill is not installed, the layer is `not checked` and says so. When a
  `CONSTRAINTS.md` exists, every check it names at the task-end cadence is a proving command for the
  tests-pass layer, run fresh like any other.
- **Every file touched is inside the declared scope.** If the run has an artifact directory holding a
  `scope-baseline.json` (written by `tdd-implementation` before its first red, with
  `scripts/scope-guard.py baseline`), run `python scripts/scope-guard.py check --artifact-dir <dir>`
  (bundled with this skill). It diffs the tree name-only against the baseline object captured when
  implement started — uncommitted changes, files committed since, and every untracked file that is new
  or was edited, leaving out `.do-code-change/` (the run's own notes, committed as the change goes) —
  and fails on any file outside `plan.md`'s `## Scope` globs (one per bullet: the backticked span when
  the bullet has one, else its first word, so a note after the path is fine). Exit `0` passes; exit `1`
  is a hard fail listing every out-of-scope file, each a finding to explain (revert it, or extend the
  plan's scope out loud), never just delete; exit `2` means it could not check (no baseline, no scope
  declared, nothing touched since the baseline), reported as `not checked` — a gap, never a pass. A file
  touched and reverted mid-run, or written beside the change, is exactly what this layer sees and the
  diff-contains-fix layer does not; a scope declared with no check is prose. Without an artifact
  directory the layer is `not checked` and says so.

**Write the per-layer report to `verification-result.md`** in the artifact directory whenever the run
has one (`.do-code-change/<slug>/`, or a directory the caller names): one line per layer in a fixed
shape, `<layer>: PASS | FAIL | not checked — <evidence>`. For a scripted layer the evidence is the
script's exit code and its own verdict line copied word for word, e.g. `frozen tests: PASS —
check-freeze.py exit 0, "frozen-tests layer: PASS — 9 entries checked, all match"`. A paraphrase in place
of the verdict ("9/9 match, unmodified") is not a verdict: the gate and a later reader must not have to
interpret it. The consuming gate reads that file, not the transcript; a report that exists only in the
answer is a claim the next stage cannot check.

**A scripted layer's verdict is the script's exit code, never your reading of it.** Exit 0 is PASS,
exit 1 is FAIL, exit 2 is `not checked` — including when you are sure the change is right and the tool
is being too strict. An exception the user approved (a suppression they accepted, a file they agreed to
touch) is written as a **named FAIL with the approval beside it** — who approved what, where it is
recorded — never as PASS. The gate downstream decides what an approved FAIL means; the report never
decides it for the gate. If you believe the tool itself is wrong (a parsing bug), the layer is still
FAIL, and the suspected bug is a finding named beside it.

**Watch for soft-hedge language as violations, not near-misses** — "should work now," "I'm
confident," "looks correct" are completion claims without evidence; the rule catches paraphrases
and implications, not just the literal words "it's done."

If any step or layer fails, name exactly which one failed and stop — don't proceed to
finishing-and-committing with a caveat instead.

## Known limitation
This gate is, like every skill, **entirely prompt/discipline-based** — nothing here technically
forces itself to run. A skill is advisory: it fires when the model reaches for it, and it cannot
enforce a guarantee (that's what a hook/permission-gate is for). Whether this pipeline's completion
gate should eventually move from a skill (advisory) to a hook (structural) is an open question, not
resolved here — flagged rather than overselling what a skill can guarantee. The shape it would take
exists: Anthropic's security-guidance plugin runs its final review as a `Stop` hook that diffs the
turn against a baseline captured at prompt time, re-wakes the model with findings in the background,
caps itself at three firings per turn with a time-to-live, fails open with a recorded skip reason,
and tags every injected line with its provenance — a re-wake hook, the second hook shape beside the
refusing hook.

**Should this be user-invoked instead of model-invoked?** It gates a high-stakes transition (the
pipeline's last chance before committing), which argues for a human deliberately triggering it
rather than trusting the model to remember to. Defaulted to model-invoked here (matches its
reached-for-automatically role in the pipeline) — flagging this as a real judgment call, not a
silent default.

## Examples

**Input:** An implementer claims "the CSV export feature is done."

**Output (gate applied):**
```
1. IDENTIFY: `dotnet test --filter CsvExport` proves the feature-level claim;
             `git diff --staged` proves the diff-contains-fix claim;
             test-freeze.json lists 3 frozen tests to re-hash
2. RUN: all three, fresh
3. READ: test output — 4/4 passing; diff — confirms CsvExportService.cs and CsvFormatter.cs staged;
         re-hashed frozen tests — all 3 match their recorded hash
4. VERIFY: tests confirm the specific CSV behavior (not just "no errors"); diff confirms the actual
           fix is what's about to be committed, not left in an untracked file; no frozen test was
           silently edited to get there; the coverage map shows each of the plan's 3 done criteria
           pinned by a named existing test (the negative case for the delimiter included); the
           floor guard exits 0 against the fixed point; the scope guard exits 0 — the three files
           touched since implement started all sit under the plan's `src/reports/**` and `tests/**`
5. CLAIM: "CSV export is done — 4/4 tests pass (fresh run), the fix is staged for commit, all
          3 frozen tests are unmodified, every done criterion has an existing test, the bar is
          unmoved, and nothing was touched outside the declared scope." (written to
          `verification-result.md` beside the other artifacts)
```

---

**Input:** A review sub-agent reports "no issues found, looks good to merge."

**Output:** Does not accept this at face value — re-reads the actual review-findings output,
confirms no unresolved critical/important findings remain, and only then proceeds.

## Enforcement
Every hard rule above, once, with what makes a violation fail rather than merely discouraged:
- "Never accept a claim (yours, a stage's, a sub-agent's) without running the proving check
  yourself" → `prose` — this gate is itself advisory (see Known limitation); the eval case
  `stale-claim-reruns` checks the transcript for the fresh run.
- "Never reuse a stale prior run's output; read the full output" → `prose` — freshness is
  a property of the transcript, which no script in the skill can inspect; the eval grader reads it.
- "Check every layer separately; a missing layer is a gap, never a silent pass" → `prose` — the
  per-layer report shape is the only carrier; the eval case `all-layers-pass-claims` greps it.
- "A frozen test modified with no `unfrozen_reason` is a hard fail on its own layer, and a module-level
  value it asserts against counts as part of it" → `script` — `scripts/check-freeze.py` exits non-zero on
  the mismatch and on an empty freeze file, and its fingerprint covers the names the test loads; the eval
  case `frozen-test-modified-fails` replays it, and the script's self-test covers the loosened constant,
  the loosened `parametrize` table and the helper's own constant (floor 45).
- "A frozen test deleted on purpose is retired with a reason; a retirement never covers a live test" →
  `script` — `check-freeze.py retire` refuses a test that still exists (exit 1) and a missing reason (exit 2);
  the check fails a retired test that exists again and reads a file whose every entry is retired as `not
  checked` (exit 2); the self-test replays each (task 89).
- "Check the current change's freeze file, not an archived one" → `script` — the check names the record's
  date and announces an archived record in its header and its failure line, so a superseded record cannot
  read as broken frozen tests; `prose` for choosing which file to run it on.
- "If any layer fails, name it and stop; never proceed to finishing with a caveat" → `prose` — the
  consuming workflow's Pre-finish gate reads `verification-result.md` and refuses anything but PASS on
  every layer.
- "Existing is never confused with proposed; a criterion with no existing test fails the coverage
  layer unless the plan marked it manual" → `prose` — the map's status column is the carrier; the eval
  case `coverage-map-names-untested-criterion` greps it.
- "A move that lowers the bar fails the layer; a guard that could not run is `not checked`, never a
  pass" → `script` — `constraint-driven-development`'s `floor-guard.py` exits 1 on a violation and 2
  when it cannot check; the eval case `floor-guard-catches-suppression` replays exit 1. A test file deleted
  on the user's word passes only through `floor-guard.py approve-deletion` and `--approvals`, whose
  refusals (a file that still exists, a blank reason, an unreadable record) floor-guard's self-test replays
  (task 90).
- "A file touched outside the declared scope fails the layer; a guard that could not run is `not
  checked`, never a pass; a stray file is a finding, never just deleted" → `script` —
  `scripts/scope-guard.py check` exits 1 on an out-of-scope file and 2 when it cannot check (no
  baseline, no scope, nothing touched); the eval case `scope-guard-catches-stray-file` replays exit 1.
- "A scripted layer's verdict is its exit code; an approved exception is a named FAIL, never PASS" →
  `prose` for the report's wording, backed at the gate: do-code-change's Pre-finish reads PASS as the
  script's exit 0; the eval case `approved-exception-stays-fail` replays floor-guard's exit 1 on a
  suppression the user approved and grades the written report with a checker script.
- "Each layer line has the fixed shape; a scripted layer names its exit code and copies its verdict line"
  → `prose` for the wording; do-code-change's `verify` hand-off link grades the written file with a
  checker script that fails a frozen-tests line carrying neither the verdict line nor the exit code.
- "The per-layer report is written to `verification-result.md` when an artifact directory exists" →
  `prose` — the consuming workflow's Pre-finish gate reads the file and fails closed when it is
  missing; the eval case `scope-guard-catches-stray-file` grades the file.
- "Soft-hedge language is a violation, not a near-miss" → `prose` — a reading rule; no script parses
  hedges.

## Gotchas
- **Two exit 1s written up as PASS "by reasoning"** (investment-agent, 2026-09-22). At a legislators-ingest
  verify the architect ran scope-guard (exit 1: a declared `CONSTRAINTS.md` read as out of scope, a real
  parsing bug since fixed) and floor-guard (exit 1: an exception the user had approved) and recorded both
  layers as PASS, having reasoned each failure away. Both reasons were plausible, which is the danger: the
  report then said nothing a later reader could check. Their own correction is the rule now — the tool's
  verdict goes in the report, the approval or the suspected tool bug goes beside it.
- **A Scope bullet's note became part of its glob** (investment-agent, 2026-09-22). `scope-guard.py` kept
  only a bullet's first word when that word held a `/`, so `` `CONSTRAINTS.md` — added for one edit only ``
  became one glob of the whole line and the declared file read as out of scope. Fix: the backticked span,
  else the first word, slash or not. The same pass found `- **/*.py` losing its leading `**` to the
  bullet-marker strip.
- **A superseded freeze record read as 45 broken frozen tests** (investment-agent, 2026-09-20). Told to
  re-check their frozen tests after a re-promote, they ran the layer over every archived freeze file. The
  current record passed 90/90; the archived `house-fetcher` one failed **45 of 45**, every entry, for one
  honest reason — a later change appended tests to those files. Nothing was wrong, and the script's own
  per-entry message said so, but the headline read as a breach. Fix: a freeze file records its own
  change's moment, so only the most recent record is meaningful against HEAD; the script now prints the
  record's date, names an archived record as superseded in its header, and repeats the rule in the failure
  line. Check the current change's freeze file; read an archived one as history.
- **The per-test hash could not see what the test asserts against** (investment-agent, 2026-09-21). Their
  `test_legislators_store.py` asserts `tables == EXPECTED_TABLES`, a module-level list; a step added names
  to it and every entry still reported "matches frozen hash", because the fingerprint covered the function
  body alone. Harmless there, but *removing* a name — or loosening any shared expected value, a
  `parametrize` table, or a helper's assertion — passed the layer silently: exactly the weakening this
  layer exists to catch. Fix: the fingerprint now folds in the source of every module-level name the test
  loads, transitively, under a versioned `hash_scope` so older records keep their own meaning.
- **A layer's verdict paraphrased away** (do-code-change's verify link, 2026-09-24, 1 run of 3). The report
  wrote the frozen-tests layer as "`check-freeze.py` → 9/9 match, unmodified": true, but with no PASS,
  no FAIL and no exit code, so the link's grader (and a gate reading the file) had nothing to read. The
  other two runs wrote PASS. Fix: the fixed line shape above, with the script's exit code and its own
  verdict line copied word for word.
- **A test deleted on the owner's word read as a lost test** (investment-agent, 2026-09-27). Mark had a dead
  command deleted with its tests mid-run; three of them were frozen, and the layer failed "listed file not
  found" with no honest way out: an unfreeze needs the file, and the freeze file is never hand-edited. Fix:
  `check-freeze.py retire`, which records the deletion and its reason and still fails if the test comes back.
- No real-run gotchas logged yet for the other layers — fill in as verification sessions surface repeat
  failures (e.g. a proving command that passed but didn't actually exercise the changed code path, or a
  diff-contains-the-fix check skipped because passing tests alone felt sufficient).

**Rationalizations to reject** (the gate is low-freedom; each of these is a must-not eval case):
- *"The tests passed earlier in this session, no need to run them again."* Earlier is stale: the diff
  moved since. RUN means fresh.
- *"The implementer (or the review sub-agent) said it passed."* A report is a claim; the same
  evidentiary bar applies to a sub-agent's self-report as to your own. Check the diff, run the check.
- *"The fix is obviously in the diff, I wrote it."* Recollection is not the diff. Untracked files,
  the wrong branch, and a silent revert all pass this rationalization and fail the layer.
- *"The frozen test passes now, so the hash mismatch doesn't matter."* A weakened test passes by
  construction; the mismatch is the finding, and the passing run is the symptom.
- *"The guard exited 1, but the user approved this / the guard is wrong here, so the layer passes."*
  The layer is FAIL; the approval or the suspected bug is written beside it. The gate, not the report,
  decides what an approved FAIL means.

## Scripts
- Run `scripts/check-freeze.py <test-freeze.json>` to check the frozen-tests layer (execute, do not
  reason about it by hand). Stdlib-only Python 3.8+; exits 0 only when every listed file matches its
  recorded SHA-256; exits 1 on a mismatch, 2 on an empty, missing, or
  unreadable freeze file (a check over nothing is a failure, not a pass). `tdd-implementation` writes
  each entry through this script's own `freeze` command (`freeze --freeze-file <json> --file <test file>
  --test <name> --step <n> [--unfrozen-reason "…"]`), so writer and checker cannot drift: for a Python
  test the hash covers that test's source plus the source of every module-level name it loads,
  transitively (`hash_scope: test+module`), which is what lets a later step append its test to the same
  file without breaking an earlier freeze (2026-09-17, found by do-code-change's hand-off chain) while
  still catching a shared expected value being loosened (2026-09-21, investment-agent); elsewhere it falls
  back to the whole file. The scope is versioned per entry: an entry recorded before that widening carries
  no `hash_scope` and is still verified the old way, so archived records do not all read as edited.
  Each run prints the record's own date, and an archived record under an `archive/` folder is announced as
  superseded — a failure there is expected once later work touched those files. An older freeze file with no `hash_of` is checked as a
  whole-file digest exactly as before — except that a file differing from its record only in line endings
  still matches, since git's `core.autocrlf` rewrites a checkout and this layer used to read that as an edit
  (investment-agent, 2026-09-17: two untouched files with one commit each failed it) — and one whose `hash`
  is not a 64-hex digest is reported as unverifiable, which is a failure of this layer, not a pass. Its
  `retire` command (`--freeze-file --file --test --reason`) marks a frozen test deleted on purpose; the entry
  keeps its hash and gains `retired: {reason, date}`.
- Run `scripts/scope-guard.py check --artifact-dir <dir>` to check the in-scope layer (execute; the
  touched set is computed from git, never from memory). Stdlib-only Python 3.8+. Its `baseline`
  command is run by `tdd-implementation` at the start of implement and writes `scope-baseline.json`:
  the `git stash create` object (HEAD plus every uncommitted change, the stash list untouched), HEAD,
  and an untracked-file snapshot with mtimes, capped at 2,000 entries. `check` reads `## Scope` from
  `<dir>/plan.md` (or `--plan`), takes extra globs with `--allow`, exempts the artifact directory
  itself, and reports past `--max-files` (200) rather than truncating silently. A scope that is only
  `**` declares nothing and exits 2. Each `## Scope` bullet yields one glob: its backticked span, else
  its first word, so a trailing note never joins the glob; a path with a space is backticked.
  `--self-test` proves every rule on a fixture (floor 29).

## Composition
- **Invocation class:** model-invoked discipline — reached for automatically before any completion
  claim, though see "Should this be user-invoked instead?" above.
- **Dependencies:** consumes the outputs of reviewing-code (and any earlier stage's claims) as
  things to independently re-verify, not trust; also consumes `test-freeze.json` and
  `scope-baseline.json` (both from tdd-implementation) if they exist for this change, and `plan.md`'s
  steps, Testing Decisions, and Scope for the coverage map and the in-scope layer. Runs
  `constraint-driven-development`'s `floor-guard.py` when that skill is installed alongside (the
  bar-unmoved layer reads `not checked` otherwise). Its pass/fail determination gates whether
  finishing-and-committing proceeds.
- **Lifecycle:** encoded-preference for the gate's existence and shape; but this skill's own
  prompt-only enforcement is itself a capability-uplift-flavored limitation worth revisiting — if
  this pipeline ever needs the guarantee to be structural rather than advisory, that's a
  hook/permission-gate decision, not a rewrite of this skill's prose.
