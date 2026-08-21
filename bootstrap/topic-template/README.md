# <topic> wiki

A curated knowledge base on <topic>. Built on [llm-wiki](https://github.com/...).

## Scope

(Fill in — what's in-scope for this wiki, what's out-of-scope. Keep it specific; overly-broad scope leads to topic bleed.)

## Status

Active. Started <YYYY-MM-DD>.

## First steps

After install:

1. Edit `_config/feeds.md` — add the trusted sources you want discovery to sweep.
2. Run `/wiki-update <url>` with 3-5 seed entries on your topic.
3. When you have ~10 entries, run `/wiki-cycle` for the first full pass.
4. Read the cycle report at `_inbox/reports/<date>/`; your wiki now auto-maintains structure.

Full user guide: [`wiki/llm-wiki-user-guide.md`](./wiki/llm-wiki-user-guide.md).

## Layout

```
<topic>/
├── README.md                  This file
├── _config/feeds.md           Trusted sources for discovery
├── _inbox/                    Live state (pending/proposed/done/discovered/reports)
├── raw/                       Verbatim source dumps (append-only)
└── wiki/
    ├── HOME.md               Landing page
    ├── llm-wiki-user-guide.md Canonical how-to-use reference
    ├── best-practices/
    │   └── framework/         Shipped contracts (don't edit)
    └── <your folders>/        Your content; folder taxonomy is your call
```
