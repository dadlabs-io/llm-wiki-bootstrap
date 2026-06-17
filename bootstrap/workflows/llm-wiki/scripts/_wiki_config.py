#!/usr/bin/env python3
"""Shared wiki path-resolution helpers (v3 — registry-aware).

Single source of truth for resolving WHICH wiki the /wiki-* tooling operates on.
Reads ``<cwd>/.claude/wiki-config.json`` — resolution is PER-PROJECT (cwd-scoped):
you run the tooling from inside the project whose wiki you want to touch.

THREE config shapes are supported (newest first), all back-compatible:

v3 — registry pointer (thin config; locations live in ONE shared registry)::

    {
      "notebook": "agent-builder-bootstrap",
      "registry": "C:/github.com/project-notebooks/linked-notebooks.json"
    }

  The registry (``linked-notebooks.json``) is the single source of truth for WHERE
  every notebook lives — so a notebook's location is recorded in exactly one place
  and cross-notebook links resolve through it::

    { "notebooks": {
        "agent-builder-bootstrap": { "vault_root": "notebooks/agent-builder-bootstrap", "topic": "llm-wiki" },
        "agentic-design":          { "vault_root": "C:/.../vault/wikis", "topic": "agentic-design" }
    } }

  Each entry is ``{vault_root, topic}`` (topic_root = vault_root/topic). vault_root
  may be relative (resolved against the registry file's folder) or absolute. A bare
  string entry is also accepted and treated as the flat topic_root.

v2 — explicit multi-wiki: ``vault_root`` + ``topics[]`` + ``default_topic``.
v1 — explicit single: ``vault_root`` + ``wiki_topic``.

Resolution order in every helper: registry (if ``notebook`` + ``registry`` present)
→ explicit ``vault_root`` → cwd. So existing v1/v2 configs keep working unchanged.
"""
import json
from datetime import datetime
from pathlib import Path

DEFAULT_TOPIC_FALLBACK = "llm-wiki"


# ---------- Canonical date/time standard (single source) ----------
# THE RULE for all llm-wiki tooling:
#   * DATE LABELS (calendar day a human reads/organizes by — cycle ids, report
#     folders, `date:`/`last_reviewed:`/`review_after:` frontmatter): use LOCAL
#     date via today_label(). A cycle run at 8pm local files under the local day,
#     never tomorrow's UTC day.
#   * TIMESTAMPS (a precise instant for audit/ordering — `created`, `*_at`, run
#     stamps): use now_stamp() — LOCAL time WITH an explicit UTC offset (tz-aware,
#     ISO-8601). Never a naive timestamp; the zone is always labelled.
# Do NOT use datetime.now(timezone.utc) for human date labels (off-by-one at night)
# and never emit a naive .isoformat() (ambiguous zone). New code: import these.

def today_label() -> str:
    """Local calendar date, e.g. '2026-06-17'. For human-facing date labels."""
    return datetime.now().strftime("%Y-%m-%d")


def now_stamp(timespec: str = "seconds") -> str:
    """Local timestamp WITH explicit offset, e.g. '2026-06-17T00:05:07-04:00'.
    tz-aware (never naive) so the zone is always labelled. For audit/event fields."""
    return datetime.now().astimezone().isoformat(timespec=timespec)

# Canonical wiki folder taxonomy — the SINGLE source of truth for the structure a
# new wiki gets. Both scaffolders (new-wiki.py phase B, wiki-init.py) import this
# so they can't drift apart. (Fix P5/P7 — there were two divergent taxonomies.)
#   research/  — semantic memory (external): what we ingested
#   project/   — semantic memory (internal): what we built
#   sessions/  — episodic memory (per-persona logs, created on demand)
MERGED_TAXONOMY = [
    "research/active", "research/long-term", "research/tooling",
    "research/best-practices", "research/implementation", "research/skills",
    "research/orchestration", "research/interesting-docs",
    "project/components", "project/decisions", "project/architecture",
    "project/patterns", "project/troubleshooting", "project/best-practices",
    "sessions",
]


