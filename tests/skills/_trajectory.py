"""What a session did on the way, for checks that grade the run and not only its output (task #99).

From WN-S7 (agentic-design, 2026-10-12): a passing output can hide a skipped step. SWE-CC found
agents "initiate policy searches in only 28.9% of executions" even when told to search, and nearly
half of all policy violations happen during intermediate steps. So a suite can also ask: did the
session open the file the skill told it to read, before the step that needs it, and did a step the
skill forbids happen anywhere in the run?

A refused call did nothing, so it never counts (the read guard refuses a partial read; the
harness or the classifier refuses others). A spawned agent's calls carry the id of the call that
spawned it, so a rule can look at the main session, the workers, or both.

Each suite lists its rules in `<skill>/trajectory_rules.py` as RULES; `check(run, rules)` returns
one result per applicable rule, in the shape every check.py already uses.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field

# Shell commands that read a file's content (not a listing, a search or a write)
READERS = {"cat", "type", "less", "more", "head", "tail", "sed", "awk", "Get-Content", "gc"}
# `find ... -name '*.md' | ... cat` reads every file it finds without naming one (wiki-lint, 2026-09-17)
BULK_READ = re.compile(r"\bfind\b[^|;]*-name[^|;]*\|.*\b(cat|xargs\s+cat)\b|for\s+\w+\s+in\s+\$\(find\b.*\bcat\b")


@dataclass
class Step:
    i: int          # position in the run
    name: str       # tool name
    text: str       # the command, or the path, or the prompt: what rules match against
    paths: list[str] = field(default_factory=list)  # files this step read
    worker: bool = False  # made by a spawned agent, not the main session
    wrote: list[str] = field(default_factory=list)  # files this step wrote with the Write tool


def _norm(p: str) -> str:
    return str(p).replace("\\", "/")


def expand_vars(cmd: str) -> str:
    """Put the value of each simple variable a command sets (`R=raw/x.md;`, `$s='…'` in
    PowerShell) in place of its uses later in the same command, so `cat "$R"` names its file."""
    for m in re.finditer(r"(?:^|[\s;&])\$?(\w+)=(\"[^\"]*\"|'[^']*'|[^\s;&|]+)", cmd):
        name, value = m.group(1), m.group(2).strip("\"'")
        rest = cmd[m.end():]
        rest = re.sub(r"\$\{%s\}|\$%s\b" % (name, name), lambda _: value, rest)
        cmd = cmd[:m.end()] + rest
    return cmd


def _shell_reads(cmd: str) -> list[str]:
    """Paths a shell command reads with a reader verb. Loose on purpose: a path in a pipeline or
    after `&&` counts; one only listed (`ls`) or searched (`grep`) does not. A relative path is
    taken from the folder the command last `cd`-ed into."""
    out, cwd = [], ""
    for part in re.split(r"&&|\|\||;|\|", expand_vars(cmd)):
        try:
            words = shlex.split(part, posix=True)
        except ValueError:
            words = part.split()
        if not words:
            continue
        verb = words[0].rsplit("/", 1)[-1]
        if verb in ("cd", "Set-Location", "pushd") and len(words) > 1:
            cwd = _norm(words[1])
        elif verb in READERS:
            for w in words[1:]:
                if w.startswith("-") or not ("/" in w or "." in w):
                    continue
                w = _norm(w)
                out.append(w if re.match(r"^([A-Za-z]:)?/", w) or not cwd else f"{cwd}/{w}")
    return out


def steps(run: dict, looked: bool = False) -> list[Step]:
    """The run's calls in order, refused ones left out. With `looked`, a Read that failed only
    because the file does not exist stays in: the session looked before writing a new file."""
    errors = run.get("error_texts") or {}
    out = []
    for i, c in enumerate(run.get("tool_calls") or []):
        err = errors.get(c.get("id"))
        if err is not None and not (looked and c.get("name") == "Read"
                                    and re.search(r"does not exist|not found|no such file", err, re.I)):
            continue
        name, inp = c.get("name") or "", c.get("input") or {}
        worker = bool(c.get("parent_tool_use_id"))
        if name == "Read":
            p = _norm(inp.get("file_path") or "")
            out.append(Step(i, name, p, [p], worker))
        elif name in ("Bash", "PowerShell"):
            # a command continued over lines (`\` in bash, a backtick in PowerShell) is one line to a rule
            cmd = re.sub(r"(\\|`)\r?\n", " ", str(inp.get("command") or ""))
            reads = _shell_reads(cmd)
            if BULK_READ.search(cmd):
                reads.append("*bulk*")
            out.append(Step(i, name, cmd, reads, worker))
        elif name in ("Agent", "Task"):
            out.append(Step(i, name, f"{inp.get('description', '')}\n{inp.get('prompt', '')}"
                                     f"\nname={inp.get('name', '')}", [], worker))
        else:
            out.append(Step(i, name, " ".join(f"{k}={v}" for k, v in inp.items()
                                              if isinstance(v, (str, int))), [], worker,
                            [_norm(inp["file_path"])] if name == "Write" and inp.get("file_path") else []))
    return out


def _scope(ss: list[Step], scope: str) -> list[Step]:
    return [s for s in ss if scope == "all" or (scope == "workers") == s.worker]


def check(run: dict, rules: list[dict]) -> list[dict]:
    """One result per rule that applies to this run. A rule:

    - id, rule: a short name, and the skill's own words it tests (for the report)
    - kind "read_before": the first step matching `action` (a regex over the step's text) comes
      after a read of a file matching `path` (a regex over the path). Applies only when an action
      ran. With `path_from_action` (a regex whose group 1 is a path in the action's own text), every
      such action needs an earlier read of the file it names; an action naming none is skipped.
    - kind "never": no step matches `pattern`. Applies to every run, or only when `when` (a regex)
      matches some step.
    - scope: "main" (default), "workers" or "all"; `tool`: limit `action` / `pattern` to one tool.
    - looked: true for a file the run may be creating: a Read refused as missing counts as a read.
    """
    ss, ss_looked = steps(run), steps(run, looked=True)
    res = []
    for r in rules:
        scoped = _scope(ss_looked if r.get("looked") else ss, r.get("scope", "main"))
        tools = r.get("tool")
        tools = [tools] if isinstance(tools, str) else tools
        pool = [s for s in scoped if not tools or s.name in tools]
        name = f"run: {r['id']}"
        if r["kind"] == "read_before":
            act = re.compile(r["action"], re.S)
            actions = [s for s in pool if act.search(s.text)]
            if r.get("path_from_action"):
                # the file to have read is named by the action itself (e.g. its --raw-path)
                wanted = []
                for s in actions:
                    m = re.search(r["path_from_action"], expand_vars(s.text))
                    if m:  # by file name: the action may spell its folder with a variable or a relative path
                        name_only = _norm(m.group(1)).rsplit("/", 1)[-1]
                        wanted.append((s, re.compile(re.escape("/" + name_only) + "$", re.I)))
            else:
                wanted = [(actions[0], re.compile(r["path"], re.I))] if actions else []
            if not wanted:
                continue
            # also_from: a regex whose group 1 names, in an earlier step, a file that stands in for
            # the one wanted (a local file --fetch-only copied into raw/); reading it, or having
            # written it (pasted text saved to a temp file), counts
            alts = []
            if r.get("also_from"):
                for o in scoped:
                    for m in re.finditer(r["also_from"], o.text):
                        alts.append((o.i, "/" + _norm(m.group(1)).lstrip("./")))

            def known(o: Step, s: Step, pat) -> bool:
                if o.i >= s.i:
                    return False
                if any(pat.search("/" + p.lstrip("./")) or p == "*bulk*" and r.get("bulk_ok") for p in o.paths):
                    return True
                return any(ai < s.i and ("/" + p.lstrip("./")).lower().endswith(a.lower())
                           for ai, a in alts for p in o.paths + o.wrote)

            missed = [s for s, pat in wanted if not any(known(o, s, pat) for o in scoped)]
            res.append({"name": name, "ok": not missed,
                        "detail": "" if not missed else f"no read before: {missed[0].text[:2000]}"})
        elif r["kind"] == "never":
            if r.get("when") and not any(re.search(r["when"], s.text, re.S) for s in scoped):
                continue
            pat = re.compile(r["pattern"], re.S)
            hits = [s for s in pool if pat.search(s.text)]
            res.append({"name": name, "ok": not hits,
                        "detail": " ;; ".join(h.text[:2000] for h in hits[:2])})
        else:
            raise ValueError(f"unknown rule kind {r['kind']!r} in {r['id']}")
    return res
