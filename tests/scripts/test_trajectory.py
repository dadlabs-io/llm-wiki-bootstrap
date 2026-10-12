"""tests/skills/_trajectory.py: what counts as a read, and how each rule kind decides (task #99).

Run: uv run python tests/scripts/test_trajectory.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills"))
import _trajectory as T  # noqa: E402

FAILS = []


def call(i, name, **inp):
    return {"id": f"t{i}", "name": name, "input": inp, "parent_tool_use_id": inp.pop("_worker", None)}


def run(*calls, errors=None):
    return {"tool_calls": list(calls), "error_texts": errors or {}}


def expect(label, got, want):
    print(f"{'ok ' if got == want else 'FAIL'} {label}: {got}")
    if got != want:
        FAILS.append(label)


RUBRIC = {"id": "rubric", "kind": "read_before", "path": r"spec\.md$", "action": r"file\.py .*--tier [1-4]",
          "tool": "Bash"}
NEVER = {"id": "no head", "kind": "never", "pattern": r"query\.py[^|;\n]*\|\s*head", "tool": "Bash"}


def ok(r, rules):
    res = T.check(r, rules)
    return [x["ok"] for x in res]


# 1. a Read before the action counts; after it does not
expect("read before the action", ok(run(call(1, "Read", file_path="C:\\nb\\spec.md"),
                                        call(2, "Bash", command="python file.py --tier 3")), [RUBRIC]), [True])
expect("read after the action", ok(run(call(1, "Bash", command="python file.py --tier 3"),
                                       call(2, "Read", file_path="/nb/spec.md")), [RUBRIC]), [False])
# 2. a refused Read (the read guard) did not read
expect("refused read does not count", ok(run(call(1, "Read", file_path="/nb/spec.md"),
                                             call(2, "Bash", command="python file.py --tier 3"),
                                             errors={"t1": "hook error: read-guard: partial read"}), [RUBRIC]), [False])
# 3. cd, then a relative path; a variable set in the same command; a continued line
expect("cd then cat", ok(run(call(1, "Bash", command="cd /nb/docs && cat spec.md"),
                             call(2, "Bash", command="python file.py --tier 2")), [RUBRIC]), [True])
expect("variable path", ok(run(call(1, "Bash", command='S=/nb/spec.md; cat "$S"'),
                               call(2, "Bash", command="python file.py --tier 2")), [RUBRIC]), [True])
expect("continued line is one command", ok(run(call(1, "Read", file_path="/nb/spec.md"),
                                               call(2, "Bash", command="python file.py \\\n  --tier 1")), [RUBRIC]), [True])
# 4. never: a hit fails, a clean run passes, a rule with nothing to act on is not reported
expect("never: hit", ok(run(call(1, "Bash", command="python query.py 'x' | head -5")), [NEVER]), [False])
expect("never: clean, read_before not applicable", ok(run(call(1, "Bash", command="python query.py 'x'")),
                                                       [NEVER, RUBRIC]), [True])
# 5. looked: a Read that failed because the file is missing counts as looking
LOOK = {"id": "look", "kind": "read_before", "path": r"task\.md$", "action": r"file_path=\S*task\.md",
        "tool": "Write", "looked": True}
expect("missing-file read counts with looked",
       ok(run(call(1, "Read", file_path="/w/task.md"), call(2, "Write", file_path="/w/task.md", content="x"),
              errors={"t1": "File does not exist."}), [LOOK]), [True])

print(f"\n{9 - len(FAILS)}/9 passed")
sys.exit(1 if FAILS else 0)
