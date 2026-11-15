# fp-check, round 1: finding standards-5

## Step 0, the claim restated
`tests/skills/wiki-cycle/baseline-opus.json` has the key `"run: read reference.md before writing the scratchpad"` in 9 case entries (lines 450, 487, 526, 573, 627, 677, 721, 762, 836). `baseline-sonnet.json` has it in none. The finding says the two models' entries differ in key set and that this is a defect. Defect class: baseline inconsistency. Trigger: none stated beyond the difference itself. Impact claimed: unspecified. The fix it suggests is to decide whether the rule scores both models, and then either find out why sonnet never records it or drop it from opus.

## Step 1, the path
- Rule (`tests/skills/wiki-cycle/trajectory_rules.py:21-23`): kind `read_before`, `tool: "Write"`, `action: file_path=\S*scratchpad\.md`.
- `tests/skills/_trajectory.py:114-171`, `check()`. The docstring says "One result per rule that applies to this run", and a `read_before` rule "Applies only when an action ran". When no Write call to `scratchpad.md` occurred, `wanted` is empty and `continue` (lines 150-151) emits no result. The key is therefore absent for that run.
- `run_skill_test.py:443-444`, `as_baseline`: `{cid: {c["name"]: c["ok"] for c in r["checks"]}}`. It records exactly the checks the run produced.
- `run_skill_test.py:574-585`, the comparison against the baseline. It counts a regression only as `not ok and base.get(cid, {}).get(n)`, and a gain only as `ok and base.get(cid, {}).get(n) is False`. A key missing on either side is neither. A differing key set changes no result.

## Step 2, the trigger
The key sets do differ, so the observation is true. It comes from whether the rule applied in a given run, which depends on whether the session called the Write tool on the scratchpad. It is not tied to the model:
- `baseline-opus.json` has `"scratchpad written"` in 23 entries and the rule key in only 9. The 14 opus entries without it include the new case `empty-queue-rebuild-runs-before-lint-planted-stale-and-missing-blocks-read-zero`. The other new case in the same commit (`6fc2239`), `empty-queue-clean-notebook-...`, has the key. So the absence follows the run, not the model.
- A correction to the implementer's dispute: sonnet runs do sometimes apply the rule. Saved results `.results/wiki-cycle/20261017-153545/sonnet/parallel-workers-own-folders.json` and `.results/wiki-cycle/20261023-141314/sonnet/full-lint-all-reads-every-entry-older-included.json` each carry the check, `"ok": true`. "Sonnet never writes the scratchpad with the Write tool" is therefore not supported by the saved runs. It does not need to be, as shown below.
- The key was not introduced by this change except in one entry. `git log -S` shows it in opus baselines since `58ff275` and earlier commits. Of the 9 lines, this change (`6fc2239`) added only the one in the `empty-queue-clean-notebook` entry (line 836). The other 8 predate it. The sonnet baseline has never held the key (`git log -S` on `baseline-sonnet.json` is empty).

## Step 3, impact
None. A missing key makes no check fail, hides no regression and creates no false gain, because the comparison reads absent keys as neither. No spec item, done criterion or convention says the baselines must hold identical key sets. `as_baseline` is documented to record the checks a run produced.

## Step 4, sketch and oracle
source: a sonnet run that writes the scratchpad through the shell → `check()`: `actions` empty, `wanted` empty, `continue` → no key in the result → `as_baseline` has no key → the comparison skips it. Effect: none. No existing test expresses the claim, and I ran none. (no oracle)

## Step 5, devil's advocate
1. The key-set difference is visible, but it is not a defect, and the code shows why.
2. Not applicable, as there is no actor.
3. The trigger (a differing key set) occurs. Its harm was never shown. The comparison code at `run_skill_test.py:581-583` shows none.
4. Not applicable.
5. The finding is not pattern-matching on dangerous code. It reads an asymmetry as a defect.
6. I am not dismissing it for being unlikely. The condition occurs and is harmless.
7. I read `_trajectory.py:114-171` and `run_skill_test.py:443-444, 574-585` in this run and cited the lines. The mitigation is the code, not a guess.

## Step 6, gates
| Gate | Result | Evidence |
|---|---|---|
| 1 Process | pass | steps 0-5 above carry cited evidence |
| 2 Reachability | pass | the difference occurs; it is in the baselines |
| 3 Real impact | FAIL | `run_skill_test.py:581-583` ignores keys absent from either side; no regression is hidden and no gain is faked; the baseline records only the checks that applied (`as_baseline`, `_trajectory.py:150-151`) |
| 4 Proof | n/a | no oracle; the sketch shows the key is absent without consequence |
| 5 Bounds | pass | the condition is possible |
| 6 Environment | pass | nothing prevents it; it simply does no harm |

Evidence summary: the key is present exactly when a run called Write on `scratchpad.md`; the opus baseline itself omits it in 14 of 23 entries, one of them a case added in this same change. The sonnet baseline never records it. The implementer's description of how an unapplied rule is recorded is correct. The statement that sonnet never applies the rule is not: two saved sonnet runs applied it and passed. That does not alter the verdict, because nothing in the baseline mechanism depends on the key sets matching.

Checks made: `git log -S` on both baselines; `git show 6fc2239` on `baseline-opus.json`; grep counts of the key and of `"scratchpad written"` in each baseline; grep of the saved `.results/wiki-cycle` runs for the rule's result.

Unverified: why sonnet's saved runs (2 above) that applied the rule did not get it merged into `baseline-sonnet.json`. This was not traced and does not bear on the verdict.

VERDICT: standards-5 FALSE POSITIVE — gate 3 (Real impact) FAIL: the key is recorded only when a run applied the rule (`_trajectory.py:150-151`, `run_skill_test.py:443-444`) and the baseline comparison (`run_skill_test.py:581-583`) treats a key absent on either side as neither regression nor gain, so differing key sets change no result; the opus baseline itself omits the key in 14 of 23 entries, so it varies by run, not by model
