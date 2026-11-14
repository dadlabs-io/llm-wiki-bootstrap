# doubt-log — 240-backlink-block-check (steps 1-2)

CLAIM: "backlink_blocks_out_of_step in wiki-lint-mechanical.py returns one row per entry whose BACKLINKS-AUTO block disagrees with the pages that really link to it, by the plan's one link rule and entry set, and no row for any other page."
Cycle 1 (one doubt-reviewer, haiku tier, artifact lines 280-347 plus the plan's rule as contract):
- a marker quoted in inline code or a fence made the lint cut the page's text at it (links after it dropped) and count the page unclosed — actionable; fixed by stripping code before looking for blocks, red test `test_marker_quoted_in_inline_code_is_neither_a_block_nor_unclosed` first (the freeze's red command exited 1 before the fix), frozen, then green;
- `f.resolve()`/`read_text` not inside a try, so a directory named `x.md` raises — trade-off: the lint's own Pass 3 (`f.read_text(...)` at the orphan pass) already raises on the same input before this code runs, so a guard here would not keep the lint alive; left, named here;
- parentheses in a target file name (`a(b).md`) are not read as links — trade-off: the script's old rule (`[^)]+\.md`) did not read them either and the plan's rule says "no whitespace" only; left, named for the review;
- `.search` takes the first block, `.sub` removes all blocks (two complete blocks on one page) — noise: the rebuild itself writes at most one block and replaces the first; a second block is outside the contract;
- a marker quoted in code counted by the raw `count()` for "unclosed" — actionable, same fix as the first finding (the counts now run on the code-stripped text);
- a dot-directory (`wiki/.x/y.md`) stays in the entry set — trade-off: the script's own entry rule is a file-name test (`p.name.startswith(".")`) and the plan words it "files whose name starts with `.`"; both agree.
STOP: trivial findings (cycle 2 not spawned: the one changed line is covered by the new frozen test and the whole file's 41 checks).

Step 2 (wiki-reciprocate-backlinks.py): the same link rule, the same code-then-block-then-stray-START order and the same `_inbox` exclusion were written to the contract cycle 1 examined and carry its findings; no separate cycle (the behaviours are each pinned by a frozen red-then-green test). Decision recorded for the reviewer: a START with no END makes both scripts ignore every line after it as links (the lines are the stray block's, not the author's), which keeps lint and rebuild in agreement on that page.
