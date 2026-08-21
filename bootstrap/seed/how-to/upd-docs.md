# `/upd-docs` — RETIRED (use `/wrap-up`)

`/upd-docs` was **retired on 2026-07-06**. Refreshing the working-memory dashboards is now part of **`/wrap-up`** (Step 0.5), which runs on every wrap-up:

- `wiki/sessions/<persona>/handoff.md` — resume-here / survival dump (mutable, overwrite)
- `wiki/sessions/<persona>/task.md` — NOW + QUEUE (mutable, update in place)
- `wiki/sessions/active-context.md` — cross-persona dashboard (update only your lines)

**Just run `/wrap-up`.** It writes the session journal, refreshes those three dashboards, and (optionally) extracts durable `project/*` entries. If you only want the fast dashboard refresh without crystallizing knowledge, run `/wrap-up` and answer `none` at the proposal table — the journal + dashboards still update, nothing gets staged.

See [`wrap-up.md`](./wrap-up.md) for the full flow.
