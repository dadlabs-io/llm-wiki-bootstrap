---
title: "LoomDB failover results"
date: 2026-09-01
source_url: "https://example.com/loomdb-failover-results"
tier: 2
confidence: high
tags: [loomdb, durability, recovery]
---

# LoomDB failover results

## TL;DR
LoomDB recovers quickly after a crash: about 2 seconds to replay its write-ahead log on the 50 GB test set.

## Test
We killed the LoomDB process 20 times during writes on a 50 GB data set and timed the restart.

## Results
Recovery took about 2 seconds to replay the write-ahead log. No acknowledged write was lost in any of the 20 runs.
