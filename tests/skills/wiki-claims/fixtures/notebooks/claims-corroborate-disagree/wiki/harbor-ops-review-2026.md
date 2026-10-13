---
title: "Harbor in production: an ops review"
date: 2026-09-02
source_url: "https://ravi.example.io/posts/harbor-in-production"
tier: 2
confidence: medium
tags: [harbor, cache, operations]
---

# Harbor in production: an ops review

## TL;DR
Ravi Okonkwo reviews a year of running Harbor. Cached entries expire after 15 idle minutes, the default, and he left it alone on all four clusters.

## Operations
Across four clusters he saw the same behaviour: a cached entry that is not read for 15 minutes is evicted. His main complaint is slow warm-up after a restart.
