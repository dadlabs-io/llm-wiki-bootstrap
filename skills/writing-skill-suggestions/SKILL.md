---
name: writing-skill-suggestions
description: "Writes a skill suggestion, one four-line note (the skill under the exact name the user or its folder gives, never a similar-sounding one; where it was seen; the issue; the fix) dropped into the project notebook's _inbox/skill-suggestions/ box, whenever a skill, agent, workflow or one of their scripts got in the way: it forced a workaround, a check it ran missed something, one of its rules did not fit the case, or the user corrected how it made the work go. Use in any session at that moment, and when asked to note, log or pass on a problem with a skill for whoever maintains it. Not for lessons about the project's own code or data (those belong in the project's wiki), not for fixing the skill itself, and not for going through suggestions already sent (improving-skills-from-suggestions)."
last_reviewed: 2026-09-27
review_after: 2026-12-27
reviewed_for_model: claude-opus-5-5
---

# Writing skill suggestions

## What this does
A lesson about a skill otherwise ends with the session that learned it. This skill writes it down as a **skill
suggestion**: one small file in the project notebook's box, `_inbox/skill-suggestions/<skill>--<slug>.md`, four
labelled lines (`Skill`, `Seen in`, `Issue`, `Fix`). `/wrap-up` later puts each one to the user, who sends it to the
skill's owner, keeps it or drops it. A sent one waits in the box, marked `Sent`, until the owner's `receive` moves it
into the owner's notebook, where the owner's improver turns it into proposed changes.

## When to use
- A skill, agent, workflow or one of their scripts forced a workaround (a flag it would not take, a step done by hand).
- A check it ran missed something a later step or the user caught.
- One of its rules did not fit the case, and the work went around it.
- The user corrected how the skill made the work go ("you asked me questions a plan should have answered").
- The user asks to note, log or pass on a problem with a skill for its owner.

Not for a lesson about the project's own code or data (a parser that crashes on an empty file is the project's, and
goes in its wiki), for fixing the skill yourself, or for going through suggestions already sent here
(`improving-skills-from-suggestions`).

## How it works
1. **Name what got in the way.** It must be a skill, agent or workflow, its name copied from where it is written: the
   user's words, the skill's folder, or its frontmatter `name`. Never paraphrase it, and never swap in a
   similar-sounding skill you can see (`code-review` is not `reviewing-code`): the owner finds the suggestion by that
   name. For a script, name the skill it belongs to (`check-freeze.py` is `verifying-before-done`'s). A lesson about
   the project itself stops here: it goes in the project's wiki. Done when you have one name, copied, not composed.
2. **Write it** with this skill's script, from the project's root:
   `uv run --project {{WIKI_SCRIPTS_DIR}} python <this skill's folder>/scripts/skill-suggestion.py add --skill <name> --seen-in "<run, task or session>"
   --issue "<what happened>" --fix "<the fix>"`.
   - **Issue** — what happened and where you saw it, in one line: the surprise, with the file or step.
   - **Fix** — the fix that worked, or the one you would suggest; leave `--fix` out when there is none (`none yet`).
     Record the fix, never a count of failures.
   Done when the script has answered.
3. **Read its exit code.** 0: written; say so in one line with the path. 1: the box already holds the same skill and
   issue; say so and write nothing else. 3: no wiki was found; give the user the four lines it printed (in a
   do-code-change run they go in the run's `checkpoints.md` under `## Skill suggestions`). 2: the call was wrong (a
   name that is not an artifact name, a line break in a field); fix the call. Done when one of the four is handled.
4. **Carry on with the task.** The suggestion waits in the box; `/wrap-up` puts it to the user. A suggestion is never a
   question in the middle of the work.

## Examples
The situation: running the tests, `check-freeze.py freeze --step fix-1` was refused because `--step` takes only a
number, so the entries were frozen at 4 and relabelled by hand.

```
uv run --project {{WIKI_SCRIPTS_DIR}} python .claude/skills/writing-skill-suggestions/scripts/skill-suggestion.py add --skill verifying-before-done \
  --seen-in "committee-names-from-history" \
  --issue "check-freeze.py --step takes only an integer, so the fix round's freeze entries were relabelled by hand." \
  --fix "let --step take a label (e.g. --step fix-1)"
```

The file it writes, `_inbox/skill-suggestions/verifying-before-done--check-freeze-py-step-takes-only.md`:

```
Skill: verifying-before-done
Seen in: committee-names-from-history (2026-09-26)
Issue: check-freeze.py --step takes only an integer, so the fix round's freeze entries were relabelled by hand.
Fix: let --step take a label (e.g. --step fix-1)
```

## Enforcement
Every hard rule above, once, with what makes a violation fail rather than merely discouraged:
- "Each field is one line; the skill is an artifact name; the same suggestion is never written twice" → `script` —
  `skill-suggestion.py` refuses a line break (exit 2), a name that is not lowercase-hyphen (exit 2), and a duplicate
  skill and issue already in the box (exit 1).
- "The box's existing files and its `archive/` are never edited" → `script` — the script only creates new files at the
  box's top level (an exclusive create, `-2` on a name clash).
- "A lesson about the project's own code or data is not a skill suggestion" → `prose` — a judgment about what got in
  the way; the eval case `should-not-trigger-project-lesson` replays it.
- "Never a question in the middle of the work; carry on" → `prose` — a judgment of timing; the eval cases check the run
  goes on without asking.
- "Record the fix, never a count of failures" → `prose` — wording; the contract's Gotchas rule (§8).

## Gotchas
No gotchas logged yet.

## Composition
- **Invocation class:** model-invoked, at the moment a skill gets in the way; do-code-change's orchestrating session
  names it in its rule, so it does not carry `disable-model-invocation`.
- **Readers:** `/wrap-up` Step 5.5 (llm-wiki) puts each suggestion to the user, finds its owner from the skill's
  usage page, and marks a sent one with a `Sent (<date>, Mark): <owner>` line, left in the box; the owner's `receive`
  (`improving-skills-from-suggestions`, run in the owning library) moves it out, and its improver proposes changes. All
  three read the four labelled lines and the `<skill>--<slug>.md` name and ship together in llm-wiki's pack, so a
  change to either is made in all three at once.
- **Script:** `scripts/skill-suggestion.py` — `add`, `--self-test` with a floor of 34. The notebook is resolved from
  `.claude/wiki-config.json` (`llm_wiki_root`, else `notebook` + `registry`, else `llm-wiki/`); `--wiki` overrides.
- **Lifecycle:** encoded preference (Mark's loop, 2026-09-26/27); revisit when the box or its four lines change.
