#!/usr/bin/env python3
"""wiki-upgrade.py — refresh the GLOBAL llm-wiki tooling from the master source.

Re-installs every wiki skill (~/.claude/skills/<skill>/) and script
(~/.claude/wiki-scripts/) from the bootstrap source, substituting the
{{WIKI_SCRIPTS_DIR}} placeholder. Idempotent — run it after pulling new tooling.

This is the dedicated upgrade command. It shares its implementation with
new-wiki.py via _install_tooling.install_tooling() — the manifests and copy/
install loop live in ONE place. (new-wiki.py scaffolds projects; upgrading the
global tooling is a separate concern and now a separate command.)

Usage:
  python wiki-upgrade.py                          # upgrade from auto-detected master
  python wiki-upgrade.py --bootstrap-source <path># explicit master location
  python wiki-upgrade.py --dry-run                # show what would change
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _install_tooling import (  # noqa: E402
    install_tooling, derive_bootstrap_source, print_summary,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Upgrade the global llm-wiki tooling (skills + scripts) from the master source.")
    ap.add_argument("--bootstrap-source", default=None,
                    help="Path to the llm-wiki-bootstrap / workflows-core checkout. "
                         "Default: auto-detect (wiki-config.json bootstrap_source, then walk up).")
    ap.add_argument("--tool", default="claude-code", choices=["claude-code", "cursor"],
                    help="Install target (default: claude-code).")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without writing.")
    args = ap.parse_args()

    if args.tool == "cursor":
        print("ERROR: standalone cursor upgrade not supported yet — "
              "use `new-wiki.py --mode tooling --tool cursor` for now.", file=sys.stderr)
        return 1

    bootstrap = derive_bootstrap_source(args.bootstrap_source)
    if not bootstrap:
        print("ERROR: could not find the bootstrap source. Pass --bootstrap-source <path>.",
              file=sys.stderr)
        return 1

    print(f"[wiki-upgrade] bootstrap source: {bootstrap}")
    print(f"[wiki-upgrade] tool: claude-code  (dry-run: {args.dry_run})")
    print()
    try:
        summary = install_tooling(bootstrap, dry_run=args.dry_run)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print_summary(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
