---
name: wiki-triage
description: "Sorts a notebook's untriaged research sources (the queue tickets in _inbox/pending/ from Drive, discovery, feeds or queued URLs) into its intake buckets, one owner per item, by the purposes written in _inbox/intake/README.md: reads the buckets and the past calls, reads each item enough to judge it, captures the raw for items another reader will ingest, moves each ticket into _inbox/intake/<folder>/ with a one-line reason, logs every call, and tells each other reader once. Use when the user says triage, sort the intake, sort pending, route these sources, who should read these, or when /wiki-cycle reaches its triage step. Not for ingesting (wiki-update, wiki-cycle), not for a source the user hands over directly (their choice is the triage), and never for project/ entries."
last_reviewed: 2026-09-24
review_after: 2026-12-24
reviewed_for_model: claude-opus-5-5
---

# /wiki-triage

Gives each untriaged research source in a notebook one owner. A source waits in `_inbox/pending/`; triage moves its ticket into `_inbox/intake/<folder>/`, and that bucket's reader ingests it from there. A notebook with one reader has one bucket, `main`; a notebook several projects draw on (agentic-design) has one per reader. It is the same job either way.

The buckets are the frontmatter of `_inbox/intake/README.md` (`folder`, `purpose`, `reader`); `reader: mark` means the user reviews that folder himself. **`main` is the catch-all.** Every move goes through the script, which refuses a folder that is not a bucket and logs each call:

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-triage.py --topic <notebook> buckets     # the buckets, readers, and who "this session" is
python {{WIKI_SCRIPTS_DIR}}/wiki-triage.py --topic <notebook> check       # config problems (exit 1)
python {{WIKI_SCRIPTS_DIR}}/wiki-triage.py --topic <notebook> log --last 30   # past calls: the precedents
python {{WIKI_SCRIPTS_DIR}}/wiki-triage.py --topic <notebook> pending     # what waits to be sorted
python {{WIKI_SCRIPTS_DIR}}/wiki-triage.py --topic <notebook> route <ticket> --to <folder> --reason "<one line>" [--raw raw/<file>]
```

`<notebook>` is the notebook the sources are for: this project's own by default, or the one the user names (agentic-design for the shared research feed).

## Steps

1. **Read the rules.** Run `buckets` and `check`; if `check` reports a problem, stop and tell the user, since the config is theirs to fix. Read `_inbox/intake/README.md` in full (the purposes and any rules under them), then `log --last 30`. The past calls are the precedents: file a new item the way a like one was filed, and a row the user corrected wins over yours.
2. **List the queue** with `pending`. If it is empty, say so and stop. Items already in an `intake/<folder>/` were put there by the user and are triaged; leave them. **With one bucket** (no README, or `main` alone), there is nothing to judge: route every ticket to `main` with the reason "the only bucket", read nothing, and go to step 6.
3. **Judge each item, one at a time.** Read its ticket (the source URL and title). If that does not settle which bucket it belongs to, capture its raw (`python {{WIKI_SCRIPTS_DIR}}/wiki-update.py --topic <notebook> --source <url> --fetch-only`, which prints `raw_path=`) and read it in full. Pick the one bucket whose purpose fits it best: one owner per item, and the others read the promoted entry. If it fits none clearly, or two equally, it goes to **`main`**, with the reason saying which ones it straddles. Triage never drops an item for being off-topic: it goes to `main` with that reason, and its reader decides.
4. **Capture the raw for every item another reader will get** (a folder whose reader is not this session, including the user's), so they never re-fetch: `--fetch-only` as above, then pass `--raw raw/<file>` to `route`. A login-gated page is captured through the user's browser session by the Browser-session capture flow in `wiki-update`'s `fetchers.md`; with no browser, route it without a raw and put "needs browser capture" in the reason. An item for this session's own folder needs no raw now; its ingest fetches it.
5. **Route it:** `route <ticket> --to <folder> --reason "<one line: what it is, why this bucket>"`.
6. **Report and tell the readers.** Show the user one table per folder (item, reason) and the count left in `pending`. Then tell each other project reader that got items, **once per pass**, in the project's Discord channel if the session has one: one line tagged with the reader's raw `<@id>` from `buckets`, naming the folder and the count. A folder the user reads goes in the report to them. A reader with no Discord is named in the report instead.

## Don't

- Don't ingest, promote or delete anything: triage only moves tickets and captures raws. A ticket is never deleted; a wrong call is fixed by routing it again, which is logged.
- Don't edit `_inbox/intake/README.md` unless the user asks. A new bucket or a changed purpose is their decision.
- Don't triage a source the user handed over directly or dropped into a bucket, and never a `project/` entry.
- Don't guess between two buckets: that is what `main` is for.
