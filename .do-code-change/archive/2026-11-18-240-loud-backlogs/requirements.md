# Requirements: a cycle names everything it leaves undone (task #240, lesson #9)

## Facts

Source and request

- user confirmed (Mark, 2026-11-12, card #240, wiki `tasks/240-build-the-four-unbuilt-pre-mortem-lessons-into-llm.md:16,23`): "#9 in other lanes (silent backlogs, e.g. entries past review_after, reported loudly)"; each lesson is a code change, red then green, then install. #10, #11 and #12 are done (card lines 20-22).
- user confirmed (Mark, 2026-11-16, `checkpoints.md`, Decision 1), his words: "this is after we run, after we run everything should be comnpleted no? otherwise we should know about it and why?" Read as the rule of this change: at the end of every `/wiki-cycle` run, anything the cycle leaves undone, meaning any queue or backlog it owns that is not empty, is named in the cycle report with the count and the reason it was left (for example "this cycle mode does not refresh; run X"). No age rule, no threshold. Overdue entries are one case. Mark also said it is not a louder notification: one line in the cycle report, every cycle.
- wiki `project/troubleshooting/research-cycle-failures-we-hit-2026-04-to-10.md:42-46` (#9): "the same shape then fired in the decay lane: the 2026-08-01 semantic lint found >=30 entries past `review_after` and >=20 with none, clustered by ingest batch, because refresh had run only twice".
- earlier changes `2026-11-14-240-unfinished-run-check`, `2026-11-15-240-backlink-block-check`, `2026-11-15-240-report-fallbacks` (archive requirements read): the precedent for a cycle lesson is prose in `skills/wiki-cycle/SKILL.md` plus a line in `wiki-report`, a new wiki-cycle suite case run red then green, no framework-contract change, `⚠️ Needs you` stays the last section. The fallbacks change put its section before Needs you ("something that happened, not something waiting on the user") with "Fallbacks: none" so silence is not read as unchecked. The fallbacks change's Exclusions: "Not lesson #9 (silent backlogs)".
- wiki `tasks/245-agentic-design-refresh-the-320-entries-past-review.md:16` (Mark, 2026-11-13): refreshing agentic-design's overdue entries is its own task, in batches, on his go. This change only reports.
- found in `skills/wiki-cycle/SKILL.md:47`: `--report-only` "runs 8 from the last run's JSON", so a count in its report is the last run's, not read fresh.
- found by grep of `skills/wiki-*/SKILL.md` for "skill suggest" and "suggestions": 0 matches. Skill suggestions are not a queue the cycle owns.
- found in `wiki-report/SKILL.md:301`: `--brief` shows only Numbers, Recommendations and Needs you, so anything placed in a new section is not in a brief report.

Settled by Mark (checkpoints.md, 2026-11-16), each a requirement of this change

- user confirmed (Decision 2, Mark, Discord: "A"): the report gets a new section **"Left undone"** just above Needs you (so Needs you stays the last section), one line per non-empty queue (queue, count, why it was left, the way out where there is one). When nothing is left it reads "Left undone: nothing", so silence is never read as unchecked. Items already in Needs you stay there.
- user confirmed (Decision 3, Mark, Discord: "A"): the five backlogs a mode skips on purpose, entries past `review_after`, entries with no `review_after`, entries not yet semantically linted, entries with no claims, and entries not yet synthesised, each get a count and a reason (for example "this mode does not run refresh; run `/wiki-cycle --full`"). The counts are worked out fresh in every mode, from dates and the scope script, without running the skipped step.
- user confirmed (Decision 4, Mark, terminal: "A"): each source the run dropped, failed or deferred is named in Left undone with its reason, as the worker or step returned it, tier-4 discovery deferrals included. Counts alone are not enough.
- user confirmed (Decision 5, Mark, terminal: "A"): every kind in `lint-mechanical.json`'s summary with a count above 0 is named with its count and a reason ("no fix step in this mode" or "awaiting your approval"), and the "lint fixes awaiting approval" line gets its count.
- user confirmed (Decision 6, Mark, terminal): "If its not your bucket you dont really care. Naming them once with the left to be processed is fine". So other readers' buckets and the user's `mark` bucket are named in one line in Left undone, each bucket with the count still to be processed. No owner, no reason, no item list.

Inventory: every queue or backlog the cycle owns or touches (evidence from `SKILL.md` = `skills/wiki-cycle/SKILL.md`, `REPORT` = `skills/wiki-report/SKILL.md`, scope = `scripts/wiki-cycle-scope.py`)

"Report names it" means: count and reason, in the report.

| # | Queue | Can a run end with it non-empty, in which modes | What the report says today | Gap |
|---|---|---|---|---|
| 1 | Entries past `review_after` | Yes, every mode. Counted only by `--full`/`--refresh-only` (Step 7, `SKILL.md:177`, mode table `:43`); other modes skip it (`SKILL.md:47`) | `--full` only: Stale entries table `REPORT:163-170`, Numbers row `:261`. Not in Needs you (`:279-294`, `SKILL.md:179`). The 2026-11-10 `--ingest-only` report (agentic-design) says nothing; 607 were past due | Not named in 5 of 7 modes; no reason line even in `--full` |
| 2 | Entries with no `review_after` | Yes, every mode | Nothing. The lint finds them (`wiki-lint-mechanical.py:727-730`) but its JSON summary has no key for them (`:1487-1505`) and `REPORT:182-190` has no row | Never named |
| 3 | Entries not yet semantically linted (added or revised since the last semantic lint) | Yes in every mode but `--full` and `--lint-only --semantic` (`SKILL.md:40`, `:146`; scope `:226-237` computes the list) | Only the date "Last semantic lint" (`REPORT:263`) | No count, no reason |
| 4 | Entries with no claims, or revised since the index | Yes in every mode but `--full`, `--claims-only` (`SKILL.md:43`, `:167`; scope `:240-258`) | Only "Last claims extraction" date (`REPORT:264`) | No count, no reason |
| 5 | Research entries not yet synthesised | Yes in modes that do not ingest: `--lint-only`, `--report-only`, `--refresh-only`, `--claims-only`, `--discover-only` (`SKILL.md:44`, `:169`; scope `:278-295`) | Nothing for the non-ingesting modes | Not named |
| 6 | Synthesis awaiting approval | Yes, unattended runs (`SKILL.md:175`) | Needs you with entry count and path (`REPORT:292`, `SKILL.md:179`) | None |
| 7 | Mechanical lint findings left unfixed (broken links, orphans, missing frontmatter, missing tier, others in the JSON summary) | Yes. The lint runs in most modes (`SKILL.md:39`); the fix step (Step 5, `:154`) runs only in `--full`, and then only what the user approves | Lint issues table `REPORT:182-190` lists 5 kinds with counts, "Clean" if zero; no reason; not in Needs you. `SKILL.md:144` names parts the lint could not check (exit 3). The JSON has 8 more kinds (`wiki-lint-mechanical.py:1489-1504`, e.g. `unquoted_yaml`, `design_behind`) that the table does not list | Counts for some kinds, no reason, others never named |
| 8 | Semantic lint fixes awaiting approval | Yes, `--full` | Needs you "lint fixes awaiting approval — where they are" (`REPORT:291`) | No count |
| 9 | Backlink blocks out of step | Yes | Needs you with count, first 3 pages and way out, only when above 0 (`REPORT:289`, `SKILL.md:179`) | None |
| 10 | Pending queue `_inbox/pending/` | Yes, in `--discover-only` and `--prompt-for-urls`, whose mode column has no triage (`SKILL.md:35`, queued items at `:95`); `--no-confirm-discovery` defers tier 4 (`:97`) | Pending work row with a count and an action (`REPORT:153`); tier-4 deferrals are counted in the glance table (`:126`) | No reason for what is left; deferred tier-4 sources not listed in Needs you |
| 11 | Tickets this session reads (its own bucket, `SKILL.md:99`) that ingest failed, skipped or deferred | Yes, any mode that ingests. Workers return skipped and deferred items "with reasons" (`SKILL.md:113`); a failed item is "failed with the reason" (`:107`) | Counts in the Update row (`REPORT:126`). Needs you names only Save as PDF and retry items with their cards (`:284,286`) | Items failed, skipped or deferred for any other reason are counted, with no reason in the report |
| 12 | Tickets in other readers' buckets, and in a bucket the user reads (`mark`) | Yes, every mode with triage; never ingested by this session (`SKILL.md:99`) | Pending work row "N per bucket", action "Each bucket's reader ingests it" (`REPORT:156`) | Count only in the Pending-work table; to be one line in Left undone with each bucket's count (Decision 6) |
| 13 | Staged entries in `_inbox/proposed/` | Yes. With `confirm_before_promote: true` every mode leaves them (`SKILL.md:49,156`); with `false` entries staged before this run still wait (`SKILL.md:163`) | Pending work count (`REPORT:154`). Needs you "N entries to promote" only when the setting is true (`SKILL.md:179`, `REPORT:282`) | With the setting false, a leftover staged entry has no Needs you line (the text does not settle whether anything else names it) |
| 14 | Entries held by the checker | Yes | Needs you with the report path (`REPORT:283`) | None |
| 15 | Staged entries the checker did not read (a sample, `SKILL.md:126`) | Yes, by design: "by default all of them" | Not named | Not a gap by default; named only if a notebook sets `sample_every` above 1 (not read: the config file) |
| 16 | Email candidates not approved | Yes, unattended runs (`SKILL.md:97`) | Needs you with count and "an unattended run" (`REPORT:290`) | None |
| 17 | Drive files left unread | Yes (`SKILL.md:81`) | Needs you with each name and why (`REPORT:287`) | None |
| 18 | Pages no fetcher can get (Save as PDF), PDFs not matched | Yes | Needs you with link and folder (`REPORT:284,285`) | None |
| 19 | Items left for retry | Yes | Needs you with link, reason and task card (`REPORT:286`, `SKILL.md:109`) | None |
| 20 | Unfinished earlier runs | Yes | Needs you; nothing when none (`SKILL.md:63,179`) | None (closed by lesson #10) |
| 21 | Discovery checklists in `_inbox/discovered/` | Yes | Pending work "N checklists" (`REPORT:155`) | Count only; same class as 10 |
| 22 | Concept gaps | Yes, in every mode | Pending work row with count and action (`REPORT:157`, data source `:81`) | No reason; not a queue this cycle works down |
| 23 | Hubs behind their tag | Fixed in the cycle (Step 5.6, `SKILL.md:165`) | Lines added named | None |

Rows 1, 2, 3, 4, 5, 7 (partly), 8, 10, 11, 12, 13 and 21 are the gaps. Rows 6, 9, 14 and 16 to 20 are already named with a reason. Rows 15, 22 and 23 are not changed.

Real numbers, read-only on 2026-11-16 (method: a grep of the frontmatter line `review_after:` for a date up to 2026-11-15, folders `sessions/` left out; counted, not read entry by entry)

- agentic-design: 607 of 1,731 pages with a `review_after` are past it. 599 are under `wiki/research/`; 272 fell due between 2026-11-01 and 2026-11-15; 437 more fall due by 2026-12-16. On 2026-10-30 the refresh scan said 320 of 1,602.
- agentic-design stored lint (`_inbox/reports/lint-report.md:19`): "missing lifecycle fields=0".
- llm-wiki-bootstrap's notebook: 6 past `review_after`.
- agentic-design's `_inbox/pending/` held 2 tickets, `intake/ai-money/` 15 (oldest 2026-10-05) and `intake/agent-builder/` about 50, by file listing, not read ticket by ticket.
- Earlier incident for comparison: 2026-08-01, 30 or more past, 20 or more with none.

Follows from a stated rule (shown at confirmation, not asked)

- follows from Mark's rule (2026-11-16, above): every queue in the inventory that can be non-empty at the end of a run is named once, with count and reason, in every mode that writes a report; an empty queue is not listed; the line carries no age or threshold. Other readers' buckets are the one exception to "reason" (Decision 6).
- follows from Mark's rule (2026-11-16, above), "otherwise we should know about it and why": the reason in each line says why it was left (for example "this mode does not run refresh" or "the setting says wait for the user") and the way out where there is one.
- follows from the same rule: a leftover staged entry is named whatever `confirm_before_promote` says (row 13); today only a `true` setting names it.
- follows from Mark's rule (CLAUDE.md "Don't": "one cycle report whose last section is `⚠️ Needs you`"; `REPORT:303`): Left undone stays above Needs you; Needs you remains the last section.
- follows from Mark's rule (tests/skills/README.md, 2026-10-17; card #240): the change ships once its new suite cases run red then green; then the SOP (`-RefreshOnly`, `--mode status` current, CHANGELOG, usage pages).
- follows from Mark's rule (wiki-refresh "Don't auto-update entries", and #245 "on his go"): the change reports and changes no entry and runs no step the mode skipped. Counting reads dates or a scope list only.
- follows from the lint's and refresh's convention (`wiki-refresh/SKILL.md:187`, lint `:193-194`): `sessions/`, `_inbox` and `tasks/` pages are not counted for "no review date" (task cards are rough notes, Mark 2026-10-12).
- follows from `skills/wiki-refresh/SKILL.md:185` ("Don't treat overdue as wrong"): the line says what is overdue, never that an entry is wrong.
- follows from Mark's rule (lean skills, 2026-09-15): the skill text grows by as little as it takes; detail goes to `reference.md` or the usage page.
- follows from Mark's rule (Entries say only what the source says): a count in the report is read from the entries or scope list, never estimated; a `--report-only` run says its counts come from the last run.

## Exclusions

- No refreshing, re-reading or re-dating of any entry, and no step run in a mode that does not run it today: clearing agentic-design's 607 is task #245, on Mark's go, in batches.
- No change to the review cadence or to when `review_after` is written.
- The rollback bug (`wiki-rollback.py` writes `review_after` = today, wiki `project/architecture/50-quality-and-promotion.md:268`) is not fixed here.
- No change to a queue the report already names with count and reason (rows 6, 9, 14, 16 to 20).
- No age rule and no threshold on any queue (Mark, 2026-11-16: the test is "left undone", not "old").
- No ingesting, triage or promotion of other readers' buckets: the cycle names them once, with counts, and never works them. No owner, reason or item list for them (Decision 6).
- No new lifecycle rule for skill files: `wiki-refresh` Step 1b keeps its own Skills table.
- No change to the framework-contract docs unless the cycle-step contract needs a new field (not shown to be needed; see the last section).
- No change to the lint's exit codes or to which findings are warn-only.
- No louder notification (no ping, no message outside the report), as Mark answered.

## Decisions

All settled by Mark on 2026-11-16 (answers in `checkpoints.md` and in the Facts above); none is open.

1. Scope is whatever the run leaves undone, every non-empty queue it owns, named with count and reason, no age rule: "this is after we run, after we run everything should be comnpleted no? otherwise we should know about it and why?"
2. New "Left undone" section just above Needs you; "Left undone: nothing" when empty (Mark: "A").
3. The five backlogs a mode skips on purpose each get a count and a reason, counted fresh without running the skipped step (Mark: "A").
4. Each dropped, failed or deferred source is named with its reason, tier-4 deferrals included (Mark: "A").
5. Every lint finding kind above 0 gets a count and a reason; the fixes-awaiting line gets its count (Mark: "A").
6. Other readers' and `mark` buckets: one line naming them once, each with the count still to be processed (Mark: "If its not your bucket you dont really care. Naming them once with the left to be processed is fine").

## Not read or not done (goes to the plan)

- `~/.claude/agents/product-manager-reading-list.json`, `.claude/wiki-config.json` and the agent's journal were not read; paths came from the request.
- `skills/wiki-triage/SKILL.md` was grepped, not read in full; `skills/wiki-refresh/SKILL.md` and `framework-docs/cycle-step-return-format.md` were not read in this run (cited as earlier records quote them). Whether a new counter in a step's `summary` is a contract change is not settled.
- `wiki-cycle-scope.py` read at lines 200-330 only; `wiki-lint-mechanical.py` at 1480-1520 only (plus earlier lines cited from the previous draft). The lint's report for the missing-lifecycle count lives in its report file, not its JSON; the way to count it in a run is left to the build.
- Real numbers in "Real numbers" are from the previous draft's greps; this rewrite did not repeat them.
- Whether an `update.json` failed or skipped item stays in its bucket after the run was not settled from the text (`SKILL.md:107,113`); row 11's "Can be left" rests on the text saying items are skipped and deferred.
- `wiki-checker-config.json` (`sample_every`) was not read; row 15 assumes the default of all.
