# Red-team: plan.md revision 5 (240-loud-backlogs, round 6, final check)

The orchestrator wrote this from the red-team's report. The red-team was a fresh architect running strategy-red-team, with one red-team-reviewer (haiku) spawn. It ran read-only: the readonly-guard check passed (642 files, HEAD unchanged). Rounds 1-5 are in plan-red-team-round1..5.md.

## Round-5 items: resolved against the code, or turned into a Decision?
- **Rank 1:** resolved in the text (plan:83, :169). Two new inconsistencies are covered in KA4.
- **Rank 2:** resolved. The way-out text is true against SKILL.md:152 and :154. Decision 10's disclosure is inaccurate (KA1).
- **Rank 3:** resolved as a plan.
  - The lint's `completed` conditions are at wiki-lint-mechanical.py:892-910: files scanned, qmd present, the wiki is a qmd collection, the index is not empty, and at least one skill or agent sits under `~/.claude`.
  - check.py setup() (164-214) meets the first four.
  - Literal defects remain (KA5).
- **Rank 4:** resolved. A gap remains for an unknown mode with no step files (KA3).
- **Rank 5:** resolved.
- **Rank 6:** disclosed as Decision 2. This is a choice.
- **Rank 7:** done, with one "blocked by" gap (minor list).
- **The seven minor items:** all in the text.

## Kill-assumptions (ranked)

### KA1. A newer lint with 0 findings silences an older run's findings with no line
**Claim:** "a newer lint with 0 findings replaces an older one's unresolved findings, and the line says it reads only the newest" (plan:58, :236).

**Fails if:**
- 0 findings print no line, so nothing carries that warning.
- plan:279 says "gives no semantic-backlog line", which contradicts the claim.
- A later lint that covers a single new entry does the same.
- requirements:94 says anything left undone is named.

**Kill criterion:** older unresolved findings exist and nothing is printed about them.

**Cheapest test:** an older run with 5 unresolved findings and a newer run with 0; assert a line exists.

**Fix class:** plan error in the text: state the silence plainly and remove the contradiction. The choice for Mark stays the form of Decision 10. A third form is worth offering: when the newest lint has 0 findings, still print `Semantic findings from <older id>: N, superseded by a newer lint; not read`.

### KA2. The discovery-checklist row says "not reviewed yet" and "the next /wiki-cycle shows each"
**Fails if:**
- The move to `_inbox/done/` (wiki-discover SKILL.md:220) is a model step and can be skipped. A reviewed checklist would then read "not reviewed".
- No step ever shows an older checklist (wiki-cycle SKILL.md:83, :93). wiki-report SKILL.md:155 names the action "Review candidates, approve/reject".

**Fix class:** plan error. State only what is known: "still in `_inbox/discovered/` (discovery files a processed one in `_inbox/done/`); whether it was reviewed is not recorded". Drop the way-out claim.

### KA3. With an unknown mode, the file can read `Left undone: nothing`
**Fails if:** the mode can't be read, every count is 0, and absent step files print nothing because "the mode runs it" can't be evaluated. The header then reads `nothing`, and Needs you and the Numbers row follow it. 16 of 32 live scratchpads carry no `**Cycle**` line.

**Cheapest test:** a scratchpad with no mode token and an empty run folder; the file must not read `nothing`.

**Fix class:** plan error. Add the queue line `Mode: not checked (cannot read the mode from scratchpad.md); steps that left no file are not known`, so the header is never `nothing`.

### KA4. The Needs-you rule disagrees with its invariant
**Fails if:**
- **(a)** plan:83 drops the line for "another reason (no usable findings list)", yet a partial lint with a usable list reads `not checked (…partial)`, and plan:169 says the line is absent only for 0 findings or no lint.
- **(b)** The source of N is never stated, while plan:13 says the model computes no count.
- **(c)** Today's generic line also covered mechanical findings (SKILL.md:154). The reworded line is semantic-only, which narrows "keeps every line it has today" without saying so.

**Cheapest test:** `--full` with a partial lint holding 5 findings keeps its Needs-you line.

