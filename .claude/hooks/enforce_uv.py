#!/usr/bin/env python3
"""enforce_uv.py — a PreToolUse hook that refuses a bare Python command in a uv project and names the uv form.

Each Bash call Claude Code makes is a fresh shell, so an activated virtual environment never persists and a
bare `pip`, `python`, `pytest` or `ruff` resolves to whatever interpreter the shell finds first — usually not
the project's `.venv`. That is the most reported failure of agents on Python projects (installing into system
Python and reporting success, running tests against the wrong interpreter). This hook turns the rule "every
project command runs through uv" from advice into a refusal the model cannot walk past.

It has the four properties a refusing hook needs (skills/common/scripts/write-guard.py is the model):
  * the denial names the escape — the exact `uv run …` / `uv add …` form, which the re-issued call passes;
  * it decides only the one input it can parse — the Bash command string — and only when the working
    directory holds a `pyproject.toml` and `uv` is on PATH (anywhere else it exits 0 at once);
  * it fails OPEN on its own errors and writes one line to `.artifacts/enforce-uv.log` saying why it skipped,
    so a broken guard never blocks a legitimate call and never fails silently;
  * it is bounded and stateless — a `.artifacts/enforce-uv.off` file lifts it for the session (each lifted
    call is logged), and nothing it does can strand the run.

Protocol: Claude Code passes the call as JSON on stdin ({"tool_name": "Bash", "tool_input": {"command": ...},
"cwd": ...}); exit 2 refuses the call and the stderr text reaches the model; exit 0 lets it through.
`--self-test` proves every decision below on fixtures in a temp directory (floor 76).

Segments: the command splits on &&, ||, ;, | and newline only where the shell would, so quoted text, a heredoc body
and a comment are data, never a command (task 137); text inside $( ) or backticks is not examined, as before. Input
it cannot read for certain (an unbalanced quote, a heredoc with no closing line, an arithmetic <<) splits on every
separator instead, which can only over-refuse. Leading VAR=value assignments are stripped from each segment.

Decision, per command segment:
  refuse  pip / pip3 / python -m pip                      -> uv add <pkg> | uv remove <pkg> | uv pip <args>
  refuse  pytest ruff pyright mypy ty coverage mutmut cosmic-ray bandit pre-commit   -> uv run <same>
  refuse  python -m <module>, python -c, python <path under src/ tests/ or the package>, python (REPL), python -
                                                          -> uv run python <same>
  refuse  python $VAR / %VAR% …  (a path the hook cannot see) -> uv run python <same>, or the path written literally
  refuse  python -m venv / virtualenv / venv               -> uv sync (uv creates .venv itself)
  refuse  source …/activate, . …/activate, …\\activate     -> uv run <the command you meant>
  allow   uv …, uvx …, python …/scripts/<x>.py (tool scripts that shell out to uv themselves),
          python <x>.py resolving outside the project root after ~ expansion (a global tool, e.g. ~/.claude/wiki-scripts/),
          python --version / -V, .venv/Scripts/python.exe …, .venv/bin/python …, anything else
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path, PurePosixPath
from typing import NamedTuple, TypedDict

PROJECT_TOOLS = {"pytest", "ruff", "pyright", "mypy", "ty", "coverage", "mutmut", "cosmic-ray", "bandit", "pre-commit"}
PYTHONS = {"python", "python3", "py", "pythonw"}
PIPS = {"pip", "pip3"}
SEGMENT_SPLIT = re.compile(r"\s*(?:&&|\|\||;|\||\r?\n)\s*")
SEPARATORS = ("&&", "||", ";", "|")
HEREDOC = re.compile(r"<<(-?)[ \t]*([^\s;&|<>()]+)")
HEREDOC_TAG = re.compile(r"'([A-Za-z_]\w*)'|\"([A-Za-z_]\w*)\"|([A-Za-z_]\w*)")  # a word, wholly quoted or plain
OPERATOR_CHARS = (";", "&", "|", "(", ")", "<", ">")
BLANKS = (" ", "\t", "\n")
UNSURE_IN_BRACES = set("'\"`#\n{$\\")  # ${...} is read through only when it holds none of these
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
LIFT_FILE = ".artifacts/enforce-uv.off"
LOG_FILE = ".artifacts/enforce-uv.log"
SELF_TEST_MINIMUM = 76


class Verdict(NamedTuple):
    """A decision: `allow`, and `text` beside it — the uv escape for a refused segment, the reason for a whole call."""
    allow: bool
    text: str


class HookPayload(TypedDict, total=False):
    """The fields of Claude Code's PreToolUse JSON that this hook reads."""
    tool_name: str
    tool_input: dict[str, str]
    cwd: str


