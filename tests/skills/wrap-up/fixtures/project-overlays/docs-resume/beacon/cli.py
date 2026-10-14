"""beacon's command line: `beacon sync <folder>`."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="beacon")
    sub = parser.add_subparsers(dest="command", required=True)
    sync = sub.add_parser("sync", help="upload a folder to the object store")
    sync.add_argument("folder")
    sync.add_argument(
        "--no-resume",
        dest="resume",
        action="store_false",
        default=True,
        help="start every upload from scratch instead of continuing an interrupted one",
    )
    return parser
