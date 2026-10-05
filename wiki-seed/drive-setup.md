---
title: "Drive and Gmail setup — llm-wiki"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-10-03
---

# Drive and Gmail setup — one-time OAuth for Google Drive and Gmail ingest

Gmail is set up after Drive, with the same Google app; see [Gmail](#gmail) at the end.

If you opted into Drive ingest at `/new-wiki` time, the installer attempted to walk you through OAuth. If it succeeded, you don't need this doc. If something failed, here's how to fix it.

## Prerequisites

You need a Google Cloud project with:
1. **Drive API enabled** — https://console.cloud.google.com/apis/library/drive.googleapis.com
2. **OAuth 2.0 Desktop Client** — https://console.cloud.google.com/apis/credentials

Create the project, enable the API, create an OAuth Client ID (type: **Desktop application**), download the JSON.

The Google client libraries come with the wiki scripts' own uv environment: nothing to install on the machine.

## Place the client secrets

Save the downloaded JSON as:
```
~/.config/wiki-cycle/client_secrets.json
```
(Windows: `C:\Users\<you>\.config\wiki-cycle\client_secrets.json`)

This file is your Drive auth credential. It's not committed anywhere — local-machine only.

## Run the OAuth flow

```bash
uv run --project ~/.claude/wiki-scripts python ~/.claude/wiki-scripts/wiki-fetch-drive-folder.py --auth-only
```

(A bundled install has the script at `<project>/.claude/wiki-scripts/` instead.) The script reads the client secrets from the path above; `--client-secrets <path>` or the `WIKI_DRIVE_CLIENT_SECRETS` environment variable point it elsewhere.

A browser window opens. Sign in. Approve the "See, edit, create, and delete all of your Google Drive files" scope. The token caches at `~/.config/wiki-cycle/drive-token.json`. Subsequent runs are silent. `--auth-only` then looks your folders up and prints `auth_ok` with `folder_found` (and, with `--subfolder <name>`, `subfolder_found`), so a missing API or folder shows here rather than in the first cycle. A later sign-in reuses the Google app recorded in the token if `client_secrets.json` is gone.

## Scope check

The cycle uses **full Drive scope** (not `drive.readonly`) because `--move-handled` is default-on and moving files needs write access. If the cached token has only `drive.readonly`, the next cycle will re-auth automatically. A look-only scan (`--no-move-handled`) uses a full-scope token as it is.

## Drive folder structure

The cycle expects:
```
<Your Drive>/
└── __FOR CLAUDE/                ← parent (default; override at install time)
    └── <project-slug>/          ← per-project subfolder (defaults to the notebook name)
```

Drop files into `<project-slug>/`. A link capture just needs to contain the link; Share-to-Drive files from a phone (a title plus a `https://share.google/...` short link) work as they are. A file can also be the source itself: a PDF, a Word, PowerPoint or Excel file, an EPUB, an Outlook message, a Google Slides or Sheets deck, or an image (a screenshot) is saved into the wiki's `raw/` and queued. Anything else, and a note with no link in it, is listed in the cycle's report and left where it is.

The cycle resolves short links, strips tracking parameters, skips URLs already in the wiki, and queues the rest into `_inbox/pending/` at the wiki root (beside `wiki/`). Processed files move into `__FOR CLAUDE/<project-slug>/_completed/<cycle-id>/`.

## What if I share the same Drive across multiple projects?

That works — each project has its own subfolder. The OAuth token is machine-global, so you only sign in once. The project's `.claude/wiki-config.json` records the parent folder and subfolder (`drive.parent_folder`, `drive.subfolder`), and `/wiki-cycle` scans those; unset, they default to `__FOR CLAUDE` and the notebook name.

## Troubleshooting

- **"the Google Drive API is not enabled …"** — enable it in the project the message names (the link is in the message), wait a few minutes, retry. Any refused Drive call exits 3 with one line.
- **"folder not found"** — the folder or subfolder doesn't exist yet (or got renamed); the script never creates it. Create it in Drive. The cycle logs and continues; no need to fix immediately.
- **Re-auth loop** — usually a wrong-scope token cached. Delete `~/.config/wiki-cycle/drive-token.json` and re-run `--auth-only`.
- **Browser doesn't open** — usually a Docker / WSL environment without browser access. Run the OAuth from a graphical desktop session once, then the token works headless.

## Gmail

`/wiki-cycle` can also read a Gmail label of newsletters and saved emails: every article link becomes a candidate the session recommends or skips and you approve, and handled emails move to a done label. It uses the Gmail API with the same Google app as Drive.

1. **Enable the Gmail API** in the same Google Cloud project: https://console.cloud.google.com/apis/library/gmail.googleapis.com
2. **Create the two labels** in Gmail: one you file emails under, and a done label (defaults `...wiki-inbox` and `...wiki-inbox/read`).
3. **Turn it on** in the project's `.claude/wiki-config.json`, beside the `drive` block:
   ```json
   "email": { "enabled": true, "label": "...wiki-inbox", "done_label": "...wiki-inbox/read" }
   ```
4. **Sign in once:**
   ```bash
   uv run --project ~/.claude/wiki-scripts python ~/.claude/wiki-scripts/wiki-fetch-gmail.py auth
   ```
   A browser window opens; approve reading your email and managing its labels (the `gmail.modify` scope: the script reads the label and moves handled emails to the done label; it never sends or deletes). The token caches at `~/.config/wiki-cycle/gmail-token.json`. The script finds the OAuth client the way the Drive script does (`--client-secrets`, `WIKI_GMAIL_CLIENT_SECRETS`, `client_secrets.json` above) or, failing those, reuses the client recorded in the Drive token. It then makes one call to Gmail and prints `auth_ok` with `label_found` and `done_label_found`, so a missing step 1 or 2 shows here rather than in the first cycle.

Troubleshooting: **"no Gmail label named …"** (or `label_found: false`) means a label name in the config does not match Gmail exactly (nested labels are written `parent/child`). **"the Gmail API is not enabled …"** means step 1 is not done for the project the client belongs to; after enabling it, Google can take a few minutes to let calls through. A sign-in that fails, or a Gmail call that is refused, exits 3 with one line; the cycle reports it and carries on without email.
