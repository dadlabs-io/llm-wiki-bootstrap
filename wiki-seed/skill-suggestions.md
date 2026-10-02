---
title: "Skill suggestions — llm-wiki"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-09-29
---

# Skill suggestions

When one of your installed skills, agents or workflows gets in the way, the lesson usually ends with the session
that learned it. Skill suggestions keep it: a session writes the lesson down as a small note where it happened, you decide
at wrap-up whether it goes to the library that owns the skill, and the owner turns the notes it receives into
proposed changes for you to accept or turn down. Every note ends up in one place, the owner's notebook, with your
decision on it and a wiki page that says what became of it.

Two skills, shipped with llm-wiki beside `/wrap-up` (moved from agent-builder's library, 2026-09-30). Any session can write a note; the improver runs in the session of
the library that maintains the skills.

## The skills

| Skill | One line |
|---|---|
| [`writing-skill-suggestions`](./skills/writing-skill-suggestions.md) | Writes the note: four lines (`Skill`, `Seen in`, `Issue`, `Fix`) in your notebook's `_inbox/skill-suggestions/`, then the work carries on |
| [`improving-skills-from-suggestions`](./skills/improving-skills-from-suggestions.md) | The owner's side: collects a note sent to it, checks it against the run and the skill as it stands, proposes changes, records your decision, archives the note and indexes it in the wiki |

The step between them, where each note is put to you, is part of `/wrap-up`: [wrap-up](./skills/wrap-up.md).

## How a note travels

1. **Written, where it happened.** A skill forced a workaround, missed something, or had a rule that did not fit.
   The session writes one file, `_inbox/skill-suggestions/<skill>--<slug>.md`, and carries on without asking you
   anything:

   ```
   Skill: verifying-before-done
   Seen in: committee-names-from-history (2026-09-26)
   Issue: check-freeze.py --step takes only an integer, so the fix round's freeze entries were relabelled by hand.
   Fix: let --step take a label (e.g. --step fix-1)
   ```

2. **Put to you at wrap-up.** `/wrap-up` finds the skill's owner and asks you: send, keep, or drop. See
   [wrap-up](./skills/wrap-up.md) for that step. A note you send stays in your box, marked `Sent`, and
   the owner's bot is tagged with its path; wrap-up does not ask you about it again. In the owner's own notebook
   there is no one to send to, so a note about one of its own skills is filed straight into `received/` and the
   report says so.
3. **Collected by the owner.** The owner's session moves the note into its own notebook
   (`_inbox/skill-suggestions/received/`), marked `From: <your project>`. Your box keeps no copy. A note already
   there from the same run is not taken twice (your duplicate is removed); the same problem seen in another run is
   kept as its own note, because a repeat is evidence.
4. **Proposed.** When you ask the owner for a pass, the improver checks each note against the run's record and the
   skill as it stands today. It sets aside what the skill already covers, what belongs to another library, what you
   turned down before, and what the record does not bear out, each with its reason, and writes one proposal per
   lesson: the file and place to change, the exact change, the evidence quoted from the record, tactical or
   strategic. It never edits a skill.
5. **Decided, archived and indexed.** You accept a proposal (it becomes a task, made with the skill's tests run
   before and after), turn it down, or leave it for later. Each decided note moves to
   `raw/skill-suggestions/<date>-<project>/` in the owner's notebook with your decision as its last line, beside
   the proposals you were shown. One wiki page per pass, in `wiki/project/skill-suggestions/`, lists every note,
   your decision and the task it became, and links each archived file, so a wiki search finds what projects have
   told the library.
6. **You are told.** The owner's bot tags your project's bot with what became of each note and where the page is.

## Typical session

1. During a change, a script refuses a flag the plan needed and the session works around it. It writes a note
   and goes on.
2. At `/wrap-up` you are asked about the note and answer "send".
3. Later, in the library's session: *"Go through the skill suggestions we've received."* You get the proposals,
   answer each one, and the accepted ones become tasks.

## When not to use it

- A lesson about your own project's code or data (a parser that crashes on an empty file) belongs in your
  project's wiki, not in a note to a skill's owner.
- A change you want made to a skill now ("add this to its Gotchas") is an ordinary edit in the library, not a note.

## Limits

- A project with no wiki has no box: the four lines are handed back to you instead of being written.
- The owner is found from where the skill's usage page sits in your notebook; a skill with no page there means
  wrap-up asks you who owns it.
- Nothing is proposed until someone asks for a pass: a sent note waits in the owner's notebook until then.
