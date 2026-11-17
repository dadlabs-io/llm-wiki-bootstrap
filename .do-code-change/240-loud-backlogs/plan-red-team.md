# Red-team: plan.md revision 4 (240-loud-backlogs, round 5)

Written by the orchestrator from the red-team's report. The red-team was a fresh architect running strategy-red-team, with one red-team-reviewer (haiku) spawn. The readonly-guard check passed (641 files, HEAD unchanged). Rounds 1-4 are in plan-red-team-round1..4.md.

What the architect read:
- the plan, the requirements, the checkpoints and the round-4 report;
- the text of the wiki-cycle, wiki-report and wiki-discover skills, and reference.md;
- check.py 60-250, 471-520, 779-840, 2223-2330 and 2529-2860;
- wiki-lint-mechanical.py, wiki-feeds.py `known`, and tests/skills/README.md.

It also checked the live agentic-design run folders and ran the real lint on a scratchpad copy of the test seed. No repo file was written.

## Round-4 kill-assumptions: resolved, or turned into a Decision?
- **KA1 (third state):** resolved in the design. It will fire often (rank 5). The fix-step lines still have one unstated case (rank 3).
- **KA2 (mode read from free text):** mostly resolved. No reader or eval parses the `**Cycle**` line today (check.py:2201 and the fixtures only write it). Two wording gaps remain (minor list).
- **KA3:** partly resolved. `--show` and the existence guard work. Decision 10's recommended form has a silent-drop flaw (rank 2).
- **KA4:** resolved.
- **KA5:** partly resolved.
  - The Needs-you rewording regresses (rank 1).
  - The Numbers row and `--brief` have no value when line 1 is `not checked` (rank 4).
- **KA6:** resolved in the table. B's fixture has a new gap (rank 3).
- **KA7:** resolved. A silent miss remains when the flag is unrecorded. Decision 2 discloses it, so it is a choice (rank 6).
- **KA8:** now Decision 12.

## Kill-assumptions (ranked)

### 1. The "awaiting approval" line vanishes from Needs you exactly when the model skips a command
Plan line 82 says that when the semantic line reads `not checked`, Needs you prints nothing. The semantic line reads `not checked` when lint-fixes.txt is absent (line 56).

**Fails if:**
- Step 5 skips the new `lint-fixes` command. The scope script's own docstring records a model skipping a sentence in 21 of 22 runs (wiki-cycle-scope.py:58).
- Left undone then prints `Semantic findings: 193, not checked`, and Needs you prints nothing. Today's "lint fixes awaiting approval" line is lost, which contradicts the invariant at plan line 166. The likeliest case is an unattended `--full` run.

**Kill criterion:** findings in lint-semantic.json and no Needs-you line about them.

**Cheapest test:** a `--full` fixture with 5 findings and no lint-fixes.txt must keep a Needs-you line.

**Fix class:** plan error. When the semantic lint ran and found something, Needs you keeps a line:
- `<N> semantic lint findings awaiting your approval`, or
- `<N> semantic lint findings, applied or declined not recorded — <path>`.

It prints nothing only for 0 findings or no lint.

### 2. False statements in the semantic lines: the way out, and what clears a standing backlog
**Fails if (way out):** Step 4's scope is "added or revised since the last semantic lint" (SKILL.md:152), and Step 5 shows only this run's findings. A later `--full` never re-presents an earlier run's findings. So "/wiki-cycle --full applies approved ones" (line 74) and "(approve them in a --full run)" (line 82) promise something no step does.

**Fails if (what clears it):** Decision 10 reads only the newest completed lint-semantic.json (line 57). Once a later run lints one new entry, the older run's unresolved findings leave Left undone without a word. A `--full` doesn't clear them; it silently supersedes them.

**Cheapest test:** run A has 5 unresolved findings and a newer run B has 0. The output must say it reads the newest lint only.

**Fix class:**
- Plan error: true way-out text, e.g. "findings are in lint-semantic.md; no cycle step re-presents them outside the run that found them". Drop "(approve them in a --full run)".
- Choice for Mark: restate Decision 10 as either "newest lint only, labelled `from <id>; older lints are not read`" or "read every completed lint back to the last fully answered one".

### 3. Case B ("Left undone: nothing") cannot pass as planned
**Fails if:**
- **The seed isn't lint-clean.** The real lint on the `_seed()` notebook (fixtures/seed-notebook plus extra-seed, run on a scratchpad copy) gives:
  - orphans 6;
  - missing_frontmatter 1, missing_tier 1, missing_confidence 1;
  - backlink_blocks_out_of_step 6;
  - status partial, because the copy had no qmd collection.

  All 12 seed entries also have review_after dates in 2026-04 or 2026-05.
- B's earlier lint must hold zero findings, or else carry a lint-fixes.txt. Otherwise Decision 10 prints a semantic line.
- The unpaid test runs no model, so it has no lint JSON unless it runs the lint script. That gives the third state, not `nothing`. A partial lint also never gives `nothing`.

**Kill criterion:** the real lint on B's built notebook returns `partial` or any count above 0.

**Cheapest test:** build B with the suite's own setup and prepare function, run the real lint, and read lint-mechanical.json.

**Fix class:** plan error.
- B's builder repairs or replaces the defective seed entries.
- The earlier lint holds zero findings.
- The unpaid test runs the real lint, and the plan states the qmd and installed-skills conditions for `status: completed`.

