# Step 5 checklist (manual: step 5), file:line in the working tree after the edit

1. Cycle Step 5 order `--show`, apply, `lint-fixes` (zero ids included, also when Step 4 was skipped), re-run the mechanical lint, then Step 5.5: skills/wiki-cycle/SKILL.md:154 (heading), :156 (show, ids from the script), :157 (apply, framework-contract rule kept), :158 (record), :159 (re-run, stamp after the record), :161 (Step 5.5).
2. Cycle Step 8's Needs-you list names the semantic findings line in `/wiki-report`'s wordings instead of "fixes awaiting approval": skills/wiki-cycle/SKILL.md:192.
3. Needs-you wording 1, `<N> semantic lint findings awaiting your approval — <run-folder>/lint-semantic.md` (fixes record exists, N above 0): skills/wiki-report/SKILL.md:303.
4. Needs-you wording 2 for `--lint-only --semantic`, `<N> semantic lint findings, applied or declined not recorded (no fix step in this mode) — <path>` (round 8 minor item 4): skills/wiki-report/SKILL.md:304.
5. Needs-you wording 3, `<N> semantic lint findings, applied or declined not recorded — <path>` (no fixes record: the fix step left none, unreadable, or a partial or unreadable-mode line with no lint-fixes.txt in the folder): skills/wiki-report/SKILL.md:305.
6. N copied from this run's `- Semantic findings: N …` line, never computed, earlier-run lines are not this line: skills/wiki-report/SKILL.md:302.
7. Nothing printed for 0 findings, a record covering every finding, no semantic lint, or a no-count `Semantic findings: not checked (…)` line; the count-less generic line `lint fixes awaiting approval — <run-folder>/lint-semantic.md` kept when there is no `left-undone.txt`; the narrowing to semantic findings stated: skills/wiki-report/SKILL.md:307.
8. The interim Part 1 form is untouched (removed in step 6): skills/wiki-report/SKILL.md:317 (the `--brief` rule, which names the interim "none" header) and the script's INTERIM_LAST.
9. Skill frontmatter still loads: `_entry_checks.check_frontmatter_loadable` on skills/wiki-cycle/SKILL.md and skills/wiki-report/SKILL.md both returned `[]` (run in step 5).
