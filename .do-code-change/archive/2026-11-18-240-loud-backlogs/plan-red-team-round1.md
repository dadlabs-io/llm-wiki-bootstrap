# Red-team: plan.md (240-loud-backlogs, round 1)

Written by the orchestrator from the red-team's report (fresh architect, strategy-red-team, one red-team-reviewer spawn). readonly-guard check: PASS (638 files, HEAD unchanged). Neither the architect nor the reviewer read check.py in full: the architect read lines 2223-2760 plus greps, the reviewer about 100 lines.

## Kill-assumptions (ranked)

### 1. The counter reports nothing after a `--full` run ("count equals what the step would read")
**Fails if:** after a `--full` run the counter reports "not semantically linted" or "no claims" entries the run covered. Four mechanisms:
- `added_since` counts git-added and untracked files (`wiki-cycle-scope.py:175-179`). Staged entries linted at Step 4, then promoted at Step 5.5, are uncommitted `wiki/` files at Step 8.
- `revised_since` uses `last_reviewed[:10] >= day` (`:184-187`). An entry bumped today counts as revised since a lint stamped today.
- `entries()` keeps `tasks/` (`:132-140`), but the semantic lint skips task cards (`skills/wiki-lint/SKILL.md:41,71`). That gives a permanent count on a notebook with 180 cards. `in_tasks` wants a wiki-relative path (`_wiki_config.py:177-180`).
- `last_semantic` and `last_synthesis` call `run_folder.resolve()` (`:207`), so "no run folder" crashes unless the signature changes.

**Evidence to get now:** run the counter read-only on a sandbox after a simulated `--full` run with one promotion and one entry refreshed today, and on llm-wiki-bootstrap's notebook.
**Kill criterion:** any queue the run just covered, or any `tasks/` page, shows a non-zero count.
**Cheapest test:** harness cases for same-day `last_reviewed`, an entry promoted after the lint, and a `wiki/tasks/` card.
**Fix class:** plan error. Exact covered-set rule; exclude `tasks/` and this run's promotions; strict comparison; name the signature change.

### 2. A missing `left-undone.txt` has no stated behaviour
**Fails if:** the run folder exists without `left-undone.txt` (a `--resume` of a run started before the install, a skipped Step 8 command, `/wiki-report --from-json` of an old run). Fallbacks has three states (`skills/wiki-report/SKILL.md:268-273`); the plan has two. Plan line 30 (every unreadable input → `not checked`) contradicts line 127 (an absent step file adds no line). Under `--report-only`, last run's dropped sources are never named.
**Kill criterion:** any report-writing mode ends with no Left undone line and no `not checked` line.
**Cheapest test:** run folder with no `left-undone.txt` → `Left undone: not checked (no left-undone.txt in the run folder)`.
**Fix class:** plan error. Add the third state to the template and `--brief`; reconcile lines 30/127; one rule for `--report-only` sources.

### 3. One paid red-green run of 2 cases proves D3-D6
**Fails if:** the cases cannot reach the rules credited to them.
- Scenario A (`--lint-only`, steps 0, 3 and 8) has no update.json, discover.json or lint-fixes.txt. That makes D4 and D5 unreachable and leaves lint lines tested only as absent.
- Scenario B ("nothing") cannot read `nothing` on a notebook with entries and no prior lint, claims or synthesis history. The fixture history isn't in the plan.
- Red on the old copy proves only that the section exists.
- The extraction of `cmd_semantic`/`cmd_claims`/`cmd_synthesis` is not additive, and old cases that use them are not re-run. `wiki-triage.py` is named by 11 skill files, and `tests/skills/README.md:9` lists "a script many skills call" as a trigger, which the plan doesn't discuss.

**Kill criterion:** a rule has no case that can make its output appear.
**Cheapest test:** keep the two paid cases. Name D4/D5 as unit-tested only. Add one scripted (unpaid) `--full` fixture asserting nothing left.
**Fix class:** choice (Mark). Widen the paid run (a third `--ingest-only` case) or accept D4/D5 as unit-tested; state Scenario B's fixture either way.

