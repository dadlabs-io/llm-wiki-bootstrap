# Drive setup — one-time OAuth for Google Drive ingest

If you opted into Drive ingest at `/new-wiki` time, the installer attempted to walk you through OAuth. If it succeeded, you don't need this doc. If something failed, here's how to fix it.

## Prerequisites

You need a Google Cloud project with:
1. **Drive API enabled** — https://console.cloud.google.com/apis/library/drive.googleapis.com
2. **OAuth 2.0 Desktop Client** — https://console.cloud.google.com/apis/credentials

Create the project, enable the API, create an OAuth Client ID (type: **Desktop application**), download the JSON.

## Place the client secrets

Save the downloaded JSON as:
```
~/.config/wiki-cycle/client_secrets.json
```
(Windows: `C:\Users\<you>\.config\wiki-cycle\client_secrets.json`)

This file is your Drive auth credential. It's not committed anywhere — local-machine only.

## Run the OAuth flow

```bash
python <project>/.claude/wiki-scripts/wiki-fetch-drive-folder.py --auth-only
```

A browser window opens. Sign in. Approve the "See, edit, create, and delete all of your Google Drive files" scope. The token caches at `~/.config/wiki-cycle/drive-token.json`. Subsequent runs are silent.

## Scope check

The cycle uses **full Drive scope** (not `drive.readonly`) because `--move-handled` is default-on and moving files needs write access. If the cached token has only `drive.readonly`, the next cycle will re-auth automatically.

## Drive folder structure

The cycle expects:
```
<Your Drive>/
└── __FOR CLAUDE/                ← parent (default; override at install time)
    └── <project-slug>/          ← per-project subfolder (matches your project slug)
```

Drop files into `<project-slug>/`. Each file's contents should be a title line + a `https://share.google/...` short URL (typical iOS/Android Share-to-Drive output).

The cycle resolves short URLs, dedupes, strips Discover tracking, and queues unique URLs into `llm-wiki/wiki/_inbox/pending/`. Processed files move into `__FOR CLAUDE/<project-slug>/_completed/<cycle-id>/`.

## What if I share the same Drive across multiple projects?

That works — each project has its own subfolder. The OAuth token is machine-global, so you only sign in once. Per-project `wiki-config.json` records which subfolder this project pulls from (defaults to project slug).

## Troubleshooting

- **"folder not found"** — the subfolder doesn't exist yet (or got renamed). Create it in Drive. The cycle logs and continues; no need to fix immediately.
- **Re-auth loop** — usually a wrong-scope token cached. Delete `~/.config/wiki-cycle/drive-token.json` and re-run `--auth-only`.
- **Browser doesn't open** — usually a Docker / WSL environment without browser access. Run the OAuth from a graphical desktop session once, then the token works headless.
