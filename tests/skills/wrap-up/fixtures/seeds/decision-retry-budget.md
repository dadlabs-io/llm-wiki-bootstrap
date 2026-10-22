---
title: Retry budget replaces the attempt cap
category: decision
date: 2026-09-15
tier: self
---

# Retry budget replaces the attempt cap

We stopped capping retries by attempt count. A file is now retried until the total time since its first attempt passes a 120 second budget, whatever the number of attempts. The reason: five attempts at growing delays could keep one file alive for eleven minutes on a slow endpoint, and the attempt count said nothing about how long a user had been waiting.

The backoff between attempts and the 30 second per-request timeout are unchanged.

This changes what the retry policy page says: it no longer stops at 5 attempts per file. See [[30-retry-policy]] and [Retry policy](../architecture/30-retry-policy.md).