def _segments(command: str) -> list[str]:
    """The command's segments, split where the shell splits commands and nowhere else (task 137).

    Quoted text, a heredoc body and a comment are data, never a command: a notes heredoc whose line began
    "coverage" was refused when every newline split. Input the segmenter cannot read for certain (an unbalanced
    quote, a heredoc with no closing line) falls back to SEGMENT_SPLIT, which splits everywhere: a surprise there
    can only over-refuse. Like the plain split before it, this does not look inside `$(…)` or backticks.
    """
    read = _read_segments(command)
    return SEGMENT_SPLIT.split(command) if read is None else read


def _read_segments(command: str) -> list[str] | None:
    """Split on && || ; | and newlines at the top level only; drop heredoc bodies and comments; None when unsure.

    `frames` holds what is open, innermost last: a quote (' "), a substitution `$(` with any `(` nested in it, or
    backticks. Separators split only when nothing is open, so a substitution's text stays in the segment that holds
    it (not examined, as before) and its quotes and heredocs never desynchronise the top level: the commit form
    `git commit -m "$(cat <<'EOF' ... EOF)"` is one segment.

    A misreading that still ends balanced is silent, so the rare forms are not modelled but declared unsure (four
    doubt cycles, 2026-10-02, each found ones that hid a command): a quote right after `$` ($'...' and $$'), a #
    right after an operator character, `$(` or a backtick, a ${...} holding a quote, #, $, brace, backslash or
    newline, any << that is not a blank then <<[-] then a word tag (wholly quoted or plain), or follows (( or [[,
    and an unquoted tag's body line ending in a backslash (bash joins it to the next line).
    """
    text = command.replace("\r\n", "\n")
    segments: list[str] = []
    current: list[str] = []  # one element per character, or per escaped pair (a `\\` and the character after it)
    heredocs: list[tuple[str, bool, bool]] = []  # (closing word, <<- strips tabs, tag unquoted), on the current line
    frames: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        inner = frames[-1] if frames else ""
        if inner == "'":  # nothing is special inside single quotes but the closing quote
            current.append(c)
            if c == "'":
                frames.pop()
            i += 1
            continue
        if c == "\\" and i + 1 < n:
            if text[i + 1] != "\n":  # an escaped newline joins the two lines
                current.append(text[i:i + 2])
            i += 2
            continue
        if text.startswith("${", i):  # in a command context or inside double quotes alike
            end = text.find("}", i + 2)
            if end < 0 or UNSURE_IN_BRACES & set(text[i + 2:end]):
                return None
            current.append(text[i:end + 1])
            i = end + 1
            continue
        if inner == '"':
            if text.startswith("$(", i):
                frames.append("$(")
                current.append("$(")
                i += 2
                continue
            if c == '"':
                frames.pop()
            elif c == "`":
                frames.append(c)
            current.append(c)
            i += 1
            continue
        # a command context: the top level, inside $( ... ), or inside backticks
        if c in "'\"" and current and current[-1] == "$":
            return None  # $'...' (escapes inside) or $$ then a quote: unsure
        if c in "'\"":
            frames.append(c)
        elif c == "`" and inner == "`":
            frames.pop()
        elif c == "`":
            frames.append(c)
        elif text.startswith("$(", i):
            frames.append("$(")
            current.append("$(")
            i += 2
            continue
        elif c == "(" and inner in ("$(", "("):
            frames.append("(")
        elif c == ")" and inner in ("$(", "("):
            frames.pop()
        elif c == "#" and current and current[-1] in OPERATOR_CHARS + ("$(", "`"):
            return None  # a word may begin there with no blank: unsure whether a comment
        elif c == "#" and (not current or current[-1] in BLANKS):
            end = text.find("\n", i)
            i = n if end < 0 else end
            continue
        elif text.startswith("<<<", i):  # a here-string: its word is data, and no body follows
            current.append("<<<")
            i += 3
            continue
        elif text.startswith("<<", i):
            head = "".join(current)
            m = HEREDOC.match(text, i)
            if m is None or (current and current[-1] not in BLANKS) or "((" in head or "[[" in head:
                return None  # an arithmetic or [[ ]] << is a shift, not a heredoc
            tag = HEREDOC_TAG.fullmatch(m.group(2))
            if tag is None:
                return None
            word = next(g for g in tag.groups() if g is not None)
            heredocs.append((word, m.group(1) == "-", tag.group(3) is not None))
            current.append(m.group(0))
            i = m.end()
            continue
        elif c == "\n":
            if frames:
                current.append(c)
            else:
                segments.append("".join(current))
                current = []
            i += 1
            for word, strip_tabs, unquoted in heredocs:  # each body runs to its own closing line, in the order opened
                while True:
                    if i >= n:
                        return None  # no closing line: unsure
                    end = text.find("\n", i)
                    line = text[i:] if end < 0 else text[i:end]
                    i = n if end < 0 else end + 1
                    if unquoted and line.endswith("\\"):
                        return None  # an unquoted tag's body joins a line ending in \ to the next: unsure
                    if (line.lstrip("\t") if strip_tabs else line) == word:
                        break
            heredocs = []
            continue
        elif not frames:
            op = next((s for s in SEPARATORS if text.startswith(s, i)), "")
            if op:
                segments.append("".join(current))
                current = []
                i += len(op)
                continue
        current.append(c)
        i += 1
    if frames:
        return None
    segments.append("".join(current))
    return segments


