---
title: "Evicting stale agent memories"
date: 2026-10-08
tier: 1
category: pattern
tags: [agent-memory, eviction]
---

# Evicting stale agent memories

## TL;DR
Evict a memory only after it has gone unread for ninety days and no newer memory cites it.

## What
A pattern for keeping an agent's long-term store small: age and citation, never size alone, decide what is dropped.
