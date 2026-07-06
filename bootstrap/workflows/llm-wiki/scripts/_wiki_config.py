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
import re
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


# ---------- sessions/ classification (working + episodic memory) ----------
# sessions/ holds NON-CURATED memory and is exempt from the curated pipeline the
# same way _inbox/ is — lint/map/index/reciprocate skip it (and /wiki-refresh),
# while qmd still indexes it so it stays searchable. Two tiers, by folder depth:
#   * persona-root dashboards — sessions/<persona>/{task,handoff,BACKLOG}.md,
#     sessions/<persona>/reading-list.json, sessions/active-context.md — MUTABLE
#     working memory, overwrite-in-place, written by /wrap-up (Step 0.5).
#   * dated journals — sessions/<persona>/<YYYY-MM>/*.md — append-only episodic
#     memory, written by /wrap-up (Step 0). (The old /upd-docs skill that owned the
#     dashboards was folded into /wrap-up on 2026-07-06.)
# Persona folders are created ON DEMAND by the running persona (no fixed list).
_SESSION_MONTH_RE = re.compile(r"\d{4}-\d{2}")


def in_sessions(path) -> bool:
    """True if ``path`` is anywhere under a ``sessions/`` folder."""
    return "sessions" in Path(path).parts


def is_session_journal(path) -> bool:
    """True for a dated episodic journal (``sessions/<persona>/<YYYY-MM>/*.md``)."""
    p = Path(path)
    return "sessions" in p.parts and any(_SESSION_MONTH_RE.fullmatch(part) for part in p.parts)


def is_session_dashboard(path) -> bool:
    """True for a persona-root mutable working-memory file — anything under
    ``sessions/`` that is NOT a dated journal (task/handoff/BACKLOG/reading-list/
    active-context)."""
    return in_sessions(path) and not is_session_journal(path)


def _find_config_path(cwd=None):
    """Walk up from cwd to the filesystem root; return the first existing
    ``.claude/wiki-config.json`` Path, or None. Makes resolution robust to being
    run from a NESTED cwd (e.g. from inside a notebook folder that has no config
    of its own but sits under a project/hub that does). Fixes B11 — without this,
    a nested cwd found no registry and ``topic_root`` fell back to ``cwd/topic``,
    silently DOUBLING the path (e.g. ``notebooks/agentic-design/agentic-design``)."""
    base = Path(cwd) if cwd else Path.cwd()
    for d in [base, *base.parents]:
        p = d / ".claude" / "wiki-config.json"
        if p.exists():
            return p
    return None


def load_config(cwd=None):
    """Parsed wiki-config.json dict for the given cwd (default: real cwd), or {}.
    Walks up parent dirs to find the NEAREST ``.claude/wiki-config.json`` (B11)."""
    cfg_path = _find_config_path(cwd)
    if cfg_path:
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
        # Resolve a relative registry path against the config FILE's project root
        # (the dir above .claude/), not the cwd — so a nested cwd still resolves it.
        cfg_path = _find_config_path(cwd)
        base = cfg_path.parent.parent if cfg_path else (Path(cwd) if cwd else Path.cwd())
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
    if isinstance(entry, dict):
        # Object entry. Two accepted shapes (both may also carry per-notebook
        # options like wrap_up_auto_promote, which are ignored here):
        #   {"root": "notebooks/<name>"}      → flat topic_root (preferred)
        #   {"vault_root": "...", "topic": ".."}  → split form (back-compat)
        if entry.get("root"):
            root = _abs_against(reg_path, entry["root"])
            return (str(root.parent), root.name)
        if entry.get("vault_root"):
            return (str(_abs_against(reg_path, entry["vault_root"])), entry.get("topic") or name)
    return None


def notebook_option(name, key, default=None, cwd=None, cfg=None):
    """Read a per-notebook option (e.g. 'wrap_up_auto_promote') from the registry
    entry for ``name``. Returns ``default`` if the entry is a flat string, the key
    is absent, or the registry can't be read. The registry is the single home for
    per-notebook settings so they travel with the notebook, not the calling project."""
    cfg = cfg if cfg is not None else load_config(cwd)
    reg, _ = load_registry(cwd, cfg)
    if not reg or name not in reg:
        return default
    entry = reg[name]
    if isinstance(entry, dict):
        return entry.get(key, default)
    return default


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


def wiki_dir(topic=None, vault=None, cwd=None):
    """Absolute path to a topic's ``wiki/`` folder.

    Registry-aware: resolves the topic root via ``topic_root()`` (which honors
    the linked-notebooks registry, including notebooks whose root has an extra
    path segment like ``.../<name>/llm-wiki``). Pass an explicit ``vault`` to
    force the legacy ``<vault>/<topic>/wiki`` join (override / non-registry use).
    """
    if vault:
        return str(Path(vault) / (topic or default_topic(cwd)) / "wiki")
    return str(Path(topic_root(topic, cwd)) / "wiki")


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
