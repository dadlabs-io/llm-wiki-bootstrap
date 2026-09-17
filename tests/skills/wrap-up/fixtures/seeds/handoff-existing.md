HANDOFF — MAIN — {DATE}

GOAL: Wire the retry budget into beacon's upload loop.

WORK COMPLETED (this session): Drafted `RetryBudget` in `beacon/retry.py`. Nothing wired up yet.

CURRENT STATE: Nothing running. The upload loop is untouched.

PENDING: The retry cap is undecided; the duplicate-upload report is unexplained.

KEY FILES:
- `beacon/retry.py` — the draft budget
- `beacon/transport.py` — the network seam

CONTEXT FOR CONTINUATION: The duplicate uploads were only ever seen on a resumed sync.
