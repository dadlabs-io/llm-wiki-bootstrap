---
title: Retry policy
category: architecture
kind: living
last_reviewed: 2026-08-01
tier: self
---

# Retry policy

How beacon decides when to stop retrying a failed upload.

## How it works

A failed upload is retried with exponential backoff, capped at 5 attempts per file. When the fifth attempt fails the file is reported as failed and the sync moves on.

## Rules and settings

- Per-request timeout is 30 seconds.
- Backoff starts at 1 second and doubles after each attempt.

## Known gaps and bugs

- None recorded.

## History

- 2026-08-01: first written from the retry design discussion.
