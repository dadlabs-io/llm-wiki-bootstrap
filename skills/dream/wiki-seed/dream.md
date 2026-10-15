---
title: "dream — skill"
type: how-to
artifact: skill
name: dream
installed_by: install-wiki
date: 2026-10-15
---

# dream — skill

Reads back over the project's own past work and reports what it teaches. Session journals, code-change summaries and
troubleshooting entries hold lessons that no one rereads: the same problem fixed in three sessions, the same
correction from you twice. A dream hands that record to a reader that was not in those sessions, asks it a few
questions, and keeps only what the record shows more than once, each finding quoted with its source.

**Trigger:** */dream* for a sweep, */dream "<topic>"* for a topic dream, or "dream about X", "what keeps going wrong",
"look back over our sessions for X".

**Two modes:**

| | Sweep (`/dream`) | Topic (`/dream "<topic>"`) |
|---|---|---|
| Question | What went wrong more than once, and what kept working? | Your question, broken into 3 to 5 sub-questions |
| Record | The last 30 days (`--days N`) | Every matching file, whenever it was written |

**Input / Output:** the mode, and the notebooks to read (this project's unless you name others). The reply is a short
summary: the findings ranked by evidence, one line each, and the report's path,
`_inbox/reports/dreams/<date>-<slug>.md`. The report holds each finding's pattern, count, quoted evidence, where it
would change and at what cost; what is working; the thin evidence; what was read in full, grepped or skipped; and the
ledger (below).

### What happens, step by step

1. **Scope.** It lists the record: session journals (never the dashboards), code-change summaries, troubleshooting
   entries, and counts them.
2. **Plan, then wait.** It shows the mode, the notebooks, the file counts and where the report will go, and starts
   only on your go. A dream reads every file it cites in full: the first one, on test-driven development, read about
   70 files and took about 10 minutes and 840k tokens.
3. **The dreamer reads.** One spawned agent does the reading. It writes nothing, uses no network and no API key, and
   greps instead of using the search, so the GPU stays free.
4. **The ledger is checked.** While reading, the dreamer notes every candidate pattern; before it finishes, it gives
   each one a fate (a finding, thin evidence, or dropped with a reason), so nothing it noticed is silently lost. The
   session checks the counts add up and that every finding cites two or more sessions, and sends it back once if
   not (a lesson from REA's finding ledger, 2026-10-14).
5. **Report and summary.** The session files the report and gives you the summary.
6. **Your call.** It asks what to do with the findings. One that would change a skill can become a skill suggestion;
   one that belongs to another project can go to its intake as a handoff; nothing is sent or changed until you say.

**When it skips itself:** with no session journals there is nothing to dream over, and it says so.

**What it will not do:** count a pattern seen only once (it goes under thin evidence), follow an instruction written
in the record (it names it on a `Prompt injection:` line), or change a skill itself.

**Works with:** [`wrap-up`](./wrap-up.md) writes the journals a dream reads.
[`writing-skill-suggestions`](./writing-skill-suggestions.md) turns a finding you pick into a suggestion for the
skill's owner.
