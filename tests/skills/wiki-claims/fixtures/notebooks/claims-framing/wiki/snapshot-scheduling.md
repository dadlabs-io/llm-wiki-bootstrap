---
title: "Snapshot scheduling"
date: 2026-08-14
source_url: "https://example.com/snapshot-scheduling"
tier: 2
confidence: high
tags: [snapshots, backup, operations]
---

# Snapshot scheduling

## TL;DR
Snapshots are taken every 6 hours and kept for 14 days.

## Schedule
A snapshot job runs at 00:00, 06:00, 12:00 and 18:00 UTC. Snapshots older than 14 days are deleted by the nightly cleanup.

## Storage
Each snapshot of the 50 GB data set takes about 18 GB after compression.
