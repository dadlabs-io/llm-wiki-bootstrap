# Plan: a cycle names everything it leaves undone (task #240, lesson #9)

Revised after the round-1 red-team (`plan-red-team.md`): KA1, KA2 and the KA5 plan errors are fixed in place below; KA3, KA4 and the KA5 trade-offs are under Decisions needed. History of the revision is in `checkpoints.md`, not here.

Classification: **vertical slice**. Each step adds queues to one section end to end: the script's line, the run-folder file, the report's copy of it, and the test that pins both. It is not a wide refactor: nothing is renamed or migrated, and the only touch to existing code is pulling three scope computations out into functions both callers use (step 2).

## Problem Statement

A `/wiki-cycle` run can end with queues it owns still non-empty (entries past `review_after`, entries with no `review_after`, entries not linted or claimed or synthesised, lint findings, dropped or failed sources, staged entries, discovery checklists, other readers' buckets), and the report names most of them in some modes and none in others. Mark's rule (2026-11-16): after a run, anything left undone is named, with the count and why.

## Solution

One script writes the section; the report copies it. A new `wiki-cycle-scope.py` subcommand, `left-undone`, runs at Step 8 in every mode (`--report-only` included). It counts fresh from the notebook and the run folder's step files, and writes `left-undone.txt` in the run folder: either `Left undone: nothing` or one finished line per non-empty queue, `- <queue>: <N> — <reason and way out>`. `/wiki-report` pastes that file word for word as a new section "Left undone", just above `⚠️ Needs you` (after Fallbacks), so the model computes no count and writes no reason. The section has **three states**, as Fallbacks does: the file's text; `Left undone: not checked (no left-undone.txt in the run folder)` when the run folder has no file (a `--resume` of a run begun before the install, a skipped command, a report rebuilt from an old run); and, for a standalone report with no run folder, `Left undone: not checked (standalone report: no run folder)`. Silence is never a state. `⚠️ Needs you` stays the last section and keeps every line it has today.

## Implementation Decisions

**The two open questions from requirements, settled.**

1. *Does a new counter change the cycle-step contract?* No. The output is a plain `.txt` in the run folder, as `promote-setting.txt`, `fallbacks.txt` and `unfinished-runs.txt` are; the suite reads only `*.json` as steps. No step, no `summary` key, no new JSON field. `framework-docs/` stays unedited (invariant). Where tier-4 deferrals are recorded is a separate question, Decisions needed 2.
2. *Does a failed or skipped ticket stay in its bucket?* Yes. `wiki-dequeue.py` moves a ticket to `done/` only when its `source` URL matches an entry's `source_url`, and keeps every other one. So a failed, deferred or dropped ticket is still in its bucket after the run, and so is one skipped because an entry on the same topic exists under a different URL (a concept-level match; the dequeue matches URLs only). Left undone names such a ticket every cycle, with the reason the worker gave and no further way out; not changed here.

**What the script reads.** The notebook (entries under `wiki/`, `_inbox/proposed/`, `_inbox/pending/`, `_inbox/intake/`, `_inbox/discovered/`), the run folder's step files, and `promote-setting.txt`. `--today YYYY-MM-DD` defaults to `today_label()` and exists so a test can fix the date. `--from-run <run folder>` (default: the run folder itself) names where the **events and findings** are read from: `update.json`, `discover.json`, `lint-mechanical.json`, `lint-semantic.json`, `lint-fixes.txt` and the tier-4 file (Decisions needed 2). `--report-only` passes the last run's folder, and every line read from it ends `(from <that run's id>)`; the "did this step run this cycle" checks (the reasons below) always look at the current run folder, so under `--report-only` they say nothing ran. It writes only `left-undone.txt`, never a `*-scope.txt`, and changes no entry.

**One rule for absent and unreadable inputs.** Events of the run (`update.json`, `discover.json`, the tier-4 file): absent means the step did not run, so nothing was dropped by it, and it adds no line (the queue lines' reasons already say the mode did not run it). A standing backlog read from a step file (the lint's findings): absent means it cannot be counted without running the step, which this change never does, so the line reads `Lint findings: not checked (no lint ran this cycle; /wiki-cycle --lint-only)`. Any input that exists and cannot be parsed, or a notebook folder that cannot be listed, is its own `<queue>: not checked (<why>)` line. `Left undone: nothing` is written only when no line was written at all.

**Counting rules.**
- *Entries* are `wiki/` pages minus `_`-prefixed files, `README.md`, and anything `_wiki_config.in_sessions` or `in_tasks` says. `in_tasks` and `in_sessions` take a path relative to `wiki/`, so the counter passes `Path(e).relative_to("wiki")`. The script's `entries()` keeps `tasks/` (the semantic lint and refresh skip task cards), so every count below filters again: a task card is never counted.
- *Past `review_after`*: the value parses as a `YYYY-MM-DD` date (quotes stripped, as the shared frontmatter parser does) and is strictly before today. This is `wiki-report` Step 1G's intent; its awk keeps quote characters, so its string comparison treats a quoted date as past: a defect of that snippet, not copied and not fixed here.
- *No `review_after`*: the key is absent. *`review_after` not a date*: present and not a calendar date `YYYY-MM-DD`. Two lines, because the lint lists them in two places and the way out differs.
- *Not semantically linted, no claims, not synthesised*: **an exact covered-set rule.** Pull the list-building out of `cmd_semantic`, `cmd_claims` and `cmd_synthesis` into functions that return `(entries, why)`, called by the commands (their output and files unchanged) and by the counter. No signature of `last_semantic`, `last_synthesis`, `added_since` or `revised_since` changes: they call `run_folder.resolve()` and cut-offs from other runs are what they should keep reading. The counter computes each step's scope as the step would have read it before the run (the unchanged functions, which skip the current run folder), keeps entries only, then **subtracts the stems the step covered this run**: the lines of this run folder's own `semantic-scope.txt`, `claims-scope.txt` or `synthesis-scope.txt`, taken only when the matching `lint-semantic.json`, `claims.json` or a `completed`/`skipped` `synthesis.json` is in the run folder (the step ran). Stems, not paths, because a staged entry the step read at `_inbox/proposed/<slug>.md` is at `wiki/<folder>/<slug>.md` once Step 5.5 promoted it, and one promoted after the lint is an untracked file `added_since` counts. An entry revised or promoted after the step but not read by it is a real leftover and is counted. When the step ran but its scope file is missing: `not checked (no semantic-scope.txt in the run folder)`. A `synthesis.json` with status `awaiting_approval` adds no synthesis line (it is in Needs you). Same-day entries: `revised_since` compares the day of `last_reviewed` with the cut-off's day, as the step does, so an entry re-reviewed on the day of the previous lint is counted when the step did not run this cycle (the step would read it too); a test pins both sides. The review-date comparisons above are strict.
- *Lint findings*: every key of `lint-mechanical.json`'s `summary` above 0 except `files_scanned`, `standalone` and `backlink_blocks_out_of_step` (Needs you has the last).
- *Semantic findings not yet applied*: findings in `lint-semantic.json` (sum of its category arrays) minus `applied` and `declined` from `lint-fixes.txt`; see Decisions needed 3.
- *Sources*: from `update.json`, every `skipped`, `deferred` and `errors` item; from `discover.json`, every `skipped` item whose reason does not begin `already covered` (LOW-tier and other drops; a dedup hit was never a ticket); tier-4 deferrals from the file Decisions needed 2 names. One line per item, `Source <url or slug>: <skipped|deferred|failed> — <reason as the file holds it>`, `(no reason recorded)` when none. Decisions needed 4 and 5 say whether discovery's drops and the tickets already in Needs you are listed.
- *Buckets*: the bucket list and this session's name come from `wiki-triage.py`'s `buckets()` and `me()`, loaded with `importlib` as `_install_tooling.py` does; no second README parser. PyYAML is installed in the scripts environment (6.0.3), so the yaml branch of `_parse_buckets` is what the tests run; its regex fallback (ImportError only) is not exercised. A ticket is a `.md` file in a bucket folder, not `_`-prefixed, with a `source:` line (the rule `wiki-dequeue.py` uses); it becomes one function in `wiki-triage.py`, `intake_tickets(nb)`, yielding `(folder, path, source, front)`, searched for: `wiki-dequeue.py` has the loop inline and also walks `pending/` and moves files, so it is left alone (Out of Scope). Own-bucket tickets are one line; other readers' and the `mark` bucket are one line for all, `Other readers' buckets, still to process: <folder> N, <folder> N` (Mark, D6): no owner, no reason, no items.
- *Discovery checklists*: every `.md` in `_inbox/discovered/` not `_`-prefixed and not `README`: discovery moves a checklist to `_inbox/done/` once it is processed (`wiki-discover` Step 7), so one still there is unreviewed. Included; Mark's rule names every non-empty queue.

**The line wording, one table, so the implementer chooses none of it** ("ran" means the run folder holds that step's JSON; `<x>` is the step):

| Queue | Reason when its step did not run this cycle | Reason when it ran |
|---|---|---|
| Past `review_after` | `no refresh ran this cycle; /wiki-cycle --refresh-only lists them` | `refresh listed them in refresh.md and changed none; refreshing is your call (/wiki-refresh)` |
| No `review_after` | `refresh cannot see an entry with no review_after; add the date (the lint lists them under Missing lifecycle fields)` | same |
| `review_after` not a date | `refresh cannot read it; correct the date (the lint lists them under Dates not in ISO form)` | same |
| Not semantically linted | `no semantic lint ran this cycle; /wiki-cycle --lint-only --semantic or --full` | `the semantic lint ran and did not read them (lint-semantic.md)` |
| No claims, or revised since the index | `no claims step ran this cycle; /wiki-cycle --claims-only or --full` | `the claims step ran and did not read them (claims.md)` |
| Not yet synthesised | `no synthesis ran this cycle (it runs in modes that ingest); /wiki-cycle --ingest-only` | `synthesis ran and did not read them (synthesis.md)` |
| Lint finding kind | `no fix step in this mode` | `awaiting your approval` (`lint-fixes.txt` exists: Step 5 ran) |
| Tickets in `_inbox/pending/` | `this mode does not triage; /wiki-cycle --ingest-only gives each an owner` | `triage left them (triage.md)` |
| Tickets in this session's buckets | `this mode does not ingest; /wiki-cycle --ingest-only` | `left after ingest: the dropped, failed and deferred ones are listed below` (retry and Save-as-PDF ones are in Needs you) |
| Staged entries (only when `confirm_before_promote: false`) | `staged before this run, or held by the checker; /wiki-promote` | same |
| Discovery checklists | `not reviewed yet; the next /wiki-cycle shows each for review (discovery files it in _inbox/done/ once processed)` | same |

**Not in Left undone** (already in Needs you with count and reason, which stays word for word): staged entries when `confirm_before_promote: true`, Drive files left, synthesis awaiting approval, backlink blocks, retry items, Save as PDF pages, unmatched PDFs, unapproved email candidates, held-by-checker entries, unfinished earlier runs.

**The report's side.** `wiki-report`'s template gets `## Left undone` between Fallbacks and Needs you, with the three states above. `--brief` gets one line after Numbers, as Fallbacks does, in the same three states: `Left undone: N — see the full report`, `Left undone: nothing`, or the not-checked text. `wiki-cycle` Step 8 runs the command first (passing `--from-run <last run folder>` under `--report-only`) and says Fallbacks and Left undone come just before Needs you, in that order. Step 5 says to write `lint-fixes.txt` (Decisions needed 3). Step 1.5 says where a tier-4 deferral is recorded (Decisions needed 2). Step 8's Needs you line "lint fixes awaiting approval" gets "N" from Left undone's semantic line. Skill text grows by as little as that takes; the table and the counting rules live in the script's docstring, the one source, and the usage pages point there.

**Loops over live data (arithmetic, no timing run).** agentic-design holds about 1,730 entries and lives in the project-notebooks git repository (checked: `git rev-parse` there gives that repo), so `added_since` takes its git path: one `git log` and one `git ls-files` per scope, not one per entry. The counter reads each entry's frontmatter once per count that needs it (review dates, `revised_since` for semantic and claims, the research filter for synthesis): at most about 4 x 1,730 = 7,000 small reads, bounded by the entry list; no subprocess per entry. The non-git branch (a read of every entry again) is not what the live notebooks run.

## Testing Decisions

- No script in `scripts/` has a `--self-test` block (grepped). The free seam is `tests/scripts/test_cycle_scope.py`, the existing throwaway-notebook harness (own git repo, set commit dates): the new checks extend it. `tests/scripts/test_wiki_triage.py` takes `intake_tickets`. Plus one unpaid `--full` fixture in the same harness: a notebook after a simulated `--full` run (this run's `lint-semantic.json` and `semantic-scope.txt`, `claims.json` and `claims-scope.txt`, `synthesis.json`, a staged entry linted then promoted, an entry re-reviewed today, a `wiki/tasks/` card) must give `Left undone: nothing`.
- Seam 2 (paid, model-graded): the wiki-cycle suite, the section as the model copies it into the report; `wiki-report` has no suite. Cases come from `eval-case-writer` (mode `fresh`) from the requirement and the scenarios below, never from the diff; the editing session does not read `cases.json` while editing. Scenario A and B fixtures are in Decisions needed 1.
- manual: step 3 — the `lint-fixes.txt` instruction at Step 5 and the Needs you count, read against the report template and the script's parsing; the first real `--full` run's report is the live check, named in the run notes.
- manual: step 6 — the `--brief` line, read against the Fallbacks brief line's wording.
- manual: step 7 — the CHANGELOG entry, the `wiki-cycle` and `wiki-report` usage pages and the `tests/skills/PENDING.md` row, read against steps 1 to 6; and the live read-only run of `left-undone` on agentic-design and llm-wiki-bootstrap, its past-`review_after` counts compared with requirements' 607 and 6 (a difference is explained in the run notes: those greps left `tasks/` in).

## Out of Scope

- Refreshing, re-dating or editing any entry, or running a step a mode skips: clearing agentic-design's 607 is task #245, on Mark's go.
- Review cadence, the rollback bug (`wiki-rollback.py` writes `review_after` = today), lint exit codes, which findings are warn-only, and `wiki-report` Step 1G's quote-keeping awk (named above, not fixed).
- Any age rule or threshold; any ping or message outside the report.
- Ingesting, triaging or promoting other readers' buckets.
- The queues Needs you already names, and rows 15, 22 and 23 of the requirements' inventory.
- A way to stop Left undone repeating a ticket whose topic is covered under another URL (see settled question 2).
- `wiki-dequeue.py`'s inline ticket loop is a look-alike of `intake_tickets`, left alone: it moves files and also walks `pending/`, so migrating it would put a moving script in this change's blast radius for no change in behaviour.
- The lint script, and the install itself: the finish step is `.\install-wiki.ps1 -RefreshOnly`, then `--mode status` reads installed and current.
- `wiki-triage.py` is named by 7 skill files and the scope script by 4, but the change only adds `intake_tickets` to the first (additive: README's trigger list says a purely additive check does not count) and re-routes three subcommands only `wiki-cycle` calls in the second; the "script many skills call" trigger does not fire, so no full suite is recommended. The existing triage and scope tests are the check, run at every step.

## Scope

- scripts/wiki-cycle-scope.py
- scripts/wiki-triage.py
- skills/wiki-cycle/**
- skills/wiki-report/**
- tests/scripts/test_cycle_scope.py
- tests/scripts/test_wiki_triage.py
- tests/skills/wiki-cycle/**
- tests/skills/PENDING.md
- CHANGELOG.md
- .do-code-change/240-loud-backlogs/**

(If Decisions needed 2 is answered "edit the contract", `framework-docs/cycle-step-return-format.md` and `skills/wiki-discover/**` join this list and the framework version bumps.)

## Invariants

- The existing checks in `test_cycle_scope.py` and `test_wiki_triage.py` stay green through the extraction (step 2) and `intake_tickets` (step 5): both files run at the end of every step.
- The command changes no entry: a test hashes `wiki/` and `_inbox/` before and after one run and asserts only `left-undone.txt` is new (step 1).
- The command writes no `*-scope.txt` (step 2).
- `⚠️ Needs you` is the last report section and Fallbacks stays above it: the old eval checks key on heading order, not adjacency (`check.py:2757` tests only the last heading; `:2549-2552` and `:2629` the order), so a section between them passes; the new cases assert the order again. The old fallbacks and backlinks cases are not re-run (README: nothing more without Mark's yes); logged in PENDING.md.
- `git diff --stat -- framework-docs scripts/wiki-lint-mechanical.py` prints nothing at verify (unless Decisions needed 2 is answered "edit the contract").

## Decisions needed

Each is one standalone question for Mark.

1. **How far should the paid test run reach?**
   The new section is copied into the report by the model, so one paid run proves the copying works. As planned, case A (a short `--lint-only` run) never produces the lines for dropped sources, lint findings or fixes awaiting approval, because that mode has no ingest, no discovery file and no fix step.
   Recommendation: make case A a resumed run that starts at the report step, with the earlier steps' result files already placed in the run folder (an ingest result with one skipped, one deferred and one failed source; a discovery result with one skipped source; a lint result with findings; a fixes-applied note), plus planted entries, a staged entry, other readers' tickets and one discovery checklist. Same cost as planned, 8 short sessions: two cases, both models, old copy and new copy, no workers. Case B is a clean `--lint-only` run on the clean seed notebook already used by the empty-queue cases, plus history files (an earlier semantic lint, a claims index and a completed synthesis all newer than every entry; every `review_after` in the future; no staged entries, empty queues, `confirm_before_promote: true`) so the section reads `Left undone: nothing`. The "paid run reaches every line" proof is the one place a resumed fixture helps; a resumed run with seeded files is the pattern the existing "resumed run" cases use.
   Alternative: keep case A as a plain `--lint-only` run and accept that the dropped-source and lint-fix lines are tested only by the unpaid script tests. Risk: the model has never been shown to copy those lines; the script's own tests prove the text, not the copying. A third paid case (a real `--ingest-only` run with a source that fails) would prove more but adds 4 sessions and workers, and is not recommended.
   [ ] seeded resume for case A  [ ] plain `--lint-only`, script tests only

2. **Where are sources deferred at tier 4 recorded?**
   When a cycle runs unattended (`--no-confirm-discovery`), Step 1.5 queues discovery's tier 1-3 sources and defers tier 4, but nothing records the deferral: `wiki-discover` only labels such candidates "(NEEDS HUMAN REVIEW)" in its checklist, and no script, skill or test reads `discover.json`'s `deferred[]`. The cycle-step contract defines `deferred[]` as "items blocked on recoverable error (retry next cycle)", which a tier-4 item waiting for you is not.
   Recommendation: Step 1.5 writes the deferred tier-4 sources to a new plain-text file in the run folder (`tier4-deferred.txt`, one `<url><tab><title>` per line), which the script reads. No contract edit, no framework version change.
   Alternative: put them in `discover.json`'s `deferred[]` and edit the contract to say it also holds items waiting on the user, bumping the framework version and adding `framework-docs/` and `wiki-discover` to this change's scope. Risk: a framework-contract change that every global install refreshes, for one reason string.
   [ ] separate text file  [ ] edit the contract

3. **How is the "lint fixes awaiting approval" count worked out?**
   Nothing on disk records what you approved at Step 5, and the fixes list is not written until fixes are applied, so the count cannot be read from existing files.
   Recommendation: Step 5 always writes a small `lint-fixes.txt` in `--full` runs (`applied: N` and `declined: N`, both 0 when the run could not ask), and the script reports awaiting = findings in `lint-semantic.json` minus those two. The file's presence also tells the line's reason ("awaiting your approval" versus "no fix step in this mode").
   Alternative: write only `applied: N` and call the line "findings not applied: N", with no claim they await approval. Risk: a finding you declined reads as pending, and the line wording stops matching your Decision 5.
   [ ] applied and declined  [ ] applied only

4. **Should discovery's dropped sources be listed?**
   Your Decision 4 said each source the run dropped, failed or deferred is named. Discovery drops candidates as "LOW relevance, no tier-1 source" or similar and as "already covered by <slug>". An already-covered one was never queued, so nothing is left undone.
   Recommendation: list every discovery drop except the "already covered" ones, so a LOW-tier drop shows with its reason. Risk: on agentic-design that can be many lines per cycle.
   Alternative: one line, `Discovery dropped N sources, listed in discover.md`, with no per-source lines. Risk: that is a count with a pointer, which Decision 4 said was not enough.
   [ ] list them  [ ] one line with a pointer

5. **Should a ticket already in "Needs you" also appear in the sources list?**
   Tickets left for retry and pages to save as PDF are in Needs you with their task card or folder. A failed source may be one of them. Tickets carry structured markers for both (`retry:` and `save_as_pdf:` in their own frontmatter), so no reason-text matching is needed.
   Recommendation: leave out of the sources list any source whose ticket carries either marker, so each item sits in one place. Risk: if a source's URL differs in form from its ticket's, the filter misses it and it appears twice, which is harmless.
   Alternative: list every dropped, failed or deferred source, repeats included: the list is the inventory, Needs you is the action. Risk: one item twice on the page.
   [ ] leave them out  [ ] list everything

## Steps

Every step ends with `test_cycle_scope.py` and `test_wiki_triage.py` run green (the invariant).

1. **The section exists, with the two review-date lines and its three states** — a `--lint-only` report shows `## Left undone` just above Needs you with past-`review_after` and no-`review_after` lines, or `Left undone: nothing`. Builds the `left-undone` subcommand (`--today`, `--from-run`, writes `left-undone.txt`), Step 8's call, the template section and `--brief` line in all three states. uses: `entries()`, `_front`, `write_scope`'s header-line convention, `_wiki_config.in_sessions`, `in_tasks`, `today_label`; new function `review_date_counts`, searched for: `review_after` in `scripts/` (the lint collects inline, the refresh guidance is prose; neither returns a list), found none. Done when the new checks in `test_cycle_scope.py` pass:
   - Expected: 2 entries past `review_after`, 1 dated today, 1 in the future, 1 with no `review_after`, 1 with `review_after: soon` give `Past review_after: 2 — no refresh ran…`, `No review_after: 1 — …`, `review_after not a date: 1 — …`; with `refresh.json` in the run folder the past line carries the `ran` reason; all dates future and none missing writes exactly `Left undone: nothing`; a quoted `review_after: "2026-01-01"` counts as past.
   - Failures: a `wiki/tasks/` card and a `wiki/sessions/` page with no `review_after` are not counted; `--today 2026-13-40` exits 2 and writes no file; a missing notebook or run folder exits 2 and writes no file; a run folder with no `left-undone.txt` is read by the template text as `Left undone: not checked (no left-undone.txt in the run folder)` (checked by reading the wiki-report text, manual: step 7).
   - Invariant: `wiki/` and `_inbox/` hashes are identical before and after except the new file; no `*-scope.txt` appears.
   - Done also when `check.py`'s order checks are read statically and found to key on heading order (recorded in the run notes).
   Trivial stakes: no

2. **Not linted, no claims, not synthesised, counted after the run** — `--lint-only` reports the three with their reasons; after a `--full` run they report none. Extracts list-returning functions from `cmd_semantic`, `cmd_claims`, `cmd_synthesis` (callers and counter share them) and applies the covered-set rule. No signature change to `last_semantic`, `last_synthesis`, `added_since`, `revised_since`. Done when the new checks pass:
   - Expected: with the harness history (lint 2026-09-10; `new-d` added and `old-a` re-reviewed after), step not run: `Not semantically linted: 2` with the `no semantic lint ran` reason; with this run's `lint-semantic.json` and a `semantic-scope.txt` listing `new-d` and `old-a`: no line; claims with no index counts every entry, with an index only the unindexed or revised ones; a completed `synthesis.json` and `synthesis-scope.txt` in the run folder: no synthesis line, without them the research entries added since the last answered synthesis.
   - Failures: a staged entry linted then promoted (listed as `_inbox/proposed/x.md` in the scope file, now `wiki/.../x.md`) is not counted; an entry re-reviewed today after a lint run earlier today IS counted when the step did not run, and is not when this run's scope file lists it; a `wiki/tasks/` card is never counted; a `synthesis.json` `awaiting_approval` adds no line; the step JSON present with no scope file gives `not checked (no semantic-scope.txt in the run folder)`; a malformed `lint-semantic.json` gives `not checked`, no crash; no `semantic-scope.txt`, `claims-scope.txt` or `synthesis-scope.txt` is written by the counter.
   - Invariant: the file's existing `semantic`, `claims` and `synthesis` checks pass unchanged (they pin the extraction); the unpaid `--full` fixture (Testing Decisions) reads `Left undone: nothing`.
   Trivial stakes: no

3. **Lint findings and semantic findings not applied** — a run whose lint found 2 broken links reports them with `no fix step in this mode`, a `--full` run `awaiting your approval`; the Needs you line gets the count. Reads `lint-mechanical.json`'s summary and `lint-semantic.json`; Step 5 text gets the `lint-fixes.txt` instruction (Decisions needed 3, recommended form). Done when the new checks pass:
   - Expected: `broken_links: 2`, `orphans: 0`, `unquoted_yaml: 1` gives two lines, none for `files_scanned`, `standalone`, `backlink_blocks_out_of_step`; with `lint-fixes.txt` the reason is `awaiting your approval`; a `lint-semantic.json` with 5 findings and `applied: 2`, `declined: 1` gives 2 awaiting; `--from-run <last run>` adds `(from <id>)`.
   - Failures: no lint JSON gives `Lint findings: not checked (no lint ran this cycle; /wiki-cycle --lint-only)` and the file is not `nothing`; unparseable JSON gives `not checked (<why>)`; a summary of all zeros adds no lint line; a non-numeric `applied:` counts as 0 and the line says so, no crash.
   - manual: the Step 5 instruction and the Needs you count (Testing Decisions).
   Trivial stakes: no

4. **Dropped, failed and deferred sources** — a run whose ingest skipped one source, failed one and deferred one, and whose discovery dropped one, names each with its reason; under `--report-only` the lines come from the last run. Reads `update.json`, `discover.json`, the tier-4 file (Decisions needed 2, recommended form) and each ticket's `retry:` / `save_as_pdf:` marker (Decisions needed 5, recommended form) via `intake_tickets` (step 5 adds it; this step is **blocked by: 5**, so the order is 5 then 4). Step 1.5 text gets the tier-4 file instruction. Done when the new checks pass:
   - Expected: `update.json` with 1 skipped (`thin content`), 1 deferred (`429`), 1 error (`item`, `message`); `discover.json` with 1 skipped (`LOW relevance`) and 1 skipped (`already covered by x`); a tier-4 file with 1 line: five lines, each with URL or slug and the reason verbatim, the `already covered` one absent; `--from-run` another folder adds `(from <id>)`.
   - Failures: `update.json` that does not parse gives `Sources: not checked (update.json unreadable)`; an item with no reason gives `(no reason recorded)`; a step file absent adds no line; a source whose ticket carries `retry:` or `save_as_pdf:` is left out (recommended form), one with neither stays in.
   Trivial stakes: no

5. **Buckets, pending, staged entries and discovery checklists** — a run leaves tickets in two other readers' buckets and in `mark`'s, 3 in `_inbox/pending/`, 2 staged entries with `confirm_before_promote: false` and 1 discovery checklist: the section carries `Other readers' buckets, still to process: …` once, plus the pending, staged and checklist lines with their reasons; with the setting `true`, no staged line. Adds `intake_tickets` to `wiki-triage.py`; `buckets()` and `me()` load through `importlib`. Done when the new checks in `test_cycle_scope.py` and `test_wiki_triage.py` pass:
   - Expected: buckets `main` (this session), `other` (another bot), `money` (`mark`) holding 2, 4 and 15 tickets give `Other readers' buckets, still to process: other 4, money 15` and an own-bucket line for `main` (2, `update.json` absent: `this mode does not ingest`); 3 pending tickets give the pending line; `intake_tickets` returns each ticket once with its bucket, source and frontmatter and skips `README.md`, `_`-prefixed files and a `.md` with no `source:`; one `.md` in `_inbox/discovered/` gives the checklist line, a `README.md` there does not.
   - Failures: a bucket folder that does not exist counts 0 and adds nothing; no `_inbox/discovered/` folder adds nothing and no `not checked`; no `promote-setting.txt` gives `Staged entries: not checked (no promote-setting.txt)`; `confirm_before_promote: true` adds no staged line.
   - Invariant: the existing `wiki-triage` bucket and route checks pass (`buckets()` and `me()` are used unchanged).
   Trivial stakes: no

6. **`--brief` carries the line** — the brief report shows the three-state line after Numbers. The `wiki-report` text edit; manual: step 6. Trivial stakes: yes — template wording in a skill file, no code branch; the evidence is the text read against the Fallbacks brief line.

7. **Eval cases red then green, docs, finish** — blocked by: 1 to 6. The `eval-case-writer` writes scenarios A and B (fixtures per Decisions needed 1), saved unchanged to `cases.json` with its `check.py` branch; one run proves them: `uv run python tests/skills/run_skill_test.py wiki-cycle --cases <A>,<B> --red-green <the commit before step 1>` (both models, as the README requires). Then CHANGELOG, the `wiki-cycle` and `wiki-report` usage pages (what the section holds and where it comes from, pointing to the script's docstring), the `PENDING.md` row, and the live read-only run on the two notebooks. The install SOP is the separate finish step after. Done when the red-green command exits 0 with each of A and B `red then green` on both models:
   - Expected: on the old copy both fail (no Left undone section); on the new copy both pass: A's section lines carry the planted counts and reasons and equal the script's file, above Needs you, Needs you last; B reads `Left undone: nothing` above Needs you.
   - Failures: a case that passes on the old copy goes back to the writer (`replay`), not counted; the red-green run exits 1 and stops, the 8 sessions not repeated.
   - manual: the live run and docs (Testing Decisions).
   Trivial stakes: no (the cases); the docs lines are wording only.

## Paid runs the plan expects

One red-green run, two new cases, both models, old and new copy: 8 headless sessions, none with workers. No full suite (no README trigger fires; see Out of Scope). It runs only on Mark's go; cost to be read from the fallbacks change's red-green run, the same size. A third paid case is not planned (Decisions needed 1).
