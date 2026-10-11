---
id: 2
title: Switch the retry loop to the elapsed-time budget
owner: main
list: current
status: doing
next: use RetryBudget.exhausted() in the retry loop in beacon/transport.py
priority: high
tags: [beacon, retry]
created: 2026-10-06
updated: 2026-10-09
links: []
---

Replace the attempt-count limit in the upload retry loop with the `RetryBudget` allowance from `beacon/retry.py`.

**Steps**
- [x] Draft `RetryBudget` in `beacon/retry.py`
- [ ] Use it in the retry loop
- [ ] Exercise it against the injected fake sender

**Log**
- 2026-10-06: Drafted RetryBudget as an elapsed-time allowance in beacon/retry.py.
