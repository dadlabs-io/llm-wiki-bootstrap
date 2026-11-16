# Plan: a cycle names everything it leaves undone (task #240, lesson #9)

Classification: **vertical slice**. Each step adds more queues to one section, end to end: the script's line, the run-folder file, the report's copy of it, and the test that pins both. It is not a wide refactor: nothing is renamed or migrated, and the only touch to existing code is pulling two scope computations out into functions both callers use (step 2).

## Problem Statement

A `/wiki-cycle` run can end with queues it owns still non-empty (entries past `review_after`, entries with no `review_after`, entries not linted or claimed or synthesised, lint findings, dropped or failed sources, staged entries, other readers' buckets) and the report names most of them in some modes and none in others. Mark's rule (2026-11-16): after a run, anything left undone is named, with the count and why.

## Solution

One script writes the section; the report copies it. A new `wiki-cycle-scope.py` subcommand, `left-undone`, runs at Step 8 in every mode (`--report-only` included). It counts fresh from the notebook and the run folder's step files, and writes `left-undone.txt` in the run folder: either `Left undone: nothing` or one finished line per non-empty queue, `- <queue>: <N> — <reason and way out>`. `/wiki-report` pastes that file word for word as a new section "Left undone", just above `⚠️ Needs you` (after Fallbacks), so the model computes no count and writes no reason. `⚠️ Needs you` stays the last section and keeps every line it has today.

## Implementation Decisions

**The two open questions from requirements, settled here.**

1. *Does a new counter change the cycle-step contract?* No. The output is a plain `.txt` in the run folder, as `promote-setting.txt` and `unfinished-runs.txt` are (`cmd_promote`'s own comment: the run folder's `*.json` files are step results under the contract, so a counter file is text). No step, no `summary` key, no new JSON field. The framework-contract doc stays unedited (invariant below). The one JSON-adjacent change is a reason string: a tier-4 discovery deferral is written to `discover.json`'s `deferred[]`, which the contract already lists as "items blocked", with the reason `tier 4: needs your review (--no-confirm-discovery)`.
2. *Does a failed or skipped ticket stay in its bucket?* Yes, by code: `wiki-dequeue.py` moves a ticket to `done/` only when its `source` is now an entry (promoted or staged), and keeps every other one. So failed, skipped and deferred tickets are still in their bucket after the run, which is what makes them "left undone". Consequence, existing behaviour and not changed here: a ticket skipped as "already covered by <slug>" never dequeues, so Left undone names it every cycle until someone removes it.

**What the script reads.** The notebook (entries under `wiki/`, `_inbox/proposed/`, `_inbox/pending/`, `_inbox/intake/`), the run folder's step files, `promote-setting.txt`, and an optional `--lint-json <path>` (default: the run folder's own `lint-mechanical.json`; `--report-only` passes the last run's, and the line then says `(from <that run's id>)`). `--today YYYY-MM-DD` defaults to `today_label()` and exists so a test can fix the date. It writes only `left-undone.txt`, never a `*-scope.txt`, and changes no entry.

**Counting rules.**
- *Past review_after*: `review_after` is a `YYYY-MM-DD` date strictly before today (the same test as `wiki-report` Step 1G). Entries are `wiki/` pages minus `_`-prefixed files, `README.md`, and anything `_wiki_config.in_sessions` or `in_tasks` says (the lint's and refresh's rule; the existing `entries()` in the script leaves `tasks/` in, so the review-date counts filter again).
- *No usable review_after*: the key is absent or its value is not a `YYYY-MM-DD` date. A malformed date is not "past" (refresh cannot read it either); it is counted here so it is never silent.
- *Not semantically linted / no claims / not synthesised*: the same entry lists the three scope commands compute, minus staged entries. Pull `semantic`, `claims` and `synthesis`'s list-building out of their `cmd_*` into functions that return the list, and have the commands and the counter call the same ones, so the count equals what the step would read. **The cut-off lookups skip the current run folder** (`last_semantic`, `last_synthesis`), correct before a step and wrong after it: reused as-is, a `--full` run would say "N not linted" right after linting them. The counter passes no run folder, so this run's own `lint-semantic.json` and a `completed` `synthesis.json` are cut-offs. A `synthesis.json` with status `awaiting_approval` is not counted (it is already in Needs you).
- *Lint findings*: every key of `lint-mechanical.json`'s `summary` above 0 except `files_scanned`, `standalone` and `backlink_blocks_out_of_step` (the last is in Needs you). A missing or unreadable lint JSON is a line `Lint findings: not checked (<why>)`, never nothing.
- *Semantic findings awaiting*: findings in `lint-semantic.json` (sum of its category arrays) minus `applied: N` from `lint-fixes.txt`; see Decisions needed 2.
- *Sources*: from `update.json`, each `skipped`, `deferred` and `errors` item; from `discover.json`, each `deferred` item. One line per item, the reason as the file holds it. Discovery's `skipped` (dedup hits, LOW tier) is a decision, not undone work, and is left out.
- *Buckets*: the bucket list and this session's name come from `wiki-triage.py`'s `buckets()` and `me()`, loaded with `importlib` as `_install_tooling.py` does; no second README parser. A ticket is a `.md` file in a bucket folder that is not `_`-prefixed and has a `source:` line (the rule `wiki-dequeue.py` uses); it goes in `wiki-triage.py` as one function, `intake_tickets(nb)`, searched for in the scripts: only `wiki-dequeue.py` has the loop inline, and it moves files and also walks `pending/`, so it is left alone (Out of Scope). Own-bucket tickets are one line; other readers' and the `mark` bucket are one line for all, `Other readers' buckets, still to process: <folder> N, <folder> N` (Mark, D6): no owner, no reason, no items.
- *A missing source file is never "nothing"*: every input the script cannot read becomes its own `not checked` line. `Left undone: nothing` is written only when every source was read and every queue is empty.

