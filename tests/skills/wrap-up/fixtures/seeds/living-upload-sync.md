---
title: Upload sync
category: architecture
kind: living
describes: beacon/manifest.py
last_reviewed: 2026-08-01
tier: self
---

# Upload sync

How beacon keeps track of which files are already uploaded, so an interrupted sync can resume.

## How it works

The manifest entry for a file is written when its upload starts, before any bytes are sent. A sync that is interrupted mid-transfer resumes from the manifest and skips every file that already has an entry. The manifest is one JSON file per bucket.

## Rules and settings

- Chunk size is 8 MiB.
- Every remote call goes through the single `send()` seam in `beacon/transport.py`.

## Known gaps and bugs

- Duplicate uploads are reported by users after an interrupted sync.

## History

- 2026-08-01: first written from the sync design discussion.
