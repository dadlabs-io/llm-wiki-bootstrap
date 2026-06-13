#!/usr/bin/env python3
"""Shared wiki path-resolution helpers (v2 — multi-wiki aware).

Single source of truth for resolving WHICH wiki the /wiki-* tooling operates on.
Reads ``<cwd>/.claude/wiki-config.json`` — resolution is PER-PROJECT (cwd-scoped)
by design: you run the tooling from inside the project whose wiki you want to
touch. There is intentionally NO global fallback.

Schema (v2)::

    {
      "vault_root":    "<abs path to the folder that CONTAINS the topic folders>",
      "default_topic": "agentic-design",
      "topics":        ["agentic-design", "cottage-build"],
      "wiki_topic":    "agentic-design"   # v1 alias for default_topic (back-compat)
    }

A topic's root is always ``<vault_root>/<topic>``. To relocate wikis out of a
repo (e.g. when one grows large enough to slow git), point ``vault_root`` at any
absolute folder and move the topic folders there — the names don't change.

Back-compat: v1 configs that only have ``vault_root`` + ``wiki_topic`` keep
working unchanged. ``default_topic()`` falls back to ``wiki_topic``;
``list_topics()`` falls back to ``[default_topic()]``.
"""
import json
from pathlib import Path

DEFAULT_TOPIC_FALLBACK = "llm-wiki"


def load_config(cwd=None):
    """Parsed wiki-config.json dict for the given cwd (default: real cwd), or {}
    if absent/unreadable."""
    base = Path(cwd) if cwd else Path.cwd()
    cfg_path = base / ".claude" / "wiki-config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def default_vault(cwd=None):
    """``vault_root`` from config, else cwd (project root)."""
    cfg = load_config(cwd)
    v = cfg.get("vault_root")
    if v:
        return str(Path(v))
    return str(Path(cwd) if cwd else Path.cwd())


def default_topic(cwd=None):
    """``default_topic``, then the v1 ``wiki_topic`` alias, then ``llm-wiki``."""
    cfg = load_config(cwd)
    return cfg.get("default_topic") or cfg.get("wiki_topic") or DEFAULT_TOPIC_FALLBACK


def list_topics(cwd=None):
    """All declared topics. Accepts a list (canonical) or a dict (keys are the
    topic names); falls back to ``[default_topic()]`` for v1 configs."""
    cfg = load_config(cwd)
    ts = cfg.get("topics")
    if isinstance(ts, list) and ts:
        return [str(t) for t in ts]
    if isinstance(ts, dict) and ts:
        return list(ts.keys())
    return [default_topic(cwd)]


def topic_root(topic=None, cwd=None):
    """Full path to a topic's root: ``<vault_root>/<topic>``."""
    t = topic or default_topic(cwd)
    return str(Path(default_vault(cwd)) / t)
