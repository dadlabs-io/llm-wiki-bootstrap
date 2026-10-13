---
title: "Chunk size decision for notes"
date: 2026-10-05
tier: 3
status: proposed
category: decision
tags: [chunking, notes]
---

# Chunk size decision for notes

## TL;DR
Split notes at heading boundaries, capped at six hundred tokens, rather than at a fixed window.

## What
The decision to chunk each entry along its headings, with a size cap, so a retrieved chunk is always a complete thought.
