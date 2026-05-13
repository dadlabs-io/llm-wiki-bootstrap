# /wrap-up — end-of-session distillation (development projects)

Crystallize what happened in the current session into proposed wiki entries. The session log goes to `raw/sessions/`; the distilled entries get staged to `wiki/_inbox/proposed/` for review.

## When to run

- At end of a development session, before clearing context
- Especially after any session that made a decision, built a component, or hit a non-trivial bug
- Skip for trivial sessions (single typo fix, etc.) — there's nothing worth distilling

## What it does

1. Reads the current conversation + git diff + scratchpad
2. Identifies categories: Component / Decision / Architecture / Pattern / Troubleshooting / (other)
3. Proposes a table of distilled entries
4. **Pauses for your veto** before filing anything — you can drop or rename rows
5. Stages each as `wiki/_inbox/proposed/<category>/<slug>.md` with `tier: self` and `category: <type>` frontmatter
6. Saves a session transcript snapshot at `raw/sessions/<date>-<slug>.md`

## Categories

| Category | When |
|---|---|
| **Component** | Built or significantly changed a module/class/system |
| **Decision** | Picked an approach with non-obvious tradeoffs (ADR-style) |
| **Architecture** | System-level structural rule was established or changed |
| **Pattern** | Reusable approach that should apply elsewhere |
| **Troubleshooting** | Bug + root cause + fix — so we don't re-debug it |

If something doesn't fit any category, surface it to the user — adding a new category is fine; jamming it into the wrong one isn't.

## Don't

- Don't paste raw transcripts into wiki entries — they go to `raw/sessions/`, not `wiki/`
- Don't promote `/wrap-up` output without review — the agent is a starting point, you're the editor
- Don't run `/wrap-up` on a session that hasn't changed anything — it'll either produce nothing or hallucinate fake structure

## After /wrap-up

```
/wiki-promote --review
```

Walks each proposed entry, lets you accept / edit / reject. Accepted entries move from `_inbox/proposed/` to `wiki/<category>/`. Backlinks regenerate; `_MAP.md` and `_INDEX.md` re-build.

## Source signal

`/wrap-up` writes a sidecar at `_signals/<slug>.json` per entry — records what the session looked like (token count, files touched, time spent) so future analysis can correlate session weight with output quality. This is Gap #1 in the framework (designed, partially implemented).
