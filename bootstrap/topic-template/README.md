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

Full user guide: [`how-to/llm-wiki/user-guide.md`](./how-to/llm-wiki/user-guide.md) (framework-managed; it arrives with the framework's docs refresh).

## Layout

```
<topic>/
├── README.md                  This file
├── _config/feeds.md           Trusted sources for discovery
├── _inbox/                    Live state (pending/proposed/done/discovered/reports)
├── how-to/llm-wiki/           Framework-managed usage docs, the user guide among them
├── raw/                       Verbatim source dumps (append-only)
└── wiki/
    ├── HOME.md               Landing page
    ├── best-practices/
    │   └── framework/         Shipped contracts (don't edit)
    └── <your folders>/        Your content; folder taxonomy is your call
```