**Fix class:** plan error, three sentences:
- The only exception is an unusable findings list.
- N is copied from the Left undone line.
- The narrowing to semantic-only is named.

### KA5. Case B's and case A's literal expectations
**Fails if:**
- `files_scanned` (always at least 1) and `standalone` are summary keys (wiki-lint-mechanical.py:1488, :1491), so "every summary count 0" can't pass.
- wiki/README.md is collected by the lint and is an orphan.
- B's earlier folders need dates other than the cycle's own (check.py:2716-2717).
- Case A's `Past review_after: 2` should read 13: 11 seed entries are dated 2026-04 and 2026-05, so A's builder must reset them.

**Fix class:** minor, fix in implementation. The unpaid fixture test catches each one.

## Minor, fix in implementation (no re-plan)
- **Interim removal:** move it from step 4 to step 6. Between those steps HEAD would print `nothing` falsely, and a -RefreshOnly in that window would install it.
- **Step 5 blocked-by:** add step 2.
- **`--brief`:** add the interim "none" line and the two no-file `not checked` states to the brief rule.
- **Refresh "ran" wording:** "refresh ran; this count is from the dates now".
- **Staged entries:** `Staged entries: not checked (no promote-setting.txt)` must keep its count.
- **Cross-check:** key it on the named step files, never a `*.json` glob (models.json and cost.json aren't steps).
- **"beside":** define it in `--semantic beside lint-only`.
- **plan:19:** say "presence of step files".
- **Part 1 paid case:** the expected lines come from the writer's brief.
- **plan:85:** the header sentence (steps 2 and 5 both carry skill text).
- **Decision 10:** put the way-out sentence on the earlier-run findings line.

## Reviewer attacks judged noise or not confirmed
- The synthesis scope file in B.
- Ticket lines in an unknown mode.
- last_semantic ignoring status: a real property, but it prints nothing false.
- "changed none" for refresh.
- The _INDEX/HOME.md worry: the unpaid test catches it.

## What holds up
- The lint conditions match the code.
- The mode table agrees with SKILL.md:28-45, and `--lint-only` runs steps 0, 3 and 8.
- The pending line reads no step file.
- The unknown-mode and mismatch rules keep the counts.
- The Numbers row takes the Left undone number (wiki-report SKILL.md:65-72 counts every page).
- Case A's precedent carries the `**Cycle**` and `- Mode:` lines.
- The old ordering checks hold.
- The minor-list fixes and the renumbering are consistent.
- The way-out text is true.

## Could not assess
- Whether B's real lint reaches completed with 0 counts (needs the unpaid test).
- The resume at Step 8 (needs the first paid session).
- Live counts outside the repo.
- Whether Step 4 writes a 0-findings lint-semantic.json on a routine empty-scope `--full`. If it does, KA1 fires routinely.
- How the model writes the mode line.
- Whether map-compile creates HOME.md or a concept-gaps page in B.
- **No standing rule found:**
  - the interim "none" header;
  - the tier-4 silent miss (Decision 2);
  - the `--today` default and `(no reason recorded)`;
  - a missing bucket folder counting 0;
  - the Numbers row defaulting to 0;
  - the drift test covering 5 of 9 modes;
  - the regex fallback;
  - cmd_retry_list left alone.
- **The case writer's brief:** per tests/skills/README.md:17 and :21, the writer works from the requirement and its answer is saved unchanged. The plan's common-check table should reach the writer as a constraint, not as a fixed answer.

## Plan errors versus choices
- **Plan errors (none needs Mark):** KA2, KA3, KA4, the text half of KA1, and KA5's literal fixes.
- **Choice for Mark:** the form of Decision 10: newest only, every lint back to the last answered one, or the third "superseded" line. The other eleven Decisions are fine as written.

## Complete enough to build?
Not as written. Its own invariant ("a false line is never written") fails in four places: KA1-KA4. Each needs a one-to-three-sentence correction. With those applied, nothing else was found that would print a false or silent line. The plan is one small revision from buildable, and it needs no further full red-team round if that revision is limited to these sentences.

VERDICT: KILL-ASSUMPTIONS FOUND