def load_config(cwd=None):
    """Parsed wiki-config.json dict for the given cwd (default: real cwd), or {}."""
    base = Path(cwd) if cwd else Path.cwd()
    cfg_path = base / ".claude" / "wiki-config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


# ---------- registry (linked-notebooks.json) ----------

def load_registry(cwd=None, cfg=None):
    """Return (notebooks_dict, registry_path) from the cfg's ``registry`` pointer,
    or (None, registry_path|None) if absent/unreadable."""
    cfg = cfg if cfg is not None else load_config(cwd)
    reg_path = cfg.get("registry")
    if not reg_path:
        return None, None
    rp = Path(reg_path)
    if not rp.is_absolute():
        base = Path(cwd) if cwd else Path.cwd()
        rp = base / reg_path
    if rp.exists():
        try:
            data = json.loads(rp.read_text(encoding="utf-8"))
            return (data.get("notebooks", data), rp)
        except (json.JSONDecodeError, OSError):
            pass
    return None, rp


def _abs_against(base_file, p):
    """Resolve p against base_file's folder if relative; else return p as-is."""
    pp = Path(p)
    return pp if pp.is_absolute() else (Path(base_file).parent / pp)


def _registry_resolve(name, cwd=None, cfg=None):
    """Look up ``name`` in the registry → (vault_root_abs:str, topic:str) or None."""
    cfg = cfg if cfg is not None else load_config(cwd)
    reg, reg_path = load_registry(cwd, cfg)
    if not reg or name not in reg:
        return None
    entry = reg[name]
    if isinstance(entry, str):
        root = _abs_against(reg_path, entry)
        return (str(root.parent), root.name)
    if isinstance(entry, dict) and entry.get("vault_root"):
        return (str(_abs_against(reg_path, entry["vault_root"])), entry.get("topic") or name)
    return None


# ---------- resolution helpers (registry → vault_root → cwd) ----------

def default_vault(cwd=None):
    """The cwd notebook's vault_root: registry → explicit vault_root → cwd."""
    cfg = load_config(cwd)
    nb = cfg.get("notebook")
    if nb and cfg.get("registry"):
        r = _registry_resolve(nb, cwd, cfg)
        if r:
            return r[0]
    v = cfg.get("vault_root")
    if v:
        return str(Path(v))
    return str(Path(cwd) if cwd else Path.cwd())


def default_topic(cwd=None):
    """The cwd notebook's topic: registry → default_topic/wiki_topic → 'llm-wiki'."""
    cfg = load_config(cwd)
    nb = cfg.get("notebook")
    if nb and cfg.get("registry"):
        r = _registry_resolve(nb, cwd, cfg)
        if r:
            return r[1]
    return cfg.get("default_topic") or cfg.get("wiki_topic") or DEFAULT_TOPIC_FALLBACK


def notebook_root(name, cwd=None):
    """Absolute topic_root for a notebook NAME via the registry (cross-notebook
    links). Returns None if the name isn't in the registry."""
    r = _registry_resolve(name, cwd)
    if r:
        return str(Path(r[0]) / r[1])
    return None


def topic_root(topic=None, cwd=None):
    """Full path to a topic's root. If ``topic`` is a registry key (a notebook
    name), resolve it through the registry (cross-notebook). Otherwise it's
    ``<default_vault>/<topic-or-default>``."""
    if topic:
        r = _registry_resolve(topic, cwd)
        if r:
            return str(Path(r[0]) / r[1])
    t = topic or default_topic(cwd)
    return str(Path(default_vault(cwd)) / t)


def list_topics(cwd=None):
    """All known notebooks/topics: registry keys → explicit topics[] →
    [default_topic()]."""
    cfg = load_config(cwd)
    reg, _ = load_registry(cwd, cfg)
    if reg:
        return list(reg.keys())
    ts = cfg.get("topics")
    if isinstance(ts, list) and ts:
        return [str(t) for t in ts]
    if isinstance(ts, dict) and ts:
        return list(ts.keys())
    return [default_topic(cwd)]