**The line wording, one table, so the implementer chooses none of it** (`<x>` means the queue's step; "ran" means the run folder holds that step's JSON):

| Queue | Reason when its step did not run this cycle | Reason when it ran |
|---|---|---|
| Past `review_after` | `no refresh ran this cycle; /wiki-cycle --refresh-only lists them` | `refresh listed them in refresh.md and changed none; refreshing is your call (/wiki-refresh)` |
| No usable `review_after` | `refresh cannot see them; add review_after (the lint lists them under Missing lifecycle fields)` (same in every mode) | same |
| Not semantically linted | `no semantic lint ran this cycle; /wiki-cycle --lint-only --semantic or --full` | `the semantic lint ran and did not cover them (lint-semantic.md)` |
| No claims, or revised since the index | `no claims step ran this cycle; /wiki-cycle --claims-only or --full` | `the claims step ran and did not cover them (claims.md)` |
| Not yet synthesised | `no synthesis ran this cycle (it runs in modes that ingest); /wiki-cycle --ingest-only` | `synthesis ran and did not cover them (synthesis.md)` |
| Lint finding kind | `no fix step in this mode` | `awaiting your approval` (`lint-fixes.txt` exists: Step 5 ran) |
| Tickets in `_inbox/pending/` | `this mode does not triage; /wiki-cycle --ingest-only gives each an owner` | `triage left them (triage.md)` |
| Tickets in this session's buckets | `this mode does not ingest; /wiki-cycle --ingest-only` | `left after ingest: failed, skipped or deferred ones are listed below` |
| Staged entries (only when `confirm_before_promote: false`) | `staged before this run, or held by the checker; /wiki-promote` | same |

**Not in Left undone** (each is already in Needs you with its count and reason; Mark: items there stay there): staged entries when `confirm_before_promote: true`, Drive files left, synthesis awaiting approval, backlink blocks, retry items, Save as PDF pages, unmatched PDFs, unapproved email candidates, held-by-checker entries, unfinished earlier runs. The sources list can repeat a retry or Save-as-PDF ticket (the Left undone line is the inventory, the Needs you line is the action); filtering them per ticket would need a reason-text match that breaks on the first wording change (Decisions needed 4).