def _base(token: str) -> str:
    """`C:/x/python3.12.exe` -> `python`; `./pip3` -> `pip3`; `pre-commit` unchanged."""
    name = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if name.endswith(".exe"):
        name = name[:-4]
    m = re.match(r"^(python)\d(?:\.\d+)?$", name)
    return m.group(1) if m else name


def _tokens(segment: str) -> list[str]:
    try:
        toks = shlex.split(segment, posix=True)
    except ValueError:
        toks = segment.split()
    while toks and ASSIGNMENT.match(toks[0]):
        toks = toks[1:]
    return toks


def _is_tool_script(path: str) -> bool:
    """A .py file inside a folder named `scripts` (a skill's tool script, which shells out to uv itself)."""
    parts = PurePosixPath(path.replace("\\", "/")).parts
    return path.endswith(".py") and "scripts" in parts[:-1]


def _outside_project(path: str, cwd: Path) -> bool:
    """A script path that resolves outside the project root, after `~` expansion, is a global tool (llm-wiki's
    ~/.claude/wiki-scripts/, a user's own tooling), not project code (investment-agent's report, 2026-09-15)."""
    p = Path(os.path.expanduser(path))
    if not p.is_absolute():
        p = cwd / p
    try:
        p.resolve().relative_to(cwd.resolve())
    except ValueError:
        return True
    except OSError:
        return False
    return False


def _under_project_code(path: str, cwd: Path) -> bool:
    """A .py path under src/, tests/, or a package folder (a folder holding __init__.py) of the project."""
    p = path.replace("\\", "/").lstrip("./")
    first = p.split("/", 1)[0]
    if first in ("src", "tests", "test"):
        return True
    return (cwd / first).is_dir() and (cwd / first / "__init__.py").exists()


