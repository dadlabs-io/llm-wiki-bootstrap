"""writing-skill-suggestions suite: agent-builder's eval cases, run by the shared jsonl checker (tests/skills/_jsonl_cases.py)."""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _jsonl_cases import (ALLOWED_TOOLS, DISALLOWED_TOOLS, check, make_setup, prepare_fixtures,  # noqa: E402,F401
                          prompt, snapshot, teardown)

setup = make_setup("writing-skill-suggestions", HERE)