**The report's side.** `wiki-report`'s template gets `## Left undone` between Fallbacks and Needs you: the file's text copied word for word; standalone (no run folder): the section is omitted, as Fallbacks is. `--brief` gets one line after Numbers, as Fallbacks does: `Left undone: N — see the full report`, or `Left undone: nothing`. `wiki-cycle` Step 8 runs the command first and says the Fallbacks and Left undone sections come just before Needs you, in that order; Step 1.5 says a tier-4 deferral under `--no-confirm-discovery` is also written to `discover.json`'s `deferred[]`; Step 5 says to write `lint-fixes.txt` (`applied: N`, written even when N is 0) once the approved fixes are applied; Step 8's Needs you line "lint fixes awaiting approval" gets "N" from Left undone's semantic line. Skill text grows by as little as that takes; the table and the counting rules live in the script's docstring, the one source.

**Loops over live data (arithmetic, no timing run).** agentic-design holds about 1,730 entries. The command reads each entry's frontmatter once per count that needs it (review dates, `revised_since` for semantic and claims, the research filter for synthesis): at most about 4 x 1,730 = 7,000 small reads, bounded by the entry list. `added_since` is one `git log` and one `git ls-files` per scope, not one per entry. No loop runs a subprocess per entry.

## Testing Decisions

- No script in `scripts/` has a `--self-test` block (grepped). The free seam is `tests/scripts/test_cycle_scope.py`, the existing throwaway-notebook harness (own git repo, set commit dates, registry, run via subprocess): the new checks extend it. Bucket checks add an intake README and tickets to that notebook's registry; `tests/scripts/test_wiki_triage.py` takes `intake_tickets`.
- Seam 2 (paid, model-graded): the wiki-cycle suite (`tests/skills/wiki-cycle`), the section as the model copies it into the report. `wiki-report` has no suite; the cycle's cases grade it.
- Cases come from the `eval-case-writer` agent (mode `fresh`) from the requirement text and scenarios below, never from the diff; the editing session does not read `cases.json` while editing the skill. Scenarios: (A) a `--lint-only` run on a notebook with planted backlogs (entries past `review_after`, one with no `review_after`, entries added since the last semantic lint, a staged entry with `confirm_before_promote: false`, tickets in another reader's bucket and in `mark`'s) whose report's Left undone section must carry the counts and reasons the planted data gives, above Needs you, with Needs you still last; (B) a clean run on a notebook with nothing left: the report reads `Left undone: nothing` above Needs you.
- manual: step 3 — the "lint fixes awaiting approval" count in Step 8's Needs you line and the `lint-fixes.txt` instruction, read against the report template and the script's `applied: N` parsing; the first real `--full` run's report is the live check, named in the run notes (a `--full` eval case costs semantic-lint agents and fix agents; not worth it for one number).
- manual: step 6 — the `--brief` line, read in the wiki-report text against the Fallbacks brief line's wording.
- manual: step 7 — the CHANGELOG entry, the `wiki-cycle` and `wiki-report` usage pages and `tests/skills/PENDING.md` row, read against steps 1 to 6; and the live read-only run of `left-undone` on agentic-design and llm-wiki-bootstrap, its past-`review_after` counts compared with requirements' 607 and 6 (a difference is explained in the run notes, not forced equal: those greps left `tasks/` in).

## Out of Scope

- Refreshing, re-dating or editing any entry, or running a step a mode skips: clearing agentic-design's 607 is task #245, on Mark's go.
- Any change to review cadence, the rollback bug (`wiki-rollback.py` writing `review_after` = today), lint exit codes, or which findings are warn-only.
- Any age rule or threshold; any ping or message outside the report.
- Ingesting, triaging or promoting other readers' buckets.
- The queues Needs you already names (listed above), and rows 15, 22 and 23 of the requirements' inventory.
- Dequeuing a ticket skipped as "already covered" so Left undone stops repeating it; named under Implementation Decisions as existing behaviour.
- `wiki-dequeue.py`'s inline ticket loop is a look-alike of `intake_tickets`, left alone: it moves files and also walks `pending/`, a different job, and migrating it would put a moving script inside this change's blast radius for no change in behaviour.
- `framework-docs/` (the cycle-step contract), the lint script, and the install itself. The install is the separate finish step: `.\install-wiki.ps1 -RefreshOnly`, `--mode status` reads installed and current.

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

