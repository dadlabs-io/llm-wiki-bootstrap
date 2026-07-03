# How to save working memory — `/upd-docs`

`/upd-docs` is the quick save for **live working memory**. It writes the running persona's dashboards into the wiki's `sessions/` layer:

- `wiki/sessions/<persona>/task.md` — NOW + QUEUE (mutable, overwrite)
- `wiki/sessions/<persona>/handoff.md` — resume-here / survival dump (mutable, overwrite)
- `wiki/sessions/active-context.md` — cross-persona dashboard (update only your lines)

Run it at the end of a session, when saving progress, or when context is getting long. Under 2 minutes — a save, not an audit.

## `/upd-docs` vs `/wrap-up`

| | `/upd-docs` | `/wrap-up` |
|---|---|---|
| Tier | working memory (mutable) | episodic journal (append) + durable `project/*` |
| Writes | `sessions/<persona>/{task,handoff}.md`, `active-context.md` | `sessions/<persona>/<YYYY-MM>/<date>-<sid>.md`, `project/*` |
| When | "save my live state / resume point" | "document what we built this session" |

The **completed record** lives in the `/wrap-up` journals (each carries `session_id`/`date`/`persona` and is qmd-searchable) — there is no `completed.md`.

## Notes

- Your persona folder is created **on demand** (`mkdir -p sessions/<persona>`). A new persona just works — no list to register.
- Everything under `sessions/` is **exempt from the curated pipeline** (lint/map/index/reciprocate/refresh skip it, like `_inbox/`); qmd still indexes it.
