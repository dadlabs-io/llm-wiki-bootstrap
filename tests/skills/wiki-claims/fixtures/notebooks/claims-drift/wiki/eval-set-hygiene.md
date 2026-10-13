---
title: "Evaluation set hygiene"
date: 2026-08-02
source_url: "https://example.com/eval-set-hygiene"
tier: 2
confidence: high
tags: [evaluation, datasets, hygiene]
---

# Evaluation set hygiene

## TL;DR
Duplicate questions inflate evaluation scores, so deduplicate before you measure anything.

## What we found
Our pool held 437 questions. We removed 37 duplicates and kept 400.

## Practice
Hash each normalised question and drop repeats. Re-run the hash check whenever the pool grows.
