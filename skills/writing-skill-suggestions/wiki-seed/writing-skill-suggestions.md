---
title: "writing-skill-suggestions — skill"
type: how-to
artifact: skill
name: writing-skill-suggestions
installed_by: install-wiki
date: 2026-09-29
---

# writing-skill-suggestions — skill

## What it does

When one of your installed skills, agents or workflows gets in the way, the lesson usually ends with the session. This
skill writes it down as a **skill suggestion**: one small file in your notebook's `_inbox/skill-suggestions/`, named
after the skill, with four lines:

```
Skill: verifying-before-done
Seen in: committee-names-from-history (2026-09-26)
Issue: check-freeze.py --step takes only an integer, so the fix round's freeze entries were relabelled by hand.
Fix: let --step take a label (e.g. --step fix-1)
```

It uses a bundled script, so the file always has the right name and shape: it refuses a line break inside a field, a
name that is not a skill's, and a suggestion already in the box. Then the work carries on. It never stops to ask.

What happens next is not this skill's job. `/wrap-up` (the llm-wiki framework's; its own page describes the step)
puts each suggestion to you: send it to the skill's owner, keep it, or drop it. A sent one stays in your box marked
`Sent` until the owner collects it; the owner's improver (`improving-skills-from-suggestions`) then moves it into the
owner's notebook, so your box keeps no copy, and its bot tells yours what became of it. The whole path, from this
note to the owner's decision, is on the [skill-suggestions page](../skill-suggestions.md).

## When it fires

- A skill, agent, workflow or one of their scripts forced a workaround, missed something, or had a rule that did not
  fit the case.
- You corrected how a skill made the work go.
- You ask: *"Note that for whoever maintains the review skill."* / *"Log this as a skill suggestion."*

The do-code-change workflow uses it in every run.

## Recommended role

None: any session can use it.

## Inputs and outputs

- **In:** the skill's name, where it happened, the issue, and the fix if there is one.
- **Out:** one file in `_inbox/skill-suggestions/`. With no wiki set up for the project, nothing is written and the
  four lines are handed back to you.

## When it skips itself

A lesson about your own code or data (a parser that crashes on an empty file) is not a skill suggestion; it belongs in
your project's wiki.
