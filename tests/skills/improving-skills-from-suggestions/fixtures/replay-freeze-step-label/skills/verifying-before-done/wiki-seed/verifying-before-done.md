---
title: "verifying-before-done — skill"
type: how-to
artifact: skill
name: verifying-before-done
installed_by: promote-agent
date: 2026-07-31
---

# verifying-before-done — skill

The independent completion check: **never trusts an earlier stage's "done"** — including
sub-agent self-reports. Identifies the proving command, runs it **fresh** (no cached or
remembered results), and records per-layer PASS/FAIL across seven layers: tests pass / the diff
actually contains the fix / review findings actually addressed / frozen tests unmodified / every
"done" criterion pinned by an existing test / the quality bar unmoved / nothing touched outside
the plan's declared scope. A completion claim without this evidence is just a claim.

**Trigger:** *"Verify this is actually done before we commit."*

**Recommended role:** `architect` — deliberately a different role than the one that implemented,
so completion is never self-certified (works standalone too).

**Input:** the diff, the plan's "done" criteria and `## Scope`, any review findings, and — when
the pipeline wrote them — `test-freeze.json` and `scope-baseline.json`.
**Output:** `verification-result.md` — full command output and per-layer verdicts; every layer
must PASS before finishing.

**Bundled scripts** (run, never reasoned about by hand): `check-freeze.py` re-hashes every frozen
test, and its `retire` command records a frozen test you deleted on purpose, with the reason, so the
deletion is not read as a lost test (a retired test that comes back fails the check);
`scope-guard.py` captures a baseline of the tree before implementation starts (`baseline`)
and at verify names every file touched since, failing any outside the plan's scope (`check`).
Each exits 0 / 1 / 2 — pass / hard fail / could not check — and a 2 is reported as `not checked`,
never as a pass. The bar-unmoved layer runs `constraint-driven-development`'s `floor-guard.py`; a test
file you deleted on purpose is recorded with its `approve-deletion` command in the run's
`floor-approvals.json`, and the guard is run with `--approvals` pointing at it.
