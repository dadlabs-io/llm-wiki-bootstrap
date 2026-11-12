# Review findings — 241-pre-commit-dcc-check, round 2 (focused)

Scope: the five files fix round 1 moved, plus the sibling sites of standards-1 (every shipped statement of when `--no-verify` may be used). Files round 1 reviewed that the fix left alone are out of this round. Prescan: clean. Read-only guard: PASS.

## Standards

No findings. standards-1 checked fixed at every shipped site (Grep `no-verify`, `Mark has said|only when Mark|machine's owner|owner has agreed`, `commit anyway|on purpose|false alarm` outside `.do-code-change/`).

Unverified:
- `CHANGELOG.md` names Mark in its dated history ("Mark: fail loud"; who said yes): a record of who decided, not a bypass rule; left for the owner.

| Rule | Verdict | Search |
|---|---|---|
| R3 | clear | the three Greps above |
| S1 / N1 | clear | renamed test read in context |
| C2 | clear | hook header and echo updated together |
| R15 | clear | exact `==` kept; only the expected string changed |
| R13 | clear | asserts the hook's published last stderr line |
| S2 / G5 | clear | pinned copies of one wording, not logic |

Well built: the wording changed in every shipped place and in the test that pins it, in one commit.

## Spec

- [nit] `.do-code-change/241-pre-commit-dcc-check/requirements.md:29` — the note says "the shipped hook names no person", but the hook's header (`tools/git-hooks/pre-commit:3`), README (`:3`, `:10`) and `install.sh:5` still name Mark outside the bypass rule; the ruling covered the bypass rule only. Fix: narrow the note to "the bypass rule names no person".
- [suggestion] `.do-code-change/241-pre-commit-dcc-check/plan.md:13` — the Solution still says "`--no-verify` only on Mark's word", against plan.md:24's ruled line. Fix: amend the Solution sentence in place.

Unverified:
- The renamed test's freeze entry and its red witness were not read by the lens.

| Claim | Verdict | Search |
|---|---|---|
| standards-1 in every bypass site | met | Grep `no-verify|only when|machine's owner` |
| spec-1 install.md matches hook | met | Grep in install.md |
| spec-3 plan step 3 wording | met | Grep in plan.md; test lines 113-122 |
| Decision 1 rationale | found (nit) | Grep `Mark` in tools/git-hooks |
| plan Solution | found (suggestion) | Grep `Mark|no-verify` in plan.md |

Well built: one phrase in the closing line, the header, README, install.md, CHANGELOG and the test.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `tools/git-hooks/pre-commit` | MEDIUM | 1 | in part (changed lines) | in full | — |
| `tests/scripts/test_git_hooks_dcc.py` | LOW | 1 | in part (changed lines) | in part | — |
| `tools/git-hooks/README.md` | LOW | 1 | in part (changed line) | in full | — |
| `wiki-seed/install.md` | LOW | 1 | in part (changed line) | in part | — |
| `CHANGELOG.md` | LOW | 1 | in part (changed line) | in part | — |

No high-risk file; the change-risk lens was not run.

Standards: 0 findings. Spec: 2 findings (both in the run's own notes). Change risk: not run.

VERDICT: Standards CLEAR · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
