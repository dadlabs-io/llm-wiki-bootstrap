---
title: "improving-skills-from-suggestions — skill"
type: how-to
artifact: skill
name: improving-skills-from-suggestions
installed_by: install-wiki
date: 2026-09-29
---

# improving-skills-from-suggestions — skill

## What it does

When one of your installed skills, agents or workflows gets in the way, the session leaves a **skill
suggestion**: four lines naming the skill, where it happened, the issue, and the fix that worked. At `/wrap-up` you
decide where each suggestion goes (the llm-wiki framework's page for wrap-up describes that step); one you send to
the library that owns the skill waits in your box, marked `Sent`, until that library collects it. This skill is the
library's side: it collects what you sent and turns it into **proposals** for you:

- it checks each suggestion against the run's record and against the skill as it stands today;
- it sets aside what the skill already covers, what belongs to another library, what you turned down before, and what
  the record does not bear out, each with its reason;
- it writes one proposal per lesson: the file and place to change, the exact change, the evidence quoted from the
  record, and whether it is a tactical patch or a strategic fix.

It never edits a skill. You accept a proposal (it becomes a task, made with the skill's tests run before and after),
turn it down, or leave it for later, and your answer is recorded on each suggestion.

## Trigger phrases

- *"Run the improver."*
- *"Go through the skill suggestions we've received."* / *"What have the suggestions taught us?"*
- When a suggestion is sent to this library, it is filed for the next pass: *"File this skill suggestion: <path>."*

## Recommended role

None: it runs in the library's own session (the factory that builds and maintains the skills).

## Inputs and outputs

- **In:** the suggestion files received in the library's notebook (`_inbox/skill-suggestions/received/`), the runs'
  records, and the library's skills, agents and workflows.
- **Out:** a proposals file (`raw/skill-suggestions/<date>-<project>/proposals.md`); after your answers, a task for
  each proposal you accept, each suggestion moved into that same folder with your decision on it, and one wiki page
  for the pass (`wiki/project/skill-suggestions/`) listing every suggestion, your decision and the task it became, so
  a wiki search finds what projects have told the library. A suggestion lives in one place: when you send it, the
  library moves it out of your box into its own notebook (marked `From: <your project>`), and after the pass its bot
  tells yours what became of each suggestion and where the page is. A suggestion it already holds from the same run
  is not taken twice (your duplicate is removed from the box); the same problem seen in another run is kept as its
  own suggestion, because a repeat is evidence the proposal counts.

## Composition

Uses the task-list skill for accepted proposals. Its input comes from the writing-skill-suggestions skill, which any
session (every do-code-change run among them) uses to write a suggestion, and from wrap-up, which sends them on your
word. The whole path is on the [skill-suggestions page](../skill-suggestions.md).

## When it skips itself

With nothing received, it says so and writes nothing. A request to change a skill directly ("add this line to the
Gotchas") is an ordinary edit, not an improver pass.
