## Red-team: 243-framework-docs-master (local/ folders, practice-page links, notebook moves and repoints)

Written by the orchestrator from the red-team's report (a fresh `architect` instance running `strategy-red-team`, with one `red-team-reviewer`); `readonly-guard.py check --step red-team` exited 0 (694 files compared, HEAD unchanged) before this file was written.

Run notes (the red-team's): the reviewer was one `red-team-reviewer` (haiku), spawned unnamed. The red-team re-checked three of its attacks against the code and the notebooks (marked "verified by me"). The reviewer says it went past its read budget.

### Kill-assumptions (ranked)

- **Claim:** "The scaffold creates `wiki/project/best-practices/local/README.md` in every new wiki, also with `--project-folder none` ... It uses the same helper" (Implementation Decisions; step 2).
  **Fails if:** `--project-folder none` is meant to leave no `project/` folder, and `local/` makes one. `taxonomy_for("none")` returns only `research` entries plus `sessions` (`scripts/_wiki_config.py:126-135`). The next-steps text at `scripts/new-wiki.py:1296` treats `none` as no project knowledge. `WIKI_FOLDERS` (`new-wiki.py:1040-1050`) will not list the new folder.
  **Fails if (second condition):** the README has no frontmatter. `wiki-lint-mechanical.py:707-708` flags `tags` missing for every page without the key and is not guarded by `is_exempt` (the guards at 701 and 712 cover only the source and body checks). A shipped README with no `tags` therefore lands in the missing-tags backlog of every new wiki and of every other wiki that has a `local/` folder. The plan never says the README carries frontmatter.
  **Evidence to get now (verified by the red-team for the first half):** run `wiki-lint-mechanical.py` on a temp wiki holding a frontmatter-less `project/best-practices/local/README.md`; read `is_exempt`; read the `none` branch of `skills/new-wiki/SKILL.md`.
  **Kill criterion:** the temp wiki's lint reports the README as missing tags or flags the unexpected `project/` folder, or the skill text promises that `none` creates no `project/`.
  **Cheapest test:** a Phase B run with `--project-folder none` into a temp target, then the mechanical lint over the result.
  **Fix class:** split. Plan error: the shipped README carries valid frontmatter that passes lint, and step 2 gets a test that lints the scaffolded wiki clean. Choice for Mark: whether `none` still yields a `project/best-practices/local/` folder (always, or only when `project_folder != none`).

- **Claim:** "`--phase docs` goes through `seed_toolset`, so it creates the stub too ... A dry run writes nothing and reports `would create` or `kept`."
  **Fails if:** `seed_toolset` returns at `scripts/_install_tooling.py:225-226` on `dry_run` before any later code runs, so a call placed after the file copy can never produce `would create`; `phase_docs --check` (`new-wiki.py:790-803`) reads only the status dict, so the `local` key is invisible to the check unless added before the early return.
  **Evidence to get now:** read `_install_tooling.py:216-234` and `phase_docs`; list every caller that prints or counts the dict `seed_toolset` returns.
  **Kill criterion:** a caller treats an extra key, or a non-empty `local` result, as "something changed".
  **Cheapest test:** step 1's own dry-run check, written first.
  **Fix class:** plan error: state the helper's dry-run branch and its position relative to the early return; the stub status is computed before the return and never feeds `state` or the exit code.

- **Claim:** "Every agentic-design link into the framework docs (128 links in 84 files) is repointed ... 53 mentions of `architecture-decisions` repointed" (step 5; step 9).
  **Fails if (counts, verified by the red-team):** `architecture-decisions` appears in 83 files (180 occurrences), not 53. Most are `_inbox/archive` and `_inbox/reports` lint outputs; others are machine data (`_inbox/claims-index.json`, `_signals/architecture-decisions.json`, `_config/drift-watch.md:1`).
  **Fails if (frozen content):** repointing rewrites append-only journals (llm-wiki `sessions/main/2026-09/...`, `2026-11-12`, `231-split-plan.md`) and archived lint reports.
  **Fails if (link forms):** the 128 include `.obsidian/workspace.json:190,214` and directory-form links (`HOME.md:66`, `README.md:44`), and `#anchor` suffixes (`#scoring-an-entry`, `#tier-rubric`) the practice pages may not carry.
  **Evidence to get now:** `grep -c` split into live wiki pages, `_inbox`, `_signals`, `_config`, `.obsidian`, `sessions/`; the distinct anchors among the 128.
  **Kill criterion:** more than a handful of live-page mentions fall outside the plan's list, or anchors cannot be mapped to headings that exist.
  **Cheapest test:** the step 9 listing script run read-only, with anchors and folder classes in its output.
  **Fix class:** plan error for counts, scope and anchors (live pages repointed, archives and journals left as history, machine files listed and decided). Choice for Mark: repoint journals and archives, or leave them as records.

- **Claim:** "The relative link `../../../../../agentic-design/wiki/project/best-practices/framework/<page>.md` ... is not a lint error — pinned by `test_link_gaps.py` staying green."
  **Fails if (pin):** `test_link_gaps.py` tests only `wiki-link-gaps.py` on a synthetic framework doc; it pins nothing about the new link, and step 6's check inspects only the link's prefix.
  **Fails if (location):** `toolset_location()` falls back to `~/.claude/global-toolset` when the registry is missing (`_wiki_config.py:535`); from there the link points outside any notebook root.
  **Fails if (anchors):** anchors are never resolved.
  **Evidence to get now:** the step 6 resolve script over the six links, from the registered toolset root.
  **Kill criterion:** any of the six resolves to a missing file, or the toolset root is not a sibling of `agentic-design`.
  **Cheapest test:** `os.path.normpath` of each link against `C:\github.com\project-notebooks\notebooks\global-toolset\wiki\project\best-practices\framework\`.
  **Fix class:** plan error: the invariant names a test that actually pins the new link. Dead links where the toolset is not a sibling are already accepted (Decision 6).

- **Claim:** Steps 6 and 7 "Trivial stakes: yes — doc text and version numbers only".
  **Fails if:** `wiki-update.py:754` and `:1256-1264` read the frontmatter doc as the tier rubric, and step 7 edits the tier rules and the repository-tier cell, so every ingest reads the change. Versions (9, 3, 3, 16, 19, 2) and the floors at `test_standalone.py:127,132` match the code; the risk is step 7's content.
  **Evidence to get now:** `grep -n "tier" scripts/wiki-update.py`; whether anything greps for "code read beyond the README".
  **Kill criterion:** a script or skill parses the rubric text rather than quoting it.
  **Cheapest test:** the grep above.
  **Fix class:** choice: step 7 stays "Trivial stakes: yes", or "no" (mutation/change-risk scrutiny).

- **Claim:** "Creating `local/` in existing wikis (added by hand)" and "A second Phase B run keeps an edited README".
  **Fails if:** a Phase B re-run over an existing wiki already rewrites `README.md`, `HOME.md`, `_MAP.md` (`new-wiki.py:1064-1070`) and would now also create `local/`, against "existing wikis are left alone"; `10-install-and-setup.md:155-156, 233-234` says write-once applies only to the root files; no test runs Phase B against an existing wiki.
  **Evidence to get now:** `10-install-and-setup.md` lines 150-160, 230-235; whether Phase B ever runs against an existing wiki.
  **Kill criterion:** Phase B is the supported way to refresh an existing wiki.
  **Cheapest test:** a Phase B re-run into a temp wiki with a populated `project/`, then diff the tree.
  **Fix class:** choice: a Phase B run always seeds `local/` when absent, or skips it when the wiki already exists.

### What holds up

- Leaving the README out of `toolset_files()` keeps it from being counted stale or removed: `toolset_status` compares only listed files (`_install_tooling.py:182-198`), the remove scan covers only `how-to/llm-wiki/` top level, `skills/` and `agents/` (`:191-194`), and `--phase docs --check` (`new-wiki.py:790-803`) reads only add, replace and remove, so its exit code is unchanged. Only the dry-run placement is wrong.
- Version numbers and floors match the code today.
- `agentic-design` and `global-toolset` are in one git repo, so `git mv` across notebooks is one commit by path.
- "Practice page: none" for the rerank spec is consistent: no link to it among the 128. The cycle-step-return-format doc has only two hub links (README lines 24 and 52).
- The relative link form resolves on this machine by path arithmetic; precedent at `framework-docs/wiki-authoring-best-practices.md:221`. The toolset is hidden from lint and search (`10-install-and-setup.md:216-217`). The `framework-contract: true` body-check exemption (`_entry_checks.py:229`) is real.
- Step 10's icarus line is correct: the framework `_INDEX.md:24` links a file that does not exist.
- Nothing in the plan copies agentic-design text into llm-wiki or makes a script read it (the `scripts/` grep was not run by the reviewer).
- Skills still find the docs by `{{TOOLSET_DIR}}`.

### Could not assess

- no standing rule found: the local README left out of `toolset_files()` (nearest: the 2026-10-05 global-toolset decision, silent on user files)
- no standing rule found: the rerank spec's "Practice page: none"
- no standing rule found: V2_ROADMAP.md edited only "if the line at 56 still reads as wrong"
- no standing rule found: the architecture-decisions record "stays not shipped and has no local file"
- no standing rule found: existing wikis get no `local/` (Mark's Decision 7 the only source; `10-install-and-setup.md` silent on Phase B re-runs beyond the root-file rule)
- CONSTRAINTS.md does not exist. Repository CLAUDE.md line 172 ("Don't edit the shipped folders ... unless the user explicitly wants to modify the framework") bears on the whole change; Mark has asked for it.
- Not reached: a `local` plain file where a folder should be; the `templates/CLAUDE.md.tmpl` text and whether it needs a mention of `local/`; the moved page's own frontmatter and Backlinks block; `tests/search/question-set/pool.json`, which mentions `architecture-decisions`; whether concurrent sessions writing in agentic-design collide with the step 9 script (the plan never says it re-reads the working tree before each write); the 2026-11-13 decision's supersede convention; steps 3, 4, 5, 8, 10, 11 have no Failures line (information work; not raised); Decision 3's toolset half is not pinned by step 6's check (an addition, not a fix).

VERDICT: KILL-ASSUMPTIONS FOUND