def decide_segment(segment: str, cwd: Path) -> Verdict:
    """The verdict for one segment; a refusal's `text` is the uv form of the same call."""
    toks = _tokens(segment)
    if not toks:
        return Verdict(True, "")
    raw_first = toks[0]
    first = _base(raw_first)
    rest = toks[1:]
    lowered = raw_first.replace("\\", "/").lower()

    if first in ("uv", "uvx"):
        return Verdict(True, "")
    if ".venv/" in lowered and first in PYTHONS:
        return Verdict(True, "")
    if first in ("source", ".") and rest and rest[0].replace("\\", "/").lower().endswith("activate"):
        return Verdict(False, "uv run <the command you meant to run> (activation does not persist across Bash calls)")
    if lowered.endswith("activate") or lowered.endswith("activate.bat") or lowered.endswith("activate.ps1"):
        return Verdict(False, "uv run <the command you meant to run> (activation does not persist across Bash calls)")
    if first in PIPS:
        return Verdict(False, _pip_escape(rest))
    if first in ("virtualenv", "venv"):
        return Verdict(False, "uv sync (uv creates and updates .venv itself)")
    if first in PROJECT_TOOLS:
        return Verdict(False, "uv run " + _join(toks))
    if first in PYTHONS:
        if not rest:
            return Verdict(False, "uv run python")
        arg = rest[0]
        if arg in ("--version", "-V", "-VV"):
            return Verdict(True, "")
        if arg == "-m":
            module = rest[1] if len(rest) > 1 else ""
            if module == "pip":
                return Verdict(False, _pip_escape(rest[2:]))
            if module == "venv":
                return Verdict(False, "uv sync (uv creates and updates .venv itself)")
            return Verdict(False, "uv run python " + _join(rest))
        if arg in ("-c", "-"):
            return Verdict(False, "uv run python " + _join(rest))
        if arg.startswith("-"):
            return Verdict(False, "uv run python " + _join(rest))
        if arg.startswith(("$", "%")):
            # a hook reads text: it cannot see what a shell variable holds, so it cannot tell a global tool from
            # project code; refusing is the safe side, and a literal path outside the project is allowed (task 40)
            return Verdict(False, "uv run python " + " ".join(rest) + " — or write the script path literally: the hook "
                                  "cannot see what a shell variable holds, and a literal path outside the project is allowed")
        if _is_tool_script(arg):
            return Verdict(True, "")
        if arg.endswith(".py") and _outside_project(arg, cwd):
            return Verdict(True, "")
        if arg.endswith(".py") and not _under_project_code(arg, cwd):
            # a stray script at the project root still imports the project; uv run resolves it in the venv
            return Verdict(False, "uv run python " + _join(rest))
        return Verdict(False, "uv run python " + _join(rest))
    return Verdict(True, "")


def _join(toks: list[str]) -> str:
    return shlex.join(toks) if hasattr(shlex, "join") else " ".join(toks)


def _pip_escape(args: list[str]) -> str:
    if args and args[0] == "install":
        pkgs = [a for a in args[1:] if not a.startswith("-")]
        if "-e" in args or "." in pkgs:
            return "uv sync (the project itself is installed by uv)"
        if "-r" in args:
            return "uv add -r <requirements file>  (then commit uv.lock)"
        return "uv add " + " ".join(pkgs) if pkgs else "uv add <package>"
    if args and args[0] == "uninstall":
        pkgs = [a for a in args[1:] if not a.startswith("-")]
        return "uv remove " + " ".join(pkgs) if pkgs else "uv remove <package>"
    return "uv pip " + " ".join(args) if args else "uv pip <args>"


def decide(payload: HookPayload, cwd: str, uv_on_path: bool) -> Verdict:
    """The verdict for a whole call; `text` is the reason. Active only in a uv project: pyproject.toml in cwd and uv on PATH."""
    if payload.get("tool_name") != "Bash":
        return Verdict(True, "not a Bash call")
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command.strip():
        return Verdict(True, "empty command")
    root = Path(cwd)
    if not (root / "pyproject.toml").exists():
        return Verdict(True, "no pyproject.toml in the working directory")
    if not uv_on_path:
        return Verdict(True, "uv is not on PATH")
    if (root / LIFT_FILE).exists():
        _log(root, f"lifted ({LIFT_FILE} present): {command.strip()[:200]}")
        return Verdict(True, "lifted for this session")
    for segment in _segments(command):
        verdict = decide_segment(segment, root)
        if not verdict.allow:
            return Verdict(False, f"enforce-uv: refused '{segment.strip()}'. Run it as: {verdict.text}. "
                                  f"(Lift for this session: touch {LIFT_FILE})")
    return Verdict(True, "every segment is a uv form or a tool script")


