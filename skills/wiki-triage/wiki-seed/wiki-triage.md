---
title: "wiki-triage — skill"
type: how-to
artifact: skill
name: wiki-triage
installed_by: install-wiki
date: 2026-09-24
---

# wiki-triage — skill

Decides who reads each research source that arrives in a notebook. Sources you queue, discovery finds, feeds and your Drive folder all land in the notebook's `_inbox/pending/`. Triage gives each one a single owner by moving it into a bucket, `_inbox/intake/<folder>/`, and that bucket's reader ingests it from there. A notebook only one project uses has one bucket, `main`. A notebook several projects draw on has a bucket per reader, and triage is how the shared feed gets sorted once instead of by everyone.

**Trigger:** *"triage"*, *"sort the intake"*, *"sort pending"*, *"route these sources"*, *"who should read these"*; `wiki-cycle` runs it before ingesting.

**Input / Output:** the tickets in `_inbox/pending/` and the buckets in `_inbox/intake/README.md`. Each ticket moves into one bucket folder, with the reason in the notebook's triage log (`_inbox/intake/triage-log.md`). For a source another reader will get, the raw is captured first and named in the ticket, so nobody fetches it twice. You get a table per bucket, and each other project reader gets one tagged line in the project's Discord channel, if there is one.

**The buckets file** is the frontmatter of `_inbox/intake/README.md`, one entry per bucket:

```yaml
buckets:
  - folder: main
    purpose: Anything relevant that fits no other bucket
    reader: llm-wiki
  - folder: agent-builder
    purpose: Building agents, workflows, skills, harnesses
    reader: agent-builder
  - folder: ai-money
    purpose: Making money with AI
    reader: mark
```

`reader` is a project's bot or notebook name from the registry, or you (`mark`), meaning no session ingests that folder unless you ask. Every notebook has a `main` bucket: **the catch-all**. A source that fits no bucket clearly, or two equally, goes there with the reason. A notebook with no buckets file has `main` alone.

**How it decides:** it reads the purposes and the recent rows of the triage log first, and files a new source the way a like one was filed; a call you corrected is followed from then on. It reads each source enough to judge it, the whole raw when the title is not enough. It never drops a source for being off-topic: that goes to `main`, and its reader decides.

**Where a source comes in decides whether it is triaged:** a source you hand to a session directly is not triaged, since your choice is the triage. A source you drop straight into a bucket folder is already triaged, and its reader picks it up. A source in `_inbox/pending/` is triaged.

**When it skips itself:** an empty `pending/` (it says so). A buckets file with a problem (a missing `main`, a reader the registry does not know): it stops and names the problem, since the file is yours. It never ingests, promotes or deletes anything.