### 4. Tier-4 deferrals in `discover.json`'s `deferred[]` need no contract change
**Fails if:** the contract does not say that. `cycle-step-return-format.md:123` defines `deferred[]` as "Items blocked on recoverable error (retry next cycle)", and `:133` gives fetch-failure examples. A tier-4 item waiting on the user is not a retry. `framework-docs/` and `skills/wiki-discover/**` are not in Scope. Not read: whether wiki-discover already defers tier 4.
**Evidence to get now:** read `skills/wiki-discover/SKILL.md` for tier 4; grep the `discover.json` consumers for `deferred`.
**Kill criterion:** a reader treats `deferred[]` as retries, or the contract needs a line to stay true.
**Fix class:** choice. Edit the contract (framework-version bump, `framework-docs/` in Scope) or put tier-4 elsewhere (`notes` or a separate array).

### 5. Decisions needed 1-4 and the skip/default/exempt rules
**Fails if:**
- **D1 (discovery checklists).** Posed as open, but Mark's rule is "every queue it owns that is not empty". `skills/wiki-discover/SKILL.md:220` moves checklists to `_inbox/done/` (reviewer's citation, not re-read).
- **D2 (lint-fixes.txt).** The file is written only after approved fixes are applied, so in an unanswered `--full` run it is absent and "no fix step in this mode" is false. Counting all findings mislabels declined ones as awaiting.
- **D3.** Mark's Decision 4 says "dropped, failed or deferred", and the contract calls LOW-tier items "drops" (`:132`). Leaving them out narrows a confirmed decision. Dedup hits can be left out.
- **D4.** The premise that a filter needs a reason-text match is wrong: `wiki-triage.py` has structured `save_as_pdf:` and `retry:` keys (`:222-231`, `:316-320`). Plan line 46 contradicts the repeat, and the Exclusions say no change to queues Needs you already names.
- **Skipped as covered.** `wiki-dequeue.py:113-128` dequeues on a `source_url` match. Only concept-level matches stay, so "named every cycle" is overstated, and such a line has no way out.
- **Date test.** wiki-report Step 1G uses `awk '{print $2}'`, which keeps quotes, so quoted or invalid dates compare differently.
- **Reason text.** The "No usable review_after" reason claims the lint lists these, but the lint flags only an absent key (`wiki-lint-mechanical.py:727-730`).
- **Standalone report.** Omitting the section reverses requirements line 66 ("every mode that writes a report"). It is a trade-off, and Fallbacks does the same.
- **Staged entries.** Leaving them out when the setting is true holds only while the Needs you line stays (plan line 46 says it does).

**Fix class:**
- Plan error: D1 (include the line, drop the decision), the date test, the reason text, the skipped-as-covered wording.
- Choice for Mark: D2, D3 and D4 (D4 with the corrected premise).

## What holds up
- A `.txt` run-folder file needs no step-contract change. `promote-setting.txt` is in the contract tree, `fallbacks.txt` and `unfinished-runs.txt` are unlisted, and `check.py:2726` reads only `*.json` as steps.
- The old ordering checks pass with a section between Fallbacks and Needs you (`check.py:2757` tests only `heads[-1]`; `:2549-2552`, `:2629`; `_needs_you` `:2223` ends at the next `##`; `FB_NONE` does not match "Left undone: nothing"). Not re-running old cases follows the tests README.
- Cost: about 4 reads per entry on a git notebook, with no subprocess per entry.
- The wiki-dequeue keep rule; the `tasks/` filter for the review-date counts; `not checked`, never silence; dedup hits left out; bucket reuse through `buckets()`/`me()`; framework-docs and lint output untouched.

## Could not assess
- No standing rule found:
  - staged entries left out when `confirm_before_promote: true` (beyond requirements 18 and 68);
  - a malformed `review_after` counted under "No usable" rather than "Past";
  - the `Sources: not checked (update.json unreadable)` and `(no reason recorded)` defaults.
- Not read:
  - whether /wiki-discover already defers tier 4 into `deferred[]`;
  - whether update.json lists retry and Save-as-PDF tickets;
  - the rest of check.py (about 2,000 lines);
  - wiki-lint-mechanical.py beyond lines 577 and 727-730.
- Not checked:
  - whether PyYAML is installed in the scripts environment (`wiki-triage.py:106-112` catches only ImportError);
  - whether agentic-design is a git repo (the non-git `added_since` reads each entry again);
  - wall time on the live 1,731 entries.
- Not re-read by the architect: the reviewer's claims about `wiki-discover:220`, the `save_as_pdf`/`retry` keys, and the wiki-refresh bump of `last_reviewed`.

VERDICT: KILL-ASSUMPTIONS FOUND