def _log(root: Path, line: str) -> None:
    try:
        log = root / LOG_FILE
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as fh:
            fh.write(line.rstrip() + "\n")
    except OSError:
        pass


def _uv_on_path() -> bool:
    from shutil import which
    return which("uv") is not None


def self_test() -> int:
    import tempfile
    n = 0

    def check(cond: bool, what: str) -> None:
        nonlocal n
        n += 1
        if not cond:
            print(f"FAIL self-test: {what}")
            sys.exit(1)

    def bash(cmd: str) -> HookPayload:
        return {"tool_name": "Bash", "tool_input": {"command": cmd}}

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src" / "pkg").mkdir(parents=True)
        (root / "mypkg").mkdir()
        (root / "mypkg" / "__init__.py").write_text("", encoding="utf-8")
        # inactive outside a uv project
        ok, why = decide(bash("pytest"), td, True)
        check(ok and "no pyproject" in why, "no pyproject.toml: the hook is inactive")
        (root / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n", encoding="utf-8")
        ok, why = decide(bash("pytest"), td, False)
        check(ok and "not on PATH" in why, "uv missing: the hook is inactive")
        ok, _ = decide({"tool_name": "Read", "tool_input": {"file_path": "x"}}, td, True)
        check(ok, "a non-Bash call is let through")
        # refusals name the escape
        ok, why = decide(bash("pip install requests"), td, True)
        check(not ok and "uv add requests" in why and LIFT_FILE in why, "pip install -> uv add, lift named")
        ok, why = decide(bash("python -m pip install rich httpx"), td, True)
        check(not ok and "uv add rich httpx" in why, "python -m pip install -> uv add")
        ok, why = decide(bash("pip uninstall rich"), td, True)
        check(not ok and "uv remove rich" in why, "pip uninstall -> uv remove")
        ok, why = decide(bash("pytest -q tests/"), td, True)
        check(not ok and "uv run pytest -q tests/" in why, "bare pytest -> uv run pytest")
        v = decide(bash("pytest"), td, True)
        check(isinstance(v, Verdict) and not v.allow and "uv run pytest" in v.text, "a decision is a Verdict with named fields")
        ok, why = decide(bash("ruff check . && ruff format ."), td, True)
        check(not ok and "uv run ruff check ." in why, "the first refused segment of a chain is named")
        ok, why = decide(bash("cd sub && pyright src"), td, True)
        check(not ok and "uv run pyright src" in why, "a cd segment is skipped, the tool segment refused")
        ok, why = decide(bash("python -m pkg.cli --help"), td, True)
        check(not ok and "uv run python -m pkg.cli --help" in why, "python -m module -> uv run python -m")
        ok, why = decide(bash("python src/pkg/main.py"), td, True)
        check(not ok and "uv run python src/pkg/main.py" in why, "python <src path> -> uv run python")
        ok, why = decide(bash("python mypkg/cli.py"), td, True)
        check(not ok, "python <package path> -> refused")
        ok, why = decide(bash("python -c 'import pkg'"), td, True)
        check(not ok and "uv run python -c" in why, "python -c -> uv run python -c")
        ok, why = decide(bash("python"), td, True)
        check(not ok and "uv run python" in why, "a bare python REPL -> uv run python")
        ok, why = decide(bash("source .venv/bin/activate && pytest"), td, True)
        check(not ok and "does not persist" in why, "activation is refused with the reason")
        ok, why = decide(bash(".venv\\Scripts\\activate"), td, True)
        check(not ok and "does not persist" in why, "a Windows activate is refused")
        ok, why = decide(bash("python -m venv .venv"), td, True)
        check(not ok and "uv sync" in why, "python -m venv -> uv sync")
        ok, why = decide(bash("PYTHONPATH=src pytest"), td, True)
        check(not ok and "uv run pytest" in why, "a leading VAR=value is stripped before the decision")
        # allowances
        ok, _ = decide(bash("uv run pytest -q"), td, True)
        check(ok, "uv run pytest is allowed")
        ok, _ = decide(bash("uvx ruff check ."), td, True)
        check(ok, "uvx <tool> is allowed")
        ok, _ = decide(bash("uv add httpx && uv lock --check"), td, True)
        check(ok, "a chain of uv forms is allowed")
        ok, _ = decide(bash("python C:/Users/me/.claude/skills/x/scripts/check.py --self-test"), td, True)
        check(ok, "a scripts/<x>.py tool script is allowed (absolute path)")
        ok, _ = decide(bash("python .claude/skills/x/scripts/check.py"), td, True)
        check(ok, "a scripts/<x>.py tool script is allowed (relative path)")
        # (f) a script outside the project root is a global tool (llm-wiki's ~/.claude/wiki-scripts/), not project code
        outside = (root.parent / "elsewhere-tools" / "wiki-update.py").as_posix()
        ok, _ = decide(bash(f"python {outside} --topic x"), td, True)
        check(ok, "a script outside the project root is allowed (absolute path)")
        ok, _ = decide(bash("python ~/.claude/wiki-scripts/wiki-update.py --topic x"), td, True)
        check(ok, "a script under ~ outside the project is allowed (~ expanded)")
        ok, why = decide(bash(f"python {(root / 'tool.py').as_posix()}"), td, True)
        check(not ok and "uv run python" in why, "a script inside the project, by absolute path, is still refused")
        # (40) a path held in a shell variable cannot be resolved by a hook that reads text: still refused, but the
        # message says to write the path literally (investment-agent, 2026-09-15; documented, not resolved, 2026-09-23)
        ok, why = decide(bash("S=~/.claude/wiki-scripts/wiki-update.py; python $S --topic x"), td, True)
        check(not ok and "literally" in why and "uv run python $S --topic x" in why, "python $VAR: refused, told to write the path literally")
        ok, why = decide(bash('python "${S}" --topic x'), td, True)
        check(not ok and "literally" in why, "python \"${VAR}\": the same message")
        ok, _ = decide(bash("python --version"), td, True)
        check(ok, "python --version is allowed")
        ok, _ = decide(bash(".venv/Scripts/python.exe -m pkg"), td, True)
        check(ok, "the venv interpreter by path is allowed")
        ok, _ = decide(bash("git status && ls src"), td, True)
        check(ok, "unrelated commands are allowed")
        ok, _ = decide(bash("echo 'pytest is great'"), td, True)
        check(ok, "a tool name inside an argument is not a command")
        # (137) only commands are read: a heredoc body, quoted text and a comment are data (investment-agent,
        # 2026-10-01: a notes heredoc was refused because a body line began "coverage")
        ok, _ = decide(bash("cat >> notes.md <<'EOF'\ncoverage stayed at 98.69%\npytest passed\nEOF"), td, True)
        check(ok, "a quoted-tag heredoc body is data, not commands")
        ok, _ = decide(bash("git commit -F - <<EOF\npython -m is how it runs\nEOF"), td, True)
        check(ok, "an unquoted-tag heredoc body is data, not commands")
        ok, why = decide(bash("cat <<-EOF > x.md\n\tpip install is refused\n\tEOF\npytest -q"), td, True)
        check(not ok and "refused 'pytest -q'" in why, "after a <<- heredoc's tab-indented close, the next command is read")
        ok, why = decide(bash("cat <<'A' <<'B'\nruff\nA\nmypy\nB\nruff check ."), td, True)
        check(not ok and "refused 'ruff check .'" in why, "two heredocs on one line: both bodies skipped, the command after read")
        ok, _ = decide(bash("cat <<'EOF'\r\ncoverage x\r\nEOF\r\n"), td, True)
        check(ok, "a CRLF heredoc body is data, not commands")
        ok, why = decide(bash("python - <<'EOF'\nimport os\nEOF"), td, True)
        check(not ok and "uv run python -" in why, "python - fed by a heredoc is still refused")
        ok, _ = decide(bash("echo 'done; pytest -q passes'"), td, True)
        check(ok, "a separator inside single quotes does not split")
        ok, _ = decide(bash('git commit -m "gates: ruff && pytest green"'), td, True)
        check(ok, "a separator inside double quotes does not split")
        ok, _ = decide(bash('git commit -m "fix the loader\npytest now passes"'), td, True)
        check(ok, "a newline inside quotes does not split")
        ok, _ = decide(bash("echo a\\; pytest"), td, True)
        check(ok, "an escaped ; is a literal, not a separator")
        ok, _ = decide(bash("ls  # then pytest -q; ruff"), td, True)
        check(ok, "a comment is not a command")
        ok, why = decide(bash("echo a#b && pytest"), td, True)
        check(not ok and "refused 'pytest'" in why, "a # inside a word is not a comment")
        ok, why = decide(bash("pytest \\\n  -q"), td, True)
        check(not ok and "uv run pytest -q" in why, "a line continuation joins the command")
        ok, why = decide(bash("echo a\\ #x; pytest"), td, True)
        check(not ok and "refused 'pytest'" in why, "an escaped space before # does not start a comment")
        ok, why = decide(bash("echo $'a\\'b'; pytest; echo $'c\\'d'"), td, True)
        check(not ok and "refused 'pytest'" in why, "a $'...' string is unsure: the plain split refuses")
        ok, why = decide(bash("echo $$'a\\'; pytest; echo $$'b\\'"), td, True)
        check(not ok and "refused 'pytest'" in why, "a quote after $$ is unsure: the plain split refuses")
        ok, why = decide(bash("echo a &#'\npytest\n#'"), td, True)
        check(not ok and "refused 'pytest'" in why, "a # right after & is unsure: the plain split refuses")
        ok, why = decide(bash("cat <<EOF\na \\\nEOF\nit's\nEOF\npytest\necho it's"), td, True)
        check(not ok and "refused 'pytest'" in why, "a backslash-newline in an unquoted heredoc body is unsure")
        ok, why = decide(bash("cat >> n.md <<'EOF'\nC:\\dir\\\nEOF\npytest"), td, True)
        check(not ok and "refused 'pytest'" in why, "a quoted tag's body keeps a trailing backslash as text and closes")
        # each case below is decided by one unsure rule alone (mutation check, 2026-10-02): its rule removed, it fails
        ok, why = decide(bash("echo $'it\\'s'\npytest\necho 'x"), td, True)
        check(not ok and "refused 'pytest'" in why, "a $'...' that would end balanced if misread is unsure")
        ok, why = decide(bash('v=; echo ${v:-"}"}; pytest\necho "'), td, True)
        check(not ok and "refused 'pytest'" in why, "a quote inside ${...} is unsure")
        ok, _ = decide(bash('cat <<< "a; pytest -q"'), td, True)
        check(ok, "a here-string's quoted word is data, not commands")
        ok, why = decide(bash("for ((i=0;i<1<<k;i++)); do :; done\npytest\nk"), td, True)
        check(not ok and "refused 'pytest'" in why, "a << with no blank before it is unsure, even before a word")
        ok, why = decide(bash("echo $(( 1 << k ))\npytest\nk"), td, True)
        check(not ok and "refused 'pytest'" in why, "a << after (( is unsure, even with blanks and a word")
        ok, why = decide(bash("cat <<<x\npytest\nx"), td, True)
        check(not ok and "refused 'pytest'" in why, "a here-string <<< is not a heredoc")
        ok, why = decide(bash("for ((i=0;i<1<<1;i++)); do :; done\npytest\n1"), td, True)
        check(not ok and "refused 'pytest'" in why, "a << with no space before it is unsure: the plain split refuses")
        ok, why = decide(bash("echo $(# it's\n true) ; pytest ; echo $(echo it\\'s)"), td, True)
        check(not ok and "refused 'pytest'" in why, "a # straight after $( is unsure: the plain split refuses")
        ok, why = decide(bash("v=a; echo ${v// #/_}; pytest"), td, True)
        check(not ok and "refused 'pytest'" in why, "a # inside ${...} is not a comment")
        ok, why = decide(bash("echo ${HOME}/x && pytest"), td, True)
        check(not ok and "refused 'pytest'" in why, "a plain ${VAR} is read through")
        for tag in ('E"O"F', "EO\\F", "'E'F"):
            ok, why = decide(bash(f"cat <<{tag}\nx\nEOF\npytest\nE"), td, True)
            check(not ok and "refused 'pytest'" in why, f"a mixed-quoted heredoc tag <<{tag} is unsure: the plain split refuses")
        ok, why = decide(bash("echo \"$(echo 'a\"b')\"; pytest; echo \"'\""), td, True)
        check(not ok and "refused 'pytest'" in why, "quotes inside $( ) inside double quotes are their own")
        msg = "git commit -m \"$(cat <<'EOF'\nfix: the loader\n\npytest passes; ruff && don't panic\nEOF\n)\""
        ok, _ = decide(bash(msg), td, True)
        check(ok, "the commit-message form $(cat <<'EOF' ... EOF) is data")
        ok, why = decide(bash(msg + " && pytest -q"), td, True)
        check(not ok and "refused 'pytest -q'" in why, "a command after the commit-message form is read")
        ok, why = decide(bash("echo `echo 'x;y'`; pytest"), td, True)
        check(not ok and "refused 'pytest'" in why, "quotes inside backticks are their own")
        # input the segmenter cannot read for certain falls back to splitting everywhere: it over-refuses, never hides
        ok, why = decide(bash("x=$((1<<2))\npytest\n2"), td, True)
        check(not ok and "refused 'pytest'" in why, "an arithmetic << is unsure: the plain split refuses the next line")
        ok, why = decide(bash("echo 'oops && pytest -q"), td, True)
        check(not ok and "uv run pytest" in why, "an unbalanced quote falls back to the plain split and refuses")
        ok, why = decide(bash("cat <<EOF\nnotes\npytest -q"), td, True)
        check(not ok and "uv run pytest -q" in why, "a heredoc with no closing line falls back to the plain split and refuses")
        # the lift file
        (root / LIFT_FILE).parent.mkdir(parents=True, exist_ok=True)
        (root / LIFT_FILE).write_text("", encoding="utf-8")
        ok, why = decide(bash("pytest"), td, True)
        check(ok and "lifted" in why, "the .off file lifts the hook")
        check("lifted" in (root / LOG_FILE).read_text(encoding="utf-8"), "a lifted call is logged")
        (root / LIFT_FILE).unlink()
        # fail open
        ok, _ = decide({"tool_name": "Bash", "tool_input": {}}, td, True)
        check(ok, "a Bash call with no command is let through")
        ok, _ = decide({}, td, True)
        check(ok, "an empty payload is let through")
    if n < SELF_TEST_MINIMUM:
        print(f"FAIL self-test ran {n} assertions, below the floor of {SELF_TEST_MINIMUM}")
        return 1
    print(f"PASS enforce_uv self-test ({n} assertions; floor {SELF_TEST_MINIMUM})")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    cwd = os.getcwd()
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        cwd = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or cwd
        allow, reason = decide(payload, cwd, _uv_on_path())
    # Broad on purpose (fail open): a guard that breaks must not block a legitimate call. No suppression
    # comment: the installed copy lands in a project's diff, where floor-guard reads one as a lowered bar,
    # and the pack's ruff baseline already excludes .claude/.
    except Exception as exc:
        _log(Path(cwd), f"skipped (hook error, call allowed): {type(exc).__name__}: {exc}")
        return 0
    if allow:
        return 0
    sys.stderr.write(reason + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