## Invariants

- The existing checks in `tests/scripts/test_cycle_scope.py` and `tests/scripts/test_wiki_triage.py` stay green through the scope-function extraction (step 2) and the new `intake_tickets` (step 5): run both files at the end of each step.
- The command changes no entry: a test hashes the notebook's `wiki/` and `_inbox/` before and after one run and asserts only `left-undone.txt` is new (step 1's `Failures:`).
- The command writes no `*-scope.txt`: asserted in step 2 (a stale `semantic-scope.txt` from a skipped mode could trip the existing eval checks).
- `⚠️ Needs you` is the last report section and Fallbacks stays above it: the existing suite checks ("the cycle report's last section is Needs you", "the Fallbacks section comes before Needs you") are read statically in step 1 (they key on heading order, not adjacency, so a Left undone section between them passes), and the new cases assert the order again. The old fallbacks and backlinks cases are not re-run (README: nothing more runs without Mark's yes); logged in PENDING.md.
- `framework-docs/` is untouched: `git diff --stat -- framework-docs` prints nothing at verify.
- The lint's output is untouched: `git diff --stat -- scripts/wiki-lint-mechanical.py` prints nothing.

## Decisions needed

1. **Name `_inbox/discovered/` checklists as a Left undone line?** The requirements list them as a gap (row 21); the Pending-work table counts them but nothing says whether a reviewed checklist is ever cleared, so the line could be permanent. Recommendation: include, `Discovery checklists in _inbox/discovered/: N — candidates you have not approved or rejected`, since Mark's rule names every non-empty queue. Alternative: leave it in the Pending-work table; risk: a queue the cycle owns stays unnamed. [ ] include  [ ] leave out
2. **Source of the "lint fixes awaiting approval" count.** Nothing on disk records what the user approved at Step 5. Recommendation: Step 5 writes `lint-fixes.txt` (`applied: N`) and the script counts findings in `lint-semantic.json` minus N; the file's presence also tells the reason ("awaiting your approval" vs "no fix step in this mode"). Alternative: count all findings shown at Step 5 as awaiting; risk: the number is wrong after the user approved some. [ ] lint-fixes.txt  [ ] all findings
3. **Dropped sources.** Recommendation: name each source in `update.json`'s `skipped`, `deferred` and `errors` and `discover.json`'s `deferred`, and leave discovery's dedup and LOW-tier `skipped` out (decisions, nothing was queued for them). Alternative: name those too; risk: on agentic-design that is hundreds of lines every cycle. [ ] as recommended  [ ] include discovery's skipped
4. **A retry or Save-as-PDF ticket appearing in both Left undone (inventory) and Needs you (action).** Recommendation: allow the repeat. Alternative: filter them from the sources lines per ticket; risk: a filter that matches on reason text breaks on the first wording change. [ ] allow  [ ] filter

## Steps

Every step also ends green on the existing `test_cycle_scope.py` and `test_wiki_triage.py` (the invariant above), run once at the step's end.

1. **The section exists, with the two review-date lines** — a `--lint-only` report shows `## Left undone` just above Needs you with `Past review_after` and `No usable review_after` lines, or `Left undone: nothing`. Builds the `left-undone` subcommand (fresh counts, `--today`, writes `left-undone.txt`), Step 8's call, and the template section; uses: `entries()`, `_front`, `write_scope`'s header-line convention (all in the scope script), `_wiki_config.in_sessions`, `in_tasks`, `today_label`; new function `review_date_counts`, searched for: `review_after` in `scripts/` (found only the lint's inline collection and the refresh guidance, neither returns a list). Done when the new checks in `test_cycle_scope.py` pass:
   - Expected: on a notebook with 2 entries past `review_after`, 1 on today's date, 1 in the future, 1 with no `review_after`, the file reads `Past review_after: 2 — …` and `No usable review_after: 1 — …` with the table's `no refresh ran` reason; when the run folder holds `refresh.json` the reason is the `ran` one.
   - Expected: a notebook with every date in the future and none missing writes exactly `Left undone: nothing`.
   - Failures: a `review_after: not-a-date` entry is counted under No usable `review_after`, never under Past, and the run exits 0; a page under `wiki/tasks/` and one under `wiki/sessions/` with no `review_after` are not counted; `--today 2026-13-40` exits 2 and writes no file; a missing notebook or run folder exits 2 and writes no file.
   - Invariant: the notebook's `wiki/` and `_inbox/` are byte-identical before and after (hash comparison) except the new `left-undone.txt`, and no `*-scope.txt` appears.
   - Also done when the report text is read (manual: see step 7) and the two existing "Needs you last" and "Fallbacks before Needs you" eval checks are confirmed by reading `check.py` to key on heading order.
   Trivial stakes: no

2. **The three skipped-step backlogs, counted after the run** — a `--lint-only` run reports entries not linted, with no claims, not synthesised, each with its mode reason; a `--full` run reports none of them. Extract list-returning functions from `cmd_semantic`, `cmd_claims`, `cmd_synthesis` (callers and counter share them; `last_semantic` and `last_synthesis` take no run folder from the counter). Done when the new checks pass:
   - Expected: with the harness's history (a lint on 2026-09-10; `new-d` added and `old-a` re-reviewed after), the counter says `Not semantically linted: 2` with the `no semantic lint ran` reason; after the run folder gets a `lint-semantic.json` stamped later it says nothing for that queue (the post-step cut-off); claims with no index counts every entry, after an index is written it counts only the unindexed or revised ones; synthesis with a `completed` `synthesis.json` in the run folder counts nothing, with none counts the research entries added since the last answered one.
   - Failures: a `synthesis.json` with status `awaiting_approval` adds no synthesis line; the staged entry is never counted in these three; a malformed `lint-semantic.json` does not crash: that queue's line reads `not checked (<why>)`; the command writes no `semantic-scope.txt`, `claims-scope.txt` or `synthesis-scope.txt`.
   - Invariant: the pre-existing `semantic`, `claims` and `synthesis` checks in the file are unchanged and pass (they pin that the extraction kept each command's output).
   Trivial stakes: no

3. **Lint findings and semantic fixes awaiting** — a run whose lint found 2 broken links reports `Lint: broken links: 2` with `no fix step in this mode`, and a `--full` run `awaiting your approval`; the Needs you line gets its count. Reads `lint-mechanical.json`'s summary and `lint-semantic.json`; Step 5 text gets the `lint-fixes.txt` instruction (Decisions needed 2); Step 8 and the template get the count on the awaiting line. Done when the new checks pass:
   - Expected: summary with `broken_links: 2`, `orphans: 0`, `unquoted_yaml: 1` gives two lines (kinds above 0), none for `files_scanned`, `standalone` or `backlink_blocks_out_of_step`; with `lint-fixes.txt` present the reason is `awaiting your approval`; a `lint-semantic.json` holding 5 findings and `applied: 2` gives `Semantic lint findings: 3`; `--lint-json <last run's file>` adds `(from <id>)`.
   - Failures: no lint JSON, or one that does not parse → `Lint findings: not checked (<why>)`, and the file is not `nothing`; a summary with every kind 0 adds no lint line; `applied: x` or a missing number counts as 0 applied and the line says so (never crashes).
   - Manual: the `lint-fixes.txt` instruction and the Needs you count (Testing Decisions).
   Trivial stakes: no

4. **Dropped, failed and deferred sources, tier 4 included** — a run whose ingest skipped one source, failed one and deferred one names each with the reason the step returned. Reads `update.json` (`skipped`, `deferred`, `errors`) and `discover.json` (`deferred`); Step 1.5 text gets the tier-4 deferral write. Done when the new checks pass:
   - Expected: an `update.json` with 1 skipped (`thin content`), 1 deferred (`429`), 1 error (`item`, `message`) and a `discover.json` with 1 deferred (`tier 4: needs your review`) gives four lines, each with its URL or slug and the reason verbatim; discovery's `skipped` adds none.
   - Failures: an `update.json` that does not parse gives `Sources: not checked (update.json unreadable)`, never silence; an item with no reason gives `(no reason recorded)`; a step file absent (`--lint-only`) adds no source line and no `not checked` line (the mode does not run that step, which the tickets line's reason already says).
   Trivial stakes: no

5. **Buckets, pending and staged entries** — a run leaves tickets in two other readers' buckets, one in `mark`'s, 3 in `_inbox/pending/`, and 2 staged entries with `confirm_before_promote: false`: the section carries `Other readers' buckets, still to process: <folder> N, …` once, the pending and staged lines with their reasons; with the setting `true`, no staged line. Adds `intake_tickets` to `wiki-triage.py` (the `source:` rule, new function, searched for: found only `wiki-dequeue.py`'s inline loop, left alone) and loads `buckets()` and `me()` through `importlib`. Done when the new checks in `test_cycle_scope.py` and `test_wiki_triage.py` pass:
   - Expected: buckets `main` (this session), `other` (another bot), `money` (`mark`) holding 0, 4 and 15 tickets give one line `Other readers' buckets, still to process: other 4, money 15`; `main` holding 2 gives its own-bucket line with the table's reason (`update.json` absent: `this mode does not ingest`); pending 3 gives the pending line; `intake_tickets` returns each ticket once with its bucket and source and skips `README.md`, `_`-prefixed files and a `.md` with no `source:`.
   - Failures: a bucket folder that does not exist counts 0 and adds nothing; an intake README that does not parse falls to `buckets()`'s one-bucket default (its existing behaviour) and the command does not crash; no `promote-setting.txt` makes the staged line `not checked (no promote-setting.txt)`; `confirm_before_promote: true` adds no staged line.
   - Invariant: the existing `wiki-triage` bucket and route checks stay green (they pin `buckets()` and `me()` used unchanged).
   - Decisions needed 1, if taken: a discovery-checklists line, counted the same way, with its own `Expected:` and a `Failures:` for an absent `_inbox/discovered/` (0, no line).
   Trivial stakes: no

6. **`--brief` carries the line** — the brief report shows `Left undone: N — see the full report` or `Left undone: nothing` after Numbers. Done by the `wiki-report` text edit; manual: step 6 (Testing Decisions). Trivial stakes: yes — template wording in a skill file, no code branch; the evidence is the text read against the Fallbacks brief line.

7. **Eval cases red then green, docs, finish** — blocked by: 1 to 6. The `eval-case-writer` writes scenarios A and B from the requirement (`fresh`; Mark's go first, below); saved unchanged to `cases.json` with its `check.py` branch; one run proves them: `uv run python tests/skills/run_skill_test.py wiki-cycle --cases <A>,<B> --red-green <the commit before step 1>` (both models, as the README requires). Then the CHANGELOG entry, the wiki-cycle and wiki-report usage pages (what the section holds and where it comes from, pointing to the script's docstring, not copying its table), and the `PENDING.md` row (the old fallbacks and backlinks cases not re-run). The next step is the install SOP, a separate finish step. Done when the red-green command exits 0 with each of A and B `red then green` on both models:
   - Expected: on the old copy A and B fail (no Left undone section); on the new copy both pass: A's section lines equal the planted counts and the script's file, above Needs you, Needs you last; B reads `Left undone: nothing` above Needs you.
   - Failures: a case that passes on the old copy goes back to the writer (`replay`), not counted; the red-green run exits 1 and the run stops, the 8 sessions not repeated.
   - manual: the live read-only run on the two notebooks and the docs (Testing Decisions).
   Trivial stakes: no (the cases) / the docs lines are wording only

## Paid runs the plan expects

One red-green run, two new cases, both models, old and new copy: 8 headless sessions, each a `--lint-only` or clean run (steps 0, 3, 8; no workers). No full suite: none of the README's triggers fires (no model change, no runner or shared-script change, not a long-unrun suite, nothing wrong in real use). It runs only on Mark's go; cost to be read from the fallbacks change's red-green run, which was the same size.
