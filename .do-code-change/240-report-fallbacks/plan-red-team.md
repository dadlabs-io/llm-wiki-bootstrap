# Red-team: every /wiki-cycle fallback is recorded in `fallbacks.txt` and shown in a `## Fallbacks` section of the report (task #240, lesson #12)

Written by the orchestrator from the red-team's report (architect running `strategy-red-team`; reviewer `red-team-reviewer`, haiku, which ran in the background despite the flag; the architect re-checked check.py:786, check.py:827, wiki-qmd-query.py:290 and the `--brief`/Cost-line behaviour in wiki-report/SKILL.md). Read-only guard: PASS (621 files, HEAD unchanged).

## Kill-assumptions (ranked)

1. **Claim:** `WIKI_SEARCH_MODE=keyword` puts the sandbox in keyword mode, so case `keyword-machine` tests that a keyword machine is not listed (plan line 38, step 4).
   - Fails if (a) the case cannot test the exclusion: it runs `--ingest-only`, and the depth check that produces `skipped (keyword search)` runs only in `--full` (SKILL.md:112); old copy red only for the missing section, new copy `Fallbacks: none` passes whether or not the model understood keyword mode, the same pass condition as `clean` (page 95 History: red-green finds cases that do not test the change).
   - Fails if (b) the negative check "no line naming keyword search" trips on an honest line: `--reindex` on a keyword machine prints "reindex: qmd update done; keyword machine, no embed" (wiki-qmd-query.py:290).
   - Fails if (c) the env never reaches workers or Bash children (mechanism real: run_skill_test.py:320-322, `_wiki_config.search_mode` reads the env first :465, wiki-search's keyword cases use it; not shown for wiki-cycle sessions or their workers; host `~/.claude/wiki-config.json` not pinned).
   - Evidence to get now: `wiki-qmd-query.py --preflight` and `--reindex` under the env; after the paid run, `searches.jsonl` `mode`. Kill criterion: preflight does not say keyword, or a worker search logs `mode=full`. Cheapest test: one offline `--preflight` call.
   - Fix class: (b) plan error (the check reads only a Fallbacks-section line); (a) choice: accept a weak case, add a `--full` keyword variant (costly), or drop the case.

2. **Claim:** `Fallbacks: none` in the clean case is stable, on a full-mode machine (step 1).
   - Fails if (a) the sandbox does not pin the mode: `clean` and `unreadable-ingester-config` inherit the host's `search_mode` (no WIKI_GLOBAL_CONFIG, check.py:207-213).
   - Fails if (b) a legitimate fallback fires in a clean run: exit-75 re-run (parallel Sonnet/Opus threads share one qmd slot directory, 900 s max wait; reviewer cites wiki-qmd-query.py:165-168, 293-302, 849, not re-read), a 429, a transcription.
   - Evidence to get now: which sources `clean` queues and whether any is live-fetched; saved events of earlier `--ingest-only` runs for exit 75 or `Fallback:`. Kill criterion: more than one fallback line in earlier clean runs' events. Cheapest test: grep over saved `.results` events.
   - Fix class: (a) plan error (pin `WIKI_SEARCH_MODE=full`); (b) choice (accept a flaky bar, or a source with no live fetch).

3. **Claim:** the new kind queues a source via the quick-run preparation and reuses `_prepare_models`' `ingester_config_broken` "on every case" (line 39).
   - Fails if (a) the quick-run dispatch tuple at check.py:786 (`("ingest-only", "scratch", "models")`) is not given `fallbacks`; (b) the case omits `"ingester_config_broken": true` (written only when the flag is set, check.py:266-273).
   - Kill criterion: the kind absent from the tuple. Cheapest test: a free offline `setup`/`prepare` smoke (page 95 Spending discipline asks for one before a paid run; the plan has none).
   - Fix class: plan error (add to the tuple, set the flag, add an offline check of `_prepare_fallbacks`/`_check_fallbacks`).

4. **Claim:** an absent `fallbacks.txt` reads `not checked`, never `none`; `--resume` creates the file only when a fallback is recorded.
   - Fails if (a) one label covers two states: a rule-era run resumed after its Step 0, with nothing found later, prints "not checked" though the rule was in force; the resume case's old-copy red cannot tell `not checked` from `none`.
   - Fails if (b) `--brief` and the standalone report show no Fallbacks section (SKILL.md:290: brief shows Numbers, Recommendations, Needs you); "Fallbacks: none" asserts only that none were recorded.
   - Evidence to get now: read `tests/skills/wiki-cycle/fixtures/resume/scratchpad.md`. Kill criterion: the fixture's later steps run under the new rule.
   - Fix class: choice (one label or two; whether `--brief` shows a one-line Fallbacks status; "none" or "none recorded").

5. **Claim:** the worker note format `Fallback: <expected> -> <used>, <why>` and its copy are safe, the copy manual.
   - Fails if (a) a shell `echo ... >> fallbacks.txt` or a `->` triggers the stray-file alarm (global CLAUDE.md, claude-code #76774); (b) the copy and the departure line have no test (plan says so).
   - Fix class: (a) plan error (a note format with no `>`); (b) accepted trade-off.

6. **Claim:** the departure line's rendering is defined (lines 21, 24).
   - Fails if an implementer cannot write one rendering rule: the file's `why` begins `departure from the stop-and-report rule:` while the report line is `- <step>: DEPARTURE from the stop-and-report rule: ...` beside the general `- <step>: expected ...; used ...; why ...`.
   - Fix class: plan error (state one rendering rule).

## What holds up

- `framework-docs/cycle-step-return-format.md` untouched: its tree lists `promote-setting.txt` and cost files but not `unfinished-runs.txt` (:44-46); Invariant 5 (:291) concerns step JSON vs sidecars, not side files; wiki-report/SKILL.md:104 already reads `cost.md` and `unfinished-runs.txt`.
- The missing-agent seam is rightly avoided (agent installed at user level; sandbox copy check.py:186); the unreadable-ingester-config seam is real (`wiki-cycle-scope.py` models falls back with a warning, :417-497).
- "No script changes" holds: check.py's `*.json` globs (:2533), the zero-byte check (:2940-2942), `wiki-cycle-scope.py` never lists the run folder; the Step 9 keep-list edit is a condition (SKILL.md:178), caught by `clean`'s committed-and-present check.
- Keyword on a full machine as a departure, a keyword machine not listed: agrees with the 2026-09-13 and 2026-10-02 decisions and Decision 1.
- Resume does not repeat Step 0 (SKILL.md:67).

## Could not assess

- no standing rule found: `--brief` left unchanged (Decision 3's "silence cannot be read as unchecked" bears; kill-assumption 4).
- no standing rule found: the standalone `/wiki-report` omits the section (page 95 "Nothing reads clean that checked nothing" bears loosely; the Cost line is the precedent).
- no standing rule found: no script changes and no enforcement script (requirements Exclusions cover it).
- no standing rule found: regression cases rerun on Sonnet only.
- no standing rule found: the depth check's `skipped (keyword search)` is not a fallback.
- Rules that bear and the plan complies with: keyword on a full machine (stop-and-report kept); shipped folders edited (Mark asked for the framework change); the costly run waits for Mark's go.
- Not assessed: `WIKI_SEARCH_MODE` reaching a live session's workers (1c); exit-75 frequency in a clean run (2b); `fixtures/resume/scratchpad.md`; the wiki-report INSTALL-INVENTORY row.
- Page 30's run-folder list ("Nothing else", line 42) and its Known-gaps line for #12 (line 182) need an update in the notebook after the change (the finish's living-page step).

VERDICT: KILL-ASSUMPTIONS FOUND
