---
title: "Drive setup — llm-wiki"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-09-08
---

# Drive setup — one-time OAuth for Google Drive ingest

If you opted into Drive ingest at `/new-wiki` time, the installer attempted to walk you through OAuth. If it succeeded, you don't need this doc. If something failed, here's how to fix it.

## Prerequisites

You need a Google Cloud project with:
1. **Drive API enabled** — https://console.cloud.google.com/apis/library/drive.googleapis.com
2. **OAuth 2.0 Desktop Client** — https://console.cloud.google.com/apis/credentials

Create the project, enable the API, create an OAuth Client ID (type: **Desktop application**), download the JSON.

On this machine you also need the Google client libraries: `pip install google-api-python-client google-auth-oauthlib`.

## Place the client secrets

Save the downloaded JSON as:
```
~/.config/wiki-cycle/client_secrets.json
```
(Windows: `C:\Users\<you>\.config\wiki-cycle\client_secrets.json`)

This file is your Drive auth credential. It's not committed anywhere — local-machine only.

## Run the OAuth flow

```bash
python ~/.claude/wiki-scripts/wiki-fetch-drive-folder.py --auth-only
```

(A bundled install has the script at `<project>/.claude/wiki-scripts/` instead.) The script reads the client secrets from the path above; `--client-secrets <path>` or the `WIKI_DRIVE_CLIENT_SECRETS` environment variable point it elsewhere.

A browser window opens. Sign in. Approve the "See, edit, create, and delete all of your Google Drive files" scope. The token caches at `~/.config/wiki-cycle/drive-token.json`. Subsequent runs are silent.

## Scope check

The cycle uses **full Drive scope** (not `drive.readonly`) because `--move-handled` is default-on and moving files needs write access. If the cached token has only `drive.readonly`, the next cycle will re-auth automatically.

## Drive folder structure

The cycle expects:
```
<Your Drive>/
└── __FOR CLAUDE/                ← parent (default; override at install time)
    └── <project-slug>/          ← per-project subfolder (defaults to the notebook name)
```

Drop files into `<project-slug>/`. Each file just needs to contain the link; Share-to-Drive files from a phone (a title plus a `https://share.google/...` short link) work as they are.

The cycle resolves short links, strips tracking parameters, skips URLs already in the wiki, and queues the rest into `_inbox/pending/` at the wiki root (beside `wiki/`). Processed files move into `__FOR CLAUDE/<project-slug>/_completed/<cycle-id>/`.

## What if I share the same Drive across multiple projects?

That works — each project has its own subfolder. The OAuth token is machine-global, so you only sign in once. The project's `.claude/wiki-config.json` records the parent folder and subfolder (`drive.parent_folder`, `drive.subfolder`), and `/wiki-cycle` scans those; unset, they default to `__FOR CLAUDE` and the notebook name.

## Troubleshooting

- **"folder not found"** — the folder or subfolder doesn't exist yet (or got renamed); the script never creates it. Create it in Drive. The cycle logs and continues; no need to fix immediately.
- **Re-auth loop** — usually a wrong-scope token cached. Delete `~/.config/wiki-cycle/drive-token.json` and re-run `--auth-only`.
- **Browser doesn't open** — usually a Docker / WSL environment without browser access. Run the OAuth from a graphical desktop session once, then the token works headless.
