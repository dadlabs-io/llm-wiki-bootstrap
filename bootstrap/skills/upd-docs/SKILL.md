---
name: upd-docs
description: RETIRED — folded into /wrap-up (2026-07-06). The working-memory dashboards (sessions/<persona>/handoff.md + task.md + sessions/active-context.md) are now refreshed by /wrap-up Step 0.5 on every wrap-up. If the user says "upd-docs", "update docs", "save progress", or "save state", run /wrap-up instead.
---

# /upd-docs — RETIRED (use `/wrap-up`)

This skill was **retired on 2026-07-06**. Its entire job — refreshing the mutable working-memory dashboards under `sessions/` — was folded into **`/wrap-up`** so that session-close is a single command and the resume pointer is never left stale.

**What used to be here now lives in `/wrap-up` Step 0.5** (`skills/wrap-up/SKILL.md`), which every wrap-up runs:

- `sessions/<persona>/handoff.md` — resume dump (overwrite)
- `sessions/<persona>/task.md` — NOW / QUEUE (update in place)
- `sessions/active-context.md` — cross-persona dashboard (update your lines)

## If invoked

Do **not** perform a separate working-memory save here. Run **`/wrap-up`** instead — it writes the journal, refreshes these three dashboards (Step 0.5), and (optionally) extracts durable `project/*` entries. If the user only wants the fast dashboard refresh, run `/wrap-up` and answer `none` at the proposal table.

This stub is kept only so existing muscle-memory invocations redirect cleanly. It can be deleted once no one types `/upd-docs`.