### 4. The output is undefined or conflicting when line 1 is `not checked`
**Fails if:**
- The whole-file mismatch case (line 37) has no queue lines and no past line, so the Numbers row (line 44) has no N.
- Line 37 drops the disk-state counts, while lines 35 and 39 keep them: two behaviours for one situation.
- `Left undone: nothing` has no past line either, and the plan doesn't say that means 0.

**Kill criterion:** the Numbers stale row has no defined source.

**Fix class:** plan error.
- On a mismatch, write the disk-state counts, with the reason only on the mode-dependent lines.
- With no past line and a line 1 that isn't `not checked`, the Numbers row reads 0. Otherwise it reads `not checked`.

### 5. The third state will fire constantly for pending tickets
**Fails if:** only 3 of 32 live run folders have triage.json (2026-10-11-01, 2026-10-12-02, 2026-10-30-01). The newest `--ingest-only` run (2026-11-10-01) has none. The pending line would then read `not checked` almost every time, although the ticket count is certain. Triage moves every ticket out of pending/, so a ticket still there after a triaging mode was never triaged or arrived later.

**Fix class:** plan error, in the wording. The pending line doesn't need the JSON: `not triaged: <N> arrived after triage or triage did not run`.

### 6. The tier-4 line is silent when the flag isn't recorded
**Fails if:** an unattended run defers tier-4 sources without writing `--no-confirm-discovery` into the scratchpad. Nothing is named and nothing says `not checked`, against requirements lines 18 and 20. Zero of 32 live scratchpads record the flag.

**Fix class:** choice (Decision 2). Decision 2 should say plainly that the miss is silent.

### 7. Step 1 is too large, and its done criteria miss the report side
**Fails if:** Step 1 builds the subcommand, the header, the mode and modifiers, the mode table with its cross-check and drift test, the third state, the report section, the Numbers rule, `--brief`, the reference.md line and the Step 8 call. Its done-when (lines 253-256) holds only script checks, and the report side is manual until Step 6's paid run.

**Fix class:** plan error. Split it:
- **1a, the script, unit-tested:** subcommand, header, mode and modifiers, table, cross-check, drift test, review-date lines, third state.
- **1b, the prose, with its manual-read criterion named:** wiki-report section, Numbers rule, `--brief`, Step 8 call, reference line.

Renumber the steps, the Part lists and the "blocked by" lines.

## Minor: fixable during implementation without re-planning
- **"First token of the `**Cycle**` text":** say "first token inside the parentheses".
- **Mode names:** strip backticks and quotes, and accept dashless names for all nine modes (e.g. `(lint-only)`).
- **`lint-fixes` with no lint-semantic.json** (Step 4 skipped within 24 hours): write empty lists and exit 0.
- **Mechanical-lint reason in `--full` with no lint-fixes.txt:** follow the third state explicitly.
- **Header's `N queue(s)`:** say whether `not checked` lines count.
- **`standalone` excluded from the lint kinds:** state why in the docstring. It lists declared-standalone pages, not findings.
- **`--report-only` counts disk-state queues fresh:** say so in the section's text (requirements line 75).

## What holds up
- The mode cross-check table and its drift test, which match SKILL.md:28-45.
- Leaving cmd_retry_list alone.
- check.py:
  - the citations (2704-2790), with the kind-gated row right;
  - the `res[:]` precedent (`_check_unfinished`, 2232);
  - B as the first `--lint-only` case.
- Section order: the Fallbacks and ordering checks still hold (2540, 2548-2552, 2629, 2757).
- The covered-set rule and the labelled same-day under-count.
- `known` reads the notebook, so `mark-seen` doesn't hide a tier-4 URL.
- The lint JSON timestamp is tz-aware (`now_stamp()`), so the guard's comparison is sound.
- The tier-4 gate on this run's discover.json.

## Skip, drop, exempt and default rules changed in revision 4
**Hold:**
- An unreadable mode reads `not checked` and keeps the disk counts (apart from the line 37 conflict, rank 4).
- The tier-4 gate.
- `--brief` always prints line 1, even `nothing`. That differs from the Fallbacks precedent but follows requirements line 18.
- No full suite (Decision 4).
- Staged entries named only when the setting is false: with `true`, Needs you names them.

**Conflict:** Needs you prints nothing for 0 or `not checked` (rank 1).

**No standing rule found:**
- the `--today` default;
- the `not checked` and `(no reason recorded)` defaults;
- the regex fallback not exercised;
- the drift test covering 5 of 9 modes;
- a missing bucket folder counting 0;
- `standalone` excluded.

## Complete enough to build?
Not yet, but it is one revision away.
- **Plan errors (none needs Mark):** ranks 1, 2 (the text), 3, 4, 5 (the wording) and 7, plus the minor list.
- **Choices for Mark:**
  - Decision 10, restated truthfully (rank 2);
  - Decision 2's silent-miss wording (rank 6);
  - the other ten Decisions, as written.
- **Settle before building:** ranks 1, 2 and 4, which would print a false or silent line, and rank 3, which means case B can't pass.

## Could not assess
- Whether the session resumes at Step 8 (needs the first paid session).
- Whether the sandbox lint returns `completed` for B (the scratch copy had no qmd collection).
- The live counts at plan lines 90-91 and 130.
- How often models record `--no-confirm-discovery`.
- How the Numbers row and `--brief` render.
- check.py past 3113, and test_wiki_triage.py past 277.
- That wiki-update sets last_reviewed on new entries (the reviewer's claim, unverified).

VERDICT: KILL-ASSUMPTIONS FOUND
