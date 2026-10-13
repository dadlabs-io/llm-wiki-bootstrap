---
title: "Harbor cache walkthrough"
date: 2026-08-30
source_url: "https://dev.example.org/dwhitcombe/harbor-cache-walkthrough"
tier: 2
confidence: medium
tags: [harbor, cache, walkthrough]
---

# Harbor cache walkthrough

## TL;DR
Dana Whitcombe walks through Harbor's cache. By default an entry expires after 15 minutes without being read, and the default maximum size is 2 GB.

## Expiry
In her test setup Dana measured entries disappearing 15 minutes after their last read, which matches Harbor's default idle expiry. Raising the setting is a one-line change.
