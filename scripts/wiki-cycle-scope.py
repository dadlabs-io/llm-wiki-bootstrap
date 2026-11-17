#!/usr/bin/env python3
"""
What a /wiki-cycle step reads, decided by a script instead of by the model.

    wiki-cycle-scope.py --topic N semantic --run-folder <rf> [--all]
    wiki-cycle-scope.py --topic N claims   --run-folder <rf> [--all]
    wiki-cycle-scope.py --topic N synthesis --run-folder <rf> [--all]
    wiki-cycle-scope.py --topic N checker  --run-folder <rf> [--min-minutes 15]
    wiki-cycle-scope.py --topic N checker-log --run-folder <rf> --entry <slug> --report <file.json>
    wiki-cycle-scope.py --topic N checker-corrected --entry <slug>
    wiki-cycle-scope.py --topic N cost --run-folder <rf> --mark start|end [--session-id <id>]
    wiki-cycle-scope.py --topic N session-cost [--session-id <id>]
    wiki-cycle-scope.py --topic N promote --run-folder <rf>
    wiki-cycle-scope.py --topic N unfinished --run-folder <rf>
    wiki-cycle-scope.py --topic N unfinished --mark-interrupted <cycle_id> --reason "<why>"
    wiki-cycle-scope.py --topic N writer <raw> [<raw> ...] [--ingester <config.json>]
    wiki-cycle-scope.py --topic N left-undone --run-folder <rf> [--today YYYY-MM-DD]
    wiki-cycle-scope.py --topic N lint-fixes --run-folder <rf> [--show | --applied <ids> --declined <ids>]

`semantic`: the entries added or revised since the last semantic lint (the newest
earlier run folder holding lint-semantic.json; its `timestamp` is the cut-off), plus
this run's staged entries in _inbox/proposed/. With --all, or when no semantic lint
has run yet, every entry. Writes <rf>/semantic-scope.txt, one path per line relative
to the notebook under a `#` header line, and prints the count and the cut-off.

`claims`: the entries no claim in _inbox/claims-index.json comes from, plus those
revised since the index was last written. With --all, or no index, every entry. Writes
<rf>/claims-scope.txt. Never a staged entry (task #184, 2026-10-19): one still staged at
this step waits for the user or was held by the checker, so its claims wait until it is
promoted.

`synthesis`: the live research/ entries added since the last synthesis the user answered
(the newest earlier synthesis.json with status completed; its `timestamp` is the cut-off).
Staged entries are never in it: synthesis reads wiki/. No best-practices pages: an empty
scope. With --all, or no earlier synthesis, every live research entry. Writes
<rf>/synthesis-scope.txt (task #176, 2026-10-19).

"Added" is a file created after the cut-off (git when the notebook is in a repository,
else its frontmatter `date`). "Revised" is `last_reviewed` on or after the cut-off's
day: it moves only when an entry is re-read and corrected. A plain "changed" was too
broad: on agentic-design it counted 237 entries a day after a lint, nearly all of them
machine edits (backlink blocks, lint fixes, promotions).

`checker`: the staged entries whose raw is a transcript at least --min-minutes long
(default: wiki-checker-config.json's min_transcript_minutes, else 15), from the raw's
`duration_seconds`: YouTube captions (wiki-fetch-youtube.py) and Whisper transcripts
(wiki-transcribe.py), the TRANSCRIPT_TYPES. A page that carries a transcript is not
counted (Mark, 2026-10-12). Writes <rf>/checker-scope.txt.

`checker-log`: appends one line to _inbox/reports/checker-log.jsonl from a checker's
report (entry, source minutes, finding counts by kind, verdict, model), so the pass
rate by length can be read later, and writes the verdict into the staged entry's sidecar
(`checker`: verdict, report, corrected false). wiki-promote.py holds an entry whose verdict
is `fix` until `checker-corrected --entry <slug>` records that it was corrected from its
report (task #178 row 8, 2026-10-22).

`models`: the model each kind of helper is spawned on, read from the setting files
(--ingester, --checker, --helpers; default the installed paths), printed one line per
role and written to <rf>/models.json. A cycle runs it at Step 0 and spawns from it,
because a sentence asking it to read the files was skipped in 21 of 22 test runs
(task #99, 2026-10-12): the workers got the agent description's default instead. A
file that is missing or unreadable is named, with the fallback used. The ingest workers'
line also gives the size from which a raw is written on another model (`large_raw_kb`,
`large_raw_model` in the ingester's file; 10 and opus when absent).

`writer`: which model writes each raw given, by its size on disk against that line:
`<raw>\t<KB>\t<model>` per raw, exit 1 when one is missing. Mark, 2026-11-09 (task #239):
Sonnet writes a raw under 10 KB, Opus one of 10 KB or more; on 10 sources Opus left 2
unsupported sentences to Sonnet's 17, with about twice the content on raws of 10 KB+.
Every agentic-design transcript of 15+ minutes was 15 KB or more, so the size line also
covers the long-transcript rule it replaced for writers.

`cost`: what the run cost, from the session's running total that the user's status line
saves to ~/.claude/session-cost/<session_id>.json (`total_cost_usd`, Claude Code's own
API-price estimate, subagents included; on a subscription plan it is a comparison figure,
not a bill). `--mark start` records the session's total in <rf>/cost.json; `--mark end`
reads it again and writes the difference to cost.json and cost.md. The session is the
newest file whose `cwd` is this folder (or --session-id); with no such file the step is
NOT checked (exit 3), never a zero (task #138, 2026-10-14). `session-cost [--session-id <id>]`
prints the session's running total alone, for /wrap-up's report (task #182, 2026-10-22).

`promote`: whether the cycle's new entries wait for the user or are promoted without
asking, from the notebook's confirm_before_promote (registry → project wiki-config.json →
true, as /wrap-up reads it). Prints one line and writes <rf>/promote-setting.txt. Until
2026-10-19 the cycle never read the setting: --full promoted everything and every other
mode staged everything (task #184).

`unfinished`: the earlier run folders (`_inbox/reports/<date>/<YYYY-MM-DD>-<NN>/` under the id's own date, as a
cycle files them; not <rf>) that never got
their `<cycle_id>-run-cycle-report.md`, unless their scratchpad says `interrupted`. Prints one line each, oldest
first, with the ways out (`/wiki-cycle <notebook> --resume <cycle_id>` only when the folder has a scratchpad, since a
run with none has nothing to resume; always `--topic <notebook> unfinished --mark-interrupted`, the notebook the
listing ran on, so a pasted line acts on the right one), or `unfinished: none`,
and writes <rf>/unfinished-runs.txt (`<cycle_id>` tab why). Exit 0 either way. Nothing is resumed or deleted.
One cycle runs on a notebook at a time (Mark's rule): the listing counts any earlier run still in progress as
dead, and `--mark-interrupted` rewrites it; there is no lock and no age check. `--run-folder` (list) and
`--mark-interrupted` (close) are separate commands: both together, or neither, is exit 2.
`--topic <notebook> unfinished --mark-interrupted <cycle_id> --reason "<why>"` closes one: its scratchpad's Status becomes `interrupted` and the
reason joins the Decisions log (a scratchpad is written when there is none); an unknown id is exit 2, nothing
written (task #240, lesson #10: a cycle died before its report and nothing flagged it).

`left-undone`: what the cycle leaves undone, counted fresh from the notebook and the run folder's step files, written
to <rf>/left-undone.txt and read by /wiki-report (task #240, lesson #9; Mark, 2026-11-16: after a run, anything left
undone is named, with the count and why). Exit 2, nothing written, for a `--today` that is not a calendar date
(YYYY-MM-DD), a run folder or notebook that is not there. It changes no entry and writes no `*-scope.txt`. Run it from
the project whose notebook is counted: a working folder whose .claude/wiki-config.json names another notebook is
not a supported case (this session's bucket is read from that file, so it would label the wrong bucket as this
session's). This is Part 1, the disk-state counts, and most of Part 2: the entries not linted, without claims and not
synthesised, the lint findings, the semantic findings and the earlier runs' semantic findings; the sources are not
counted yet.

  File shape. Line 1 is a header the script writes: `Left undone: <N> queue(s)`, N the number of queue lines below
  it, `Mode: not checked` lines and `, not checked` lines included (each is something not known to be empty), or
  `Left undone (disk-state queues): none` when there are none. A `--report-only` file has a second line, `Disk-state
  queues are counted now; event lines are from the last run (<id>)`, which is not a queue line and not counted in N;
  the last run is the newest earlier run folder that holds a `<id>-run-cycle-report.md` and whose scratchpad mode is
  not report-only (`none: no earlier run with a report` when there is none). Then the queue lines,
  `- <queue>: <N> — <reason and way out>`. The file always ends with the interim line `Not counted yet: leftovers of
  steps that ran (...)`; it is not a queue line and does not count toward N (it goes when Part 2 is built; until then
  `Left undone: nothing` is never written).

  Mode and modifiers, read from the run folder's scratchpad.md, never typed. Tokens are split on whitespace, commas,
  semicolons and parentheses, with backticks, quotes and trailing punctuation stripped. The mode is the first token
  inside the parentheses of the `**Cycle**: <id> (<mode>[, <modifiers>])` line, one of nine names, each accepted with
  or without its leading dashes: quick, full, ingest-only, discover-only, prompt-for-urls, lint-only, report-only,
  refresh-only, claims-only. With no mode there, the first token of the `- Mode:` line is tried; two lines that name
  different modes, no mode on either, or no scratchpad leave the mode unknown. `lint-only` with `--semantic` among the
  tokens of either line is `lint-only-semantic`. Modifiers are the tokens `--no-confirm-discovery`, `--lint-all`,
  `--direct` and `--since` found anywhere on either line. The command prints `mode <mode|unknown>; modifiers <list>`.

  Cross-check, STEP_MODES (which modes run each step; the five modes of the cycle skill's mode table are held equal to
  it by the drift test in tests/scripts/test_cycle_scope.py, the other four by this table alone) against STEP_FILES
  (the named step results: refresh.json, lint-semantic.json, claims.json, synthesis.json, update.json, triage.json,
  discover.json, lint-mechanical.json; never a `*.json` glob, as models.json, cost.json and email-review.json are not
  steps). A step result in the run folder that the mode does not run, or an unknown mode, keeps every count and
  changes only the mode-dependent reasons: `<count>, not checked (cannot read the mode from scratchpad.md)` or
  `<count>, not checked (the mode in scratchpad.md is <mode> but the run folder holds <file>)`, and adds one queue
  line, `Mode: not checked (<same text>); steps that left no file are not known`, so the header never reads nothing
  while the mode is not known.

  Third state, for every step a mode runs: the mode does not run it, "does not run" wording; its result is present and
  `completed`, the "ran" wording; absent, `<count>, not checked (<step> left no <file>)`; present and not completed,
  `<count>, not checked (the <step> ended <status>)` (`unreadable` for a file that does not parse). The count is
  printed before `not checked`.

  Review dates. Entries are wiki/ pages without `_`-prefixed files, README.md, sessions/ and the top-level tasks/
  cards. Past: `review_after` is a YYYY-MM-DD calendar date strictly before `--today` (default the local date), quotes
  stripped. No review_after: the key is absent. Not a date: present and not a calendar date.

  | Queue (step it depends on)    | Mode does not run it                                                   | Ran (completed)                                                                      |
  | Past review_after (refresh)   | this mode does not run refresh; /wiki-cycle --refresh-only lists them  | refresh ran; this count is from the dates now (refreshing them is your call: /wiki-refresh) |
  | No review_after               | refresh cannot see an entry with no review_after; add the date (the lint lists them under Missing lifecycle fields) | same in every mode |
  | review_after not a date       | refresh cannot read it; correct the date (the lint lists them under Dates not in ISO form) | same in every mode |
  | Tickets in _inbox/pending/    | this mode does not triage; /wiki-cycle --ingest-only gives each an owner | not triaged: arrived after triage, or triage did not complete |
  | Tickets in this session's bucket | this mode does not ingest; /wiki-cycle --ingest-only                 | left in the bucket after ingest: dropped, failed, deferred or not reached |
  | Staged entries                | staged before this run, or held by the checker; /wiki-promote          | same |
  | Discovery checklists          | still in _inbox/discovered/ (discovery files a processed one in _inbox/done/); whether it was reviewed is not recorded | same |
  | Not semantically linted (semantic lint) | this mode does not run the semantic lint; /wiki-cycle --lint-only --semantic or --full | the semantic lint ran and did not read them (lint-semantic.md); an entry re-reviewed later on the lint's own day is not counted |
  | No claims, or revised since the index (claims) | this mode does not run claims; /wiki-cycle --claims-only or --full | the claims step ran and did not read them (claims.md); an entry re-reviewed later on that day is not counted |
  | Not yet synthesised (synthesis) | this mode does not synthesise (only modes that ingest do); /wiki-cycle --ingest-only | synthesis ran and did not read them (synthesis.md) |

  Tickets, staged entries, checklists. The tickets lines are facts about the folders and never read a step's result
  (triage.json, update.json): the mode alone picks the wording, and an unknown mode or a mismatch reads `<count>, not
  checked (<problem>)`. Pending: every .md in _inbox/pending/ that is not `_`-prefixed or README (wiki-triage.py's
  `_tickets`; the dequeue counts a file with no `source:` there too). Buckets: wiki-triage.py's `intake_tickets`, the
  .md files of the configured buckets (`buckets()`; an intake README whose frontmatter does not parse reads as the
  one-bucket default, `main` read by this session) that are not `_`-prefixed, README or triage-log.md and carry a
  `source:` line. One line per bucket this session reads (`me()`), `- Tickets in this session's bucket <folder>: N`;
  one line for every other reader's bucket, `mark`'s included, `- Other readers' buckets, still to process: <folder> N,
  <folder> N`, with no owner, reason or items and no folder with 0. Staged entries (_inbox/proposed/) only when the
  run's promote-setting.txt says `confirm_before_promote: false` (with true Needs you has them, so no line); with no
  promote-setting.txt: `Staged entries: <N>, not checked (no promote-setting.txt: whether they wait for you is not
  known)`. Checklists: each .md in _inbox/discovered/ that is not `_`-prefixed or README. A queue with 0 adds no line.

  Entries not linted, without claims, not synthesised: one covered-set rule for the three, whether the step ran in this
  run or an earlier one. The cut-off C is the timestamp of the newest completed result of the step in any run folder,
  this one included (newest_step; claims: C is when claims-index.json was last written), and S is the scope file
  (semantic-scope.txt, claims-scope.txt, synthesis-scope.txt) in that folder, the exact list the step read. What a
  step run now would read, from the scope functions the semantic, claims and synthesis commands share (semantic_scope,
  claims_scope, synthesis_scope), is the scope-now at C; of it only live wiki entries count (task cards, sessions and
  staged pages never), and an entry is covered, so not counted, when its full path is in S, or its stem is that of an S
  line under _inbox/proposed/ (a staged page read before it was promoted; the stem bridges only when exactly one live
  entry has that name), and its last_reviewed day is not after C's day: a step compares days, so an entry re-reviewed
  later on C's own day is covered (a stated under-count), one re-reviewed on a later day is counted whatever S says.
  With no completed result anywhere, nothing is covered and scope-now is every entry (synthesis: every research entry
  when a best-practices page exists, else none). The wording by mode and this run's own result: the mode does not run
  the step, the table; the mode runs it and its result is absent `<count>, not checked (<step> left no <file>)`
  (semantic lint only: with the newest completed lint under 24 hours old, `the semantic lint was skipped: one ran
  within 24 hours (<id>)`), unreadable `(<file> unreadable)`, not completed `(<step> ended <status>; what it covered is
  unknown)`, completed the ran wording. The newest completed result with no scope file reads `<count>, not checked (no
  <scope file> in the run folder)` in every mode (what it covered is not known, nothing is subtracted). A synthesis of
  status awaiting_approval adds no line (Needs you has it). The command reads the scope files and writes none.

  Lint findings (lint-mechanical.json). One line per `summary` key above 0 except files_scanned (not a finding),
  standalone (pages that declare themselves standalone by design) and backlink_blocks_out_of_step (Needs you has it):
  `- Lint <key, underscores as spaces>: <N> — <reason>`, the reason `no fix step in this mode` or, in --full,
  `still present after the cycle Step 5 fixes (not approved, declined, or no fix step covers this kind)`; "awaiting your
  approval" is used for semantic findings only. A partial lint (`status: partial`, the `not_checked` list it writes at
  exit 3) gives one `- Lint: not checked — <reason>` line per entry of `not_checked` and no counts, whatever its summary
  says (unchecked parts report 0); a lint that ended any other status gives `- Lint findings: not checked (the
  mechanical lint ended <status>)`, one that does not parse `(lint-mechanical.json unreadable)`, a completed one with no
  summary object `(lint-mechanical.json has no usable summary)`. No result in a mode that lints: `- Lint findings: not
  checked (the mechanical lint left no lint-mechanical.json)`; in a mode that does not: `- Lint findings: not checked (no
  lint ran this cycle; /wiki-cycle --lint-only)`; with an unknown mode or a contradiction and no result the Mode line
  says it, so this line is left out. An unknown mode or a contradiction with a result keeps the counts and reads `<N>,
  not checked (<problem>)`. Staleness guard: whenever lint-fixes.txt exists in the run folder (cycle Step 5 writes it
  with `lint-fixes`, zero ids included), a lint stamped earlier than its `at:` (or when either stamp cannot be read, so
  the order cannot be proved) gives the one line `- Lint findings: not checked (the lint predates cycle Step 5; re-run
  the mechanical lint)` and no counts, because mechanical-only fixes leave no id; a lint stamped later is counted.

  Semantic findings (lint-semantic.json, this run's, in the modes that run it: full, lint-only-semantic). The count is
  the length of the flat `findings` list, usable only when it is a list whose length equals `summary.findings`;
  otherwise `- Semantic findings: not checked (lint-semantic.json has no usable findings list)`, never read as zero. A
  non-empty top-level `not_checked` adds `- Semantic lint, parts not checked: <N> — <the items>`. Awaiting is the
  count minus the distinct ids of `applied` and `declined` in lint-fixes.txt that lie inside 1..N (never negative); with no
  fixes record it is the whole count. Nothing prints for 0 findings or awaiting 0. The line is `- Semantic findings: <N>
  — awaiting your approval; the findings are in lint-semantic.md (run <id>); no later cycle step shows them again`; in
  lint-only-semantic `<N> — no fix step in this mode; the findings are in lint-semantic.md and no later cycle step
  shows them again`; in --full with no lint-fixes.txt `<N>, not checked (the fix step left no lint-fixes.txt: applied and
  declined were not recorded)`, with one that has no applied and declined lines `(lint-fixes.txt unreadable)`; a lint of
  status partial `<N>, not checked (the semantic lint ended partial)`, N the figure the complete line would print; an
  unknown mode or a contradiction `<N>, not checked (<problem>)`. A mode that runs the lint and left no result:
  `- Semantic findings: not checked (the semantic lint left no lint-semantic.json)` (also when a lint ran within 24
  hours and the step was skipped: the earlier run's findings below carry the numbers); an unparseable file
  `(lint-semantic.json unreadable)`. Needs you copies this N, never a count of the model's own.

  Semantic findings from earlier runs (every run folder's lint-semantic.json and the lint-fixes.txt beside it, this
  run's own included; only completed lints are read, so an older lint of status partial with unresolved findings is not
  read and prints nothing). The newest completed lint, when it is not this run's own, gets `- Semantic findings from
  <id>: <N> — awaiting your approval; the findings are in lint-semantic.md (run <id>); no later cycle step shows them
  again; fixes made by hand since are not seen` (N counted from that lint's own fixes record), `<N>, not checked (that
  run recorded no applied or declined findings)` when it has none, or `not checked (lint-semantic.json has no usable
  findings list)`. In every run, whatever it ran, each completed lint older than the newest (this run's own never
  counted twice) with unresolved findings gets `- Semantic findings from <id>: <N>, superseded by a newer lint; no
  longer shown in full; the findings are in lint-semantic.md (run <id>); no later cycle step shows them again`, also when
  the newest lint found nothing; older lints with a non-empty findings list and no fixes record collapse into one
  line, `- <N> earlier lints recorded no applied or declined findings; no longer shown in full`, and a lint with an
  empty or unusable list prints and counts nothing. These lines are counted in the header and are never added to an
  awaiting figure.

`lint-fixes`: the fixes record of cycle Step 5, the one fact no step file holds (which semantic findings the user
applied or declined). `--show` prints the findings of <rf>/lint-semantic.json from its `findings` list, one per line,
`<id>. [<category>] <file> — <first 100 characters of detail>` (a newline in the detail becomes a space), the id the
1-based position in that list, so the model copies ids the script printed and never counts; it writes nothing, and with
no lint-semantic.json says so and exits 0. `--applied <ids> --declined <ids>` (comma-separated, either may be left out)
writes <rf>/lint-fixes.txt, `applied: <ids>`, `declined: <ids>` and `at: <now_stamp()>`, the ids sorted and each once.
With no ids at all it writes two empty lists, which is how cycle Step 5 records a run whose lint was skipped. Exit 2 and
nothing written for an id that is not a whole number, outside 1..N (N is 0 when there is no usable lint-semantic.json),
in both lists, or for `--show` together with ids, and for a run folder that is not there.

Entries are wiki/**/*.md except `_`-prefixed machine files, README.md and sessions/.
(2026-09-24, task #42: C1 and C3; the 2026-09-23 cycle's findings 10 and 11.)
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _entry_checks import split_frontmatter  # noqa: E402
from _atomic_io import atomic_write_text  # noqa: E402
from _wiki_config import (  # noqa: E402
    confirm_before_promote, in_sessions, in_tasks, load_config, now_stamp, today_label, topic_root)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHECKER_CONFIG = Path.home() / ".claude" / "agents" / "wiki-checker-config.json"
DEFAULT_MIN_MINUTES = 15
DEFAULT_MIN_RAW_KB = 60.0  # task #202: a long PDF or a whole repo carries the same omission risk as a long talk
DEFAULT_SAMPLE_EVERY = 1  # task #236: every entry; 43 of 44 checked entries needed fixes
# raw types that are a transcript with a length (task #105: cycle 2026-10-11-01's 30-minute Whisper
# transcript was missed, when only YouTube's counted)
TRANSCRIPT_TYPES = {"youtube-transcript", "media-transcript"}


def entries(nb: Path) -> list[str]:
    wiki = nb / "wiki"
    out = []
    for p in wiki.rglob("*.md"):
        rel = p.relative_to(wiki).as_posix()
        if p.name.startswith("_") or p.name.lower() == "readme.md" or rel.startswith("sessions/"):
            continue
        out.append(f"wiki/{rel}")
    return sorted(out)


def staged(nb: Path) -> list[str]:
    prop = nb / "_inbox" / "proposed"
    return sorted(f"_inbox/proposed/{p.name}" for p in prop.glob("*.md")
                  if not p.name.startswith("_") and p.name.lower() != "readme.md") if prop.is_dir() else []


def _parse_time(s: str) -> datetime | None:
    try:
        t = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
        return t if t.tzinfo else t.astimezone()
    except ValueError:
        return None


def _git_top(nb: Path) -> tuple[Path | None, str]:
    try:
        top = subprocess.run(["git", "-C", str(nb), "rev-parse", "--show-toplevel"], capture_output=True,
                             text=True, encoding="utf-8", check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, ""
    repo = Path(top)
    prefix = nb.resolve().relative_to(repo.resolve()).as_posix()
    return repo, ("" if prefix == "." else prefix + "/")


def added_since(nb: Path, cutoff: datetime, among: list[str]) -> list[str]:
    """Entries created after `cutoff`: git's added files (plus untracked ones), else frontmatter `date`."""
    repo, prefix = _git_top(nb)
    if repo:
        log = subprocess.run(["git", "-C", str(repo), "log", f"--since={cutoff.isoformat()}", "--diff-filter=A",
                              "--name-only", "--pretty=format:", "--", f"{prefix}wiki"],
                             capture_output=True, text=True, encoding="utf-8").stdout
        new = subprocess.run(["git", "-C", str(repo), "ls-files", "--others", "--exclude-standard", "--",
                              f"{prefix}wiki"], capture_output=True, text=True, encoding="utf-8").stdout
        got = {l.strip() for l in (log.splitlines() + new.splitlines()) if l.strip()}
        got = {g[len(prefix):] if g.startswith(prefix) else g for g in got}
        return [e for e in among if e in got]
    day = cutoff.date().isoformat()
    return [e for e in among if _front((nb / e).read_text(encoding="utf-8", errors="replace")).get("date", "") > day]


def revised_since(nb: Path, cutoff: datetime, among: list[str]) -> list[str]:
    day = cutoff.date().isoformat()
    return [e for e in among
            if _front((nb / e).read_text(encoding="utf-8", errors="replace")).get("last_reviewed", "")[:10] >= day]


def _index_written(nb: Path, idx_path: Path) -> datetime:
    """When the claims index was last written: its last commit, else its file time."""
    repo, _prefix = _git_top(nb)
    if repo:
        out = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%cI", "--", str(idx_path)],
                             capture_output=True, text=True, encoding="utf-8").stdout.strip()
        if out and not subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--", str(idx_path)],
                                      capture_output=True, text=True, encoding="utf-8").stdout.strip():
            return _parse_time(out)
    return datetime.fromtimestamp(idx_path.stat().st_mtime).astimezone()


def step_results(nb: Path, json_name: str, status: str | None = None,
                 skip: Path | None = None) -> list[tuple[datetime, Path]]:
    """(timestamp, run folder) of every run folder holding `json_name`, newest first by the file's own `timestamp`
    (never by folder name); a file that does not parse or has no timestamp is left out. `status` keeps only results
    of that status (None: any), `skip` leaves out one run folder. The one walk over the run folders' step results:
    newest_step (so last_semantic and last_synthesis) and the left-undone counter read through it."""
    found = []
    for p in (nb / "_inbox" / "reports").glob(f"*/*/{json_name}"):
        if skip is not None and p.parent.resolve() == skip.resolve():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        t = _parse_time(d.get("timestamp", "")) if status is None or d.get("status") == status else None
        if t:
            found.append((t, p.parent))
    return sorted(found, key=lambda f: f[0], reverse=True)


def newest_step(nb: Path, json_name: str, status: str | None = None,
                skip: Path | None = None) -> tuple[datetime, Path] | None:
    """(timestamp, run folder) of the newest of step_results, or None."""
    found = step_results(nb, json_name, status, skip)
    return found[0] if found else None


def last_semantic(nb: Path, run_folder: Path) -> datetime | None:
    """The timestamp of the newest earlier run's lint-semantic.json."""
    found = newest_step(nb, "lint-semantic.json", skip=run_folder)
    return found[0] if found else None


def write_scope(run_folder: Path, name: str, paths: list[str], why: str) -> Path:
    """One path per line under a `#` header line, so an empty scope is never a zero-byte
    file (the stray-file sweeps delete those; the first suite run flagged one, 2026-09-24)."""
    run_folder.mkdir(parents=True, exist_ok=True)
    out = run_folder / name
    atomic_write_text(out, f"# {name}: {len(paths)} ({why})\n" + "".join(p + "\n" for p in paths))
    return out


def semantic_scope(nb: Path, cutoff: datetime | None, forced: bool = False) -> tuple[list[str], list[str], str]:
    """(the entries the semantic lint reads, every entry, why) for a lint whose cut-off is `cutoff` (None: no earlier
    lint, so every entry; `forced` is the user's --all, which only changes the why). Staged entries are the caller's."""
    all_entries = entries(nb)
    if cutoff is None:
        return all_entries, all_entries, ("--all" if forced else "no earlier semantic lint: every entry")
    picked = sorted(set(added_since(nb, cutoff, all_entries)) | set(revised_since(nb, cutoff, all_entries)))
    return picked, all_entries, f"added or revised since {cutoff.isoformat()} + staged"


def cmd_semantic(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    picked, all_entries, why = semantic_scope(nb, None if args.all else last_semantic(nb, rf), args.all)
    st = staged(nb)
    scope = picked + st
    out = write_scope(rf, "semantic-scope.txt", scope, why)
    print(f"semantic scope: {len(scope)} of {len(all_entries)} entries + {len(st)} staged ({why}) -> {out}")
    return 0


def claims_scope(nb: Path, forced: bool = False) -> tuple[list[str], list[str], str, datetime | None]:
    """(the entries the claims step reads, every entry, why, when the index was written) : the entries no claim in
    the claims index comes from plus those revised since it was written; every entry with no index or `forced`
    (the user's --all). The index time is None when the index was not read."""
    all_entries = entries(nb)
    idx_path = nb / "_inbox" / "claims-index.json"
    if forced or not idx_path.is_file():
        return all_entries, all_entries, ("--all" if forced else "no claims index: every entry"), None
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    known = {Path(str(c.get("source_entry", ""))).name for c in idx.get("claims", [])}
    missing = [e for e in all_entries if Path(e).name not in known]
    written = _index_written(nb, idx_path)
    revised = revised_since(nb, written, all_entries)
    why = (f"{len(missing)} with no claims in the index, {len(set(revised) - set(missing))} revised since "
           f"the index was written ({written.date().isoformat()})")
    return sorted(set(missing) | set(revised)), all_entries, why, written


def cmd_claims(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    scope, all_entries, why, _written = claims_scope(nb, args.all)
    st = staged(nb)
    out = write_scope(rf, "claims-scope.txt", scope, why)
    print(f"claims scope: {len(scope)} of {len(all_entries)} entries ({why}); {len(st)} staged left out -> {out}")
    return 0


def last_synthesis(nb: Path, run_folder: Path) -> datetime | None:
    """The timestamp of the newest earlier synthesis the user answered (status completed). One nobody
    could answer (awaiting_approval) leaves the cut-off where it was, so its entries come round again."""
    found = newest_step(nb, "synthesis.json", "completed", run_folder)
    return found[0] if found else None


def synthesis_scope(nb: Path, cutoff: datetime | None, forced: bool = False) -> tuple[list[str], list[str], str]:
    """(the research entries synthesis reads, every live research entry, why) for a synthesis whose cut-off is
    `cutoff` (None: no earlier answered synthesis, so every research entry; `forced` is the user's --all, which only
    changes the why). Empty when there is no best-practices page to synthesise into."""
    canon = [p for p in (nb / "wiki" / "project" / "best-practices").glob("*.md")
             if not p.name.startswith("_") and p.name.lower() != "readme.md"]
    research = [e for e in entries(nb) if e.startswith("wiki/research/")
                and not _front((nb / e).read_text(encoding="utf-8", errors="replace")).get("superseded_by")]
    if not canon:
        return [], research, "no best-practices pages: nothing to synthesise into"
    if cutoff is None:
        return research, research, ("--all" if forced else "no earlier synthesis: every research entry")
    return added_since(nb, cutoff, research), research, f"research entries added since {cutoff.isoformat()}"


def cmd_synthesis(nb: Path, args) -> int:
    """Research entries promoted since the last answered synthesis (task #176, 2026-10-19): synthesis runs in
    every cycle that ingests, so it covers what the user promoted between cycles, never only this run's batch."""
    rf = Path(args.run_folder)
    scope, research, why = synthesis_scope(nb, None if args.all else last_synthesis(nb, rf), args.all)
    out = write_scope(rf, "synthesis-scope.txt", scope, why)
    print(f"synthesis scope: {len(scope)} of {len(research)} research entries ({why}) -> {out}")
    return 0


def _front(text: str) -> dict:
    """The frontmatter, by the one shared parser (task #177, 2026-10-22)."""
    return split_frontmatter(text, flat=True)[0]


def min_minutes(args) -> float:
    if args.min_minutes is not None:
        return args.min_minutes
    try:
        return float(json.loads(CHECKER_CONFIG.read_text(encoding="utf-8")).get("min_transcript_minutes",
                                                                                  DEFAULT_MIN_MINUTES))
    except (OSError, json.JSONDecodeError, ValueError):
        return DEFAULT_MIN_MINUTES


def checker_setting(args, flag: str, key: str, default):
    """A checker scope setting: the flag, else wiki-checker-config.json's key, else the default."""
    if getattr(args, flag) is not None:
        return getattr(args, flag)
    try:
        return type(default)(json.loads(CHECKER_CONFIG.read_text(encoding="utf-8")).get(key, default))
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return default


def spot_checked(entry: str, every: int) -> bool:
    """1 in `every` entries, by a hash of the entry's name: random across entries, the same on every run."""
    return every > 0 and int(hashlib.sha1(Path(entry).stem.encode("utf-8")).hexdigest(), 16) % every == 0


def cmd_checker(nb: Path, args) -> int:
    """Staged entries the checker reads: a transcript of --min-minutes+, a raw of --min-raw-kb+ (a long PDF, a whole
    repo), and 1 in --sample-every of the rest as a spot check (task #202, Mark 2026-10-23). An entry with no raw
    is never in scope."""
    rf, floor = Path(args.run_folder), min_minutes(args)
    min_kb = checker_setting(args, "min_raw_kb", "min_raw_kb", DEFAULT_MIN_RAW_KB)
    every = checker_setting(args, "sample_every", "sample_every", DEFAULT_SAMPLE_EVERY)
    picked, skipped = [], []
    for e in staged(nb):
        rp = _front((nb / e).read_text(encoding="utf-8", errors="replace")).get("raw_path", "")
        raw = nb / rp if rp and not rp.startswith("(") else None
        if not (raw and raw.is_file()):
            skipped.append(e)
            continue
        meta = _front(raw.read_text(encoding="utf-8", errors="replace"))
        secs = meta.get("duration_seconds", "")
        minutes = float(secs) / 60 if secs.replace(".", "", 1).isdigit() else None
        kb = raw.stat().st_size / 1024
        mins = f"{minutes:.0f}" if minutes is not None else "-"
        if meta.get("type") in TRANSCRIPT_TYPES and minutes is not None and minutes >= floor:
            picked.append((f"{e}\t{rp}\t{mins}", f"transcript of {mins} minutes"))
        elif min_kb > 0 and kb >= min_kb:
            picked.append((f"{e}\t{rp}\t{mins}", f"raw of {kb:.0f} KB"))
        elif spot_checked(e, every):
            picked.append((f"{e}\t{rp}\t{mins}", f"spot check, 1 in {every}"))
        else:
            skipped.append(e)
    rules = [f"transcripts of {floor:g}+ minutes"] + ([f"raws of {min_kb:g}+ KB"] if min_kb > 0 else []) \
        + ([f"1 in {every} of the rest"] if every > 0 else [])
    out = write_scope(rf, "checker-scope.txt", [line for line, _ in picked],
                      f"staged entries: {', '.join(rules)}; entry, raw, minutes ('-' when not a transcript)")
    print(f"checker scope: {len(picked)} of {len(picked) + len(skipped)} staged entries ({', '.join(rules)}) -> {out}")
    for line, why in picked:
        print("  " + line.replace("\t", "  ") + f"  ({why})")
    return 0


def cmd_checker_log(nb: Path, args) -> int:
    rep = json.loads(Path(args.report).read_text(encoding="utf-8"))
    kinds = ("unsupported_claims", "skipped_sections", "misquotes", "vague_passages")  # the last since 2026-10-15
    row = {"ts": now_stamp(), "cycle": Path(args.run_folder).name, "entry": args.entry,
           "source_minutes": rep.get("source_minutes"), "model": rep.get("model"),
           **{k: len(rep.get(k) or []) for k in kinds},
           "verdict": rep.get("verdict") or ("pass" if not any(rep.get(k) for k in kinds) else "fix")}
    log = nb / "_inbox" / "reports" / "checker-log.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"logged: {row['entry']} {row['verdict']} "
          + ", ".join(f"{k.replace('_', ' ')} {row[k]}" for k in kinds) + f" -> {log}")
    # The verdict also goes into the staged entry's sidecar, where wiki-promote.py holds an uncorrected fix
    # (task #178 row 8: the hold rested only on the orchestrator leaving the slug out of the promote call).
    sc = _sidecar(nb, args.entry)
    if sc is None:
        print(f"warning: {args.entry} is not staged (no sidecar in _inbox/proposed/): the verdict is only logged")
        return 0
    meta = json.loads(sc.read_text(encoding="utf-8"))
    meta["checker"] = {"verdict": row["verdict"], "report": args.report, "corrected": False, "logged_at": row["ts"]}
    atomic_write_text(sc, json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    if row["verdict"] == "fix":
        print(f"held from promotion until corrected: fix the entry from the report, then "
              f"`wiki-cycle-scope.py checker-corrected --entry {args.entry}`")
    return 0


def _sidecar(nb: Path, slug: str) -> Path | None:
    f = nb / "_inbox" / "proposed" / f"{slug}.proposed_metadata.json"
    return f if f.is_file() else None


def cmd_checker_corrected(nb: Path, args) -> int:
    """The staged entry was corrected from its checker report: wiki-promote.py may promote it now."""
    sc = _sidecar(nb, args.entry)
    if sc is None:
        print(f"error: {args.entry} is not staged (no {args.entry}.proposed_metadata.json in _inbox/proposed/)",
              file=sys.stderr)
        return 2
    meta = json.loads(sc.read_text(encoding="utf-8"))
    chk = meta.get("checker")
    if not isinstance(chk, dict):
        print(f"error: {args.entry} has no checker verdict to correct (run checker-log first)", file=sys.stderr)
        return 2
    chk.update({"corrected": True, "corrected_at": now_stamp()})
    atomic_write_text(sc, json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(f"corrected: {args.entry} (checker verdict {chk.get('verdict')}) may be promoted -> {sc}")
    return 0


HOME_CLAUDE = Path.home() / ".claude"
# what each role falls back to when its setting file cannot be read
FALLBACK = {"ingest_workers": "sonnet", "checker": "opus",
            "semantic_lint": "sonnet", "lint_fixes": "sonnet", "synthesis": "sonnet",
            "large_raw_kb": 10, "large_raw_model": "opus"}


def _settings(path: str) -> tuple[dict | None, str]:
    p = Path(path).expanduser()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return (data, "") if isinstance(data, dict) else (None, f"{p}: not a JSON object")
    except FileNotFoundError:
        return None, f"{p}: missing"
    except (OSError, json.JSONDecodeError) as e:
        return None, f"{p}: unreadable ({e})"


def _large_raw(ing: dict | None) -> tuple[float, str]:
    """The size (KB) from which a raw is written on large_raw_model (task #239)."""
    ing = ing or {}
    try:
        kb = float(ing.get("large_raw_kb", FALLBACK["large_raw_kb"]))
    except (TypeError, ValueError):
        kb = float(FALLBACK["large_raw_kb"])
    return kb, ing.get("large_raw_model") or FALLBACK["large_raw_model"]


def cmd_writer(nb: Path, args) -> int:
    ing, err = _settings(args.ingester)
    if err:
        print(f"warning: {err}; using the fallback ({FALLBACK['ingest_workers']}, "
              f"{FALLBACK['large_raw_model']} from {FALLBACK['large_raw_kb']} KB)")
    kb, big = _large_raw(ing)
    small = (ing or {}).get("model_default") or FALLBACK["ingest_workers"]
    rc = 0
    for r in args.raws:
        p = Path(r)
        if not p.is_absolute() and not p.is_file():
            p = nb / r
        if not p.is_file():
            print(f"missing: {r}", file=sys.stderr)
            rc = 1
            continue
        size_kb = p.stat().st_size / 1024
        print(f"{r}\t{size_kb:.0f}\t{big if size_kb >= kb else small}")
    return rc


def cmd_models(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    roles, problems = {}, []
    ing, err = _settings(args.ingester)
    if err:
        problems.append(err)
    kb, big = _large_raw(ing)
    roles["ingest_workers"] = {"model": (ing or {}).get("model_default") or FALLBACK["ingest_workers"],
                               "ask_each_run": bool((ing or {}).get("confirm_model_each_run", False)),
                               "large_raw_kb": kb, "large_raw_model": big,
                               "from": str(Path(args.ingester).expanduser()) if ing else "fallback"}
    chk, err = _settings(args.checker)
    if err:
        problems.append(err)
    roles["checker"] = {"model": (chk or {}).get("model_default") or FALLBACK["checker"],
                        "from": str(Path(args.checker).expanduser()) if chk else "fallback"}
    hlp, err = _settings(args.helpers)
    if err:
        problems.append(err)
    for role in ("semantic_lint", "lint_fixes", "synthesis"):
        roles[role] = {"model": (hlp or {}).get(role) or FALLBACK[role],
                       "from": str(Path(args.helpers).expanduser()) if hlp and hlp.get(role) else "fallback"}
    rf.mkdir(parents=True, exist_ok=True)
    out = rf / "models.json"
    atomic_write_text(out, json.dumps({"timestamp": now_stamp(), "roles": roles, "problems": problems}, indent=2) + "\n")
    w = roles["ingest_workers"]
    print(f"ingest workers: {w['model']}"
          + (" (ask the user each run when the session can ask; this is the default)" if w["ask_each_run"] else "")
          + f"; {w['large_raw_model']} for a raw of {w['large_raw_kb']:g} KB or more")
    for role in ("checker", "semantic_lint", "lint_fixes", "synthesis"):
        print(f"{role.replace('_', ' ')}: {roles[role]['model']}")
    for p in problems:
        print(f"warning: {p}; its roles use the fallback above")
    print(f"-> {out}")
    return 0


def cmd_promote(nb: Path, args) -> int:
    wait, where = confirm_before_promote(args.topic_name)
    rf = Path(args.run_folder)
    rf.mkdir(parents=True, exist_ok=True)
    # plain text, not JSON: the run folder's *.json files are step results under the cycle contract
    out = rf / "promote-setting.txt"
    atomic_write_text(out, f"confirm_before_promote: {str(wait).lower()}\nfrom: {where}\nat: {now_stamp()}\n")
    if wait:
        print(f"promote: wait for the user (confirm_before_promote: true, from {where}): nothing is promoted; "
              f"new entries stay staged for /wiki-promote -> {out}")
    else:
        print(f"promote: automatic (confirm_before_promote: false, from {where}): every new entry the checker "
              f"did not hold is promoted at Step 5.5 -> {out}")
    return 0


CYCLE_ID = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}$")
DECISIONS_HEADING = "## Decisions log"
DECISIONS_LOG = re.compile(rf"^{re.escape(DECISIONS_HEADING)}$", re.M)


def unfinished_runs(nb: Path, run_folder: Path) -> list[tuple[str, str]]:
    """(cycle_id, why) for each earlier run folder with no `<id>-run-cycle-report.md`, unless its scratchpad says
    `interrupted`, oldest first. A run folder is `_inbox/reports/<date>/<YYYY-MM-DD>-<NN>/` with <date> the id's own
    date (a cycle always files it there; one moved by hand is skipped, as the close-out cannot find it); `checker/`
    and the like are not (task #240, lesson #10: a run that died before its report was never looked at again)."""
    out = []
    for d in sorted((nb / "_inbox" / "reports").glob("*/*")):
        if not d.is_dir() or not CYCLE_ID.match(d.name) or d.resolve() == run_folder.resolve():
            continue
        if d != run_folder_of(nb, d.name):    # filed under another date: the close-out would refuse it
            continue
        if (d / f"{d.name}-run-cycle-report.md").is_file():
            continue
        pad = d / "scratchpad.md"
        if not pad.is_file():
            out.append((d.name, "no scratchpad"))
            continue
        m = re.search(r"^\*\*Status\*\*:\s*(\S+)", pad.read_text(encoding="utf-8", errors="replace"), re.M)
        status = m.group(1) if m else "unknown"
        if status != "interrupted":
            out.append((d.name, f"scratchpad says {status}"))
    return out


def run_folder_of(nb: Path, cycle_id: str) -> Path:
    """Where a run's folder is: `_inbox/reports/<date>/<cycle_id>/` (the date is the id's first ten characters)."""
    return nb / "_inbox" / "reports" / cycle_id[:10] / cycle_id


def mark_interrupted(nb: Path, cycle_id: str, reason: str) -> None:
    """Close one run folder by its scratchpad: Status becomes `interrupted` and the reason joins the Decisions log."""
    pad = run_folder_of(nb, cycle_id) / "scratchpad.md"
    text = pad.read_text(encoding="utf-8") if pad.is_file() else (
        f"# Cycle Run — {cycle_id[:10]}\n\n**Status**: interrupted\n\n{DECISIONS_HEADING}\n")
    text, n = re.subn(r"^(\*\*Status\*\*:).*$", r"\1 interrupted", text, count=1, flags=re.M)
    if not n:
        title, _, rest = text.partition("\n")
        text = f"{title}\n\n**Status**: interrupted\n{rest}"
    line = f"- {now_stamp()} — marked interrupted: {reason}\n"
    if not DECISIONS_LOG.search(text):
        text = text.rstrip("\n") + f"\n\n{DECISIONS_HEADING}\n"
    log = DECISIONS_LOG.search(text)
    after = re.search(r"^## ", text[log.end():], re.M)
    end = log.end() + after.start() if after else len(text)
    atomic_write_text(pad, text[:end].rstrip("\n") + "\n" + line + ("\n" + text[end:] if after else ""))


def cmd_unfinished(nb: Path, args) -> int:
    if args.mark_interrupted:
        cid = args.mark_interrupted
        if not CYCLE_ID.match(cid) or not run_folder_of(nb, cid).is_dir():
            print(f"error: no run folder {cid!r} under _inbox/reports/ (a cycle id is <YYYY-MM-DD>-<NN>)", file=sys.stderr)
            return 2
        mark_interrupted(nb, cid, args.reason)
        print(f"unfinished: {cid} marked interrupted: {args.reason}")
        return 0
    rf = Path(args.run_folder)
    found = unfinished_runs(nb, rf)
    why = f"{len(found)} earlier run folder(s) with no run-cycle report"
    write_scope(rf, "unfinished-runs.txt", [f"{cid}\t{w}" for cid, w in found], why)
    for cid, w in found:
        resume = (f"resume: /wiki-cycle {args.topic_name} --resume {cid}; or "
                  if (run_folder_of(nb, cid) / "scratchpad.md").is_file() else "")
        print(f'unfinished: {cid} ({w}) — {resume}close it: '
              f'wiki-cycle-scope.py --topic {args.topic_name} unfinished --mark-interrupted {cid} --reason "<why>"')
    if not found:
        print("unfinished: none")
    return 0


SESSION_COST_DIR = HOME_CLAUDE / "session-cost"


def _norm(p: str) -> str:
    return str(Path(p)).replace("\\", "/").rstrip("/").lower()


def _session_cost(sid):
    folder = Path(os.environ.get("WIKI_SESSION_COST_DIR") or SESSION_COST_DIR)
    if sid:
        f = folder / f"{sid}.json"
        if not f.is_file():
            return None, f"no session-cost file for session {sid} in {folder}"
        try:
            return json.loads(f.read_text(encoding="utf-8")), ""
        except (OSError, ValueError) as e:
            return None, f"{f}: unreadable ({e})"
    here, best = _norm(os.getcwd()), None
    for f in (folder.glob("*.json") if folder.is_dir() else []):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if _norm(d.get("cwd") or "") == here and isinstance(d.get("total_cost_usd"), (int, float)):
            if best is None or str(d.get("updated", "")) > str(best.get("updated", "")):
                best = d
    if best is None:
        return None, (f"no session-cost file for {os.getcwd()} in {folder} "
                      "(the status line writes one; see the wiki-cycle usage page)")
    return best, ""


def _write_json(path: Path, rec: dict) -> None:
    atomic_write_text(path, json.dumps(rec, indent=2) + "\n")


def cmd_session_cost(nb: Path, args) -> int:
    """The session's running total, for /wrap-up's report (task #182 row 34): no run folder, writes nothing."""
    cur, err = _session_cost(args.session_id)
    if cur is None:
        print(f"cost: NOT checked: {err}")
        return 3
    print(f"cost: ${cur['total_cost_usd']:.2f} so far this session (session {cur['session_id']}; Claude Code's "
          "API-price estimate, subagents included; on a subscription plan a comparison figure, not a bill)")
    return 0


def cmd_cost(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    rf.mkdir(parents=True, exist_ok=True)
    out = rf / "cost.json"
    rec = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {}
    sid = args.session_id or (rec.get("session_id") if args.mark == "end" else None)
    cur, err = _session_cost(sid)
    if cur is None:
        rec.update({"step": "cost", "status": "not_checked", "not_checked": [err]})
        _write_json(out, rec)
        print(f"cost: NOT checked: {err}")
        return 3
    if args.mark == "start":
        _write_json(out, {"step": "cost", "status": "in_progress", "session_id": cur["session_id"],
                          "start_usd": cur["total_cost_usd"], "start_at": now_stamp()})
        print(f"cost: start ${cur['total_cost_usd']:.2f} (session {cur['session_id']})")
        return 0
    if "start_usd" not in rec:
        rec.update({"step": "cost", "status": "not_checked", "not_checked": ["no start mark in cost.json"]})
        _write_json(out, rec)
        print("cost: NOT checked: no start mark (run `cost --mark start` at Step 0)")
        return 3
    delta = round(cur["total_cost_usd"] - rec["start_usd"], 2)
    rec.update({"status": "completed", "end_usd": cur["total_cost_usd"], "end_at": now_stamp(), "run_usd": delta})
    _write_json(out, rec)
    atomic_write_text(rf / "cost.md", (
        f"# Cost\n\nThis run: ${delta:.2f} (session {rec['session_id']}: ${rec['start_usd']:.2f} at the start, "
        f"${cur['total_cost_usd']:.2f} at the end; Claude Code's API-price estimate, subagents included; "
        "on a subscription plan a comparison figure, not a bill)\n"))
    print(f"cost: this run ${delta:.2f}")
    return 0


MODES = ("quick", "full", "ingest-only", "discover-only", "prompt-for-urls", "lint-only", "report-only",
         "refresh-only", "claims-only")
# which modes run each step (the cycle skill's mode table, and its prose for the modes the table leaves out)
STEP_MODES = {
    "discover": ("quick", "full", "discover-only"),
    "triage": ("quick", "full", "ingest-only"),
    "ingest": ("quick", "full", "ingest-only", "prompt-for-urls"),
    "lint": ("quick", "full", "ingest-only", "prompt-for-urls", "lint-only", "lint-only-semantic"),
    "semantic": ("full", "lint-only-semantic"),
    "fix": ("full",),
    "claims": ("full", "claims-only"),
    "refresh": ("full", "refresh-only"),
    "synthesis": ("quick", "full", "ingest-only", "prompt-for-urls"),
}
# the step results the cross-check looks for (never a `*.json` glob: models.json, cost.json and email-review.json
# are not steps); the fix step leaves no JSON
STEP_FILES = {"discover": "discover.json", "triage": "triage.json", "ingest": "update.json",
              "lint": "lint-mechanical.json", "semantic": "lint-semantic.json", "claims": "claims.json",
              "refresh": "refresh.json", "synthesis": "synthesis.json"}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INTERIM_LAST = ("Not counted yet: leftovers of steps that ran (lint findings, dropped sources, "
                "entries not linted, claimed or synthesised)")


MODIFIERS = ("--no-confirm-discovery", "--lint-all", "--direct", "--since")


def _tokens(text: str) -> list[str]:
    """Split on whitespace, commas, semicolons and parentheses; backticks, quotes and trailing punctuation off."""
    return [t for t in (x.strip("`'\"….:!?") for x in re.split(r"[\s,;()]+", text)) if t]


def _mode_name(tokens: list[str]) -> str | None:
    """The first token as one of the nine mode names, with or without its leading dashes."""
    first = tokens[0] if tokens else ""
    name = first[2:] if first.startswith("--") else first
    return name if name in MODES else None


def cycle_mode(run_folder: Path) -> tuple[str | None, list[str]]:
    """(mode, modifiers) from the run's scratchpad. The mode is the first token inside the parentheses of the
    `**Cycle**` line, else the first token of the `- Mode:` line; two lines that name different modes read as no
    mode (None). The modifiers are the `--` tokens of either line that are one of MODIFIERS."""
    pad = run_folder / "scratchpad.md"
    if not pad.is_file():
        return None, []
    text = pad.read_text(encoding="utf-8", errors="replace")
    cycle_m = re.search(r"^\*\*Cycle\*\*:(.*)$", text, re.M)
    mode_m = re.search(r"^- Mode:(.*)$", text, re.M)
    cycle_text, mode_text = cycle_m.group(1) if cycle_m else "", mode_m.group(1) if mode_m else ""
    named = {m for m in (_mode_name(_tokens(cycle_text.partition("(")[2])[:1]), _mode_name(_tokens(mode_text)[:1]))
             if m}
    tokens = _tokens(cycle_text) + _tokens(mode_text)
    modifiers = sorted({t for t in tokens if t in MODIFIERS})
    if len(named) != 1:
        return None, modifiers
    mode = named.pop()
    return ("lint-only-semantic" if mode == "lint-only" and "--semantic" in tokens else mode), modifiers


def _iso_date(value: str) -> date | None:
    if not ISO_DATE.match(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def review_date_counts(nb: Path, today: date) -> tuple[list[str], list[str], list[str]]:
    """The entries (wiki/ pages, tasks/ and sessions/ left out) whose `review_after` is strictly before `today`,
    absent, and present but not a calendar date."""
    past, none, bad = [], [], []
    for e in entries(nb):
        rel = Path(e).relative_to("wiki")
        if in_tasks(rel) or in_sessions(rel):
            continue
        front = _front((nb / e).read_text(encoding="utf-8", errors="replace"))
        if "review_after" not in front:
            none.append(e)
            continue
        due = _iso_date(front["review_after"])
        if due is None:
            bad.append(e)
        elif due < today:
            past.append(e)
    return past, none, bad


def mode_problem(mode: str | None, rf: Path) -> str | None:
    """Why the mode cannot be trusted: not readable from the scratchpad, or the run folder holds the result of a
    step the mode does not run."""
    if mode is None:
        return "cannot read the mode from scratchpad.md"
    for step, name in STEP_FILES.items():
        if (rf / name).is_file() and mode not in STEP_MODES[step]:
            return f"the mode in scratchpad.md is {mode} but the run folder holds {name}"
    return None


def step_status(rf: Path, name: str) -> str | None:
    """None when the step left no file, else its `status` (`unreadable` when the file does not parse)."""
    f = rf / name
    if not f.is_file():
        return None
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "unreadable"
    return str(data.get("status") or "unknown") if isinstance(data, dict) else "unreadable"


def _triage():
    """wiki-triage.py's module (its file name has a dash), loaded as _install_tooling.py loads its helpers."""
    spec = importlib.util.spec_from_file_location("_wiki_triage_pkg", Path(__file__).resolve().parent / "wiki-triage.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def bucket_ticket_lines(nb: Path, mode: str | None, problem: str | None) -> list[str]:
    """This session's bucket tickets (one line per bucket it reads) and, once, the other readers' (the `mark`
    bucket included); a folder with no ticket adds nothing."""
    tri = _triage()
    waiting = len(tri._tickets(nb))
    if not waiting:
        pending = []
    elif problem:
        pending = [f"- Tickets in _inbox/pending/: {waiting}, not checked ({problem})"]
    elif mode not in STEP_MODES["triage"]:
        pending = [f"- Tickets in _inbox/pending/: {waiting} — this mode does not triage; "
                   "/wiki-cycle --ingest-only gives each an owner"]
    else:
        pending = [f"- Tickets in _inbox/pending/: {waiting} — not triaged: arrived after triage, "
                   "or triage did not complete"]
    me, lines, others = tri.me(), [], []
    try:
        bs = tri.buckets(nb)[0]
    except Exception:  # noqa: BLE001 - frontmatter that does not parse: the one-bucket default, as no README gives
        bs = [{"folder": "main", "reader": me}]
    counts: dict[str, int] = {}
    for folder, _path, _source, _front_ in tri.intake_tickets(nb, bs):
        counts[folder] = counts.get(folder, 0) + 1
    for b in bs:
        folder = str(b.get("folder"))
        n = counts.get(folder, 0)
        if not n:
            continue
        if b.get("reader") != me:
            others.append(f"{folder} {n}")
        elif problem:
            lines.append(f"- Tickets in this session's bucket {folder}: {n}, not checked ({problem})")
        elif mode not in STEP_MODES["ingest"]:
            lines.append(f"- Tickets in this session's bucket {folder}: {n} — this mode does not ingest; "
                         "/wiki-cycle --ingest-only")
        else:
            lines.append(f"- Tickets in this session's bucket {folder}: {n} — left in the bucket after ingest: "
                         "dropped, failed, deferred or not reached")
    return pending + lines + ([f"- Other readers' buckets, still to process: {', '.join(others)}"] if others else [])


def staged_lines(nb: Path, rf: Path) -> list[str]:
    """The staged entries, only when the run's promote-setting.txt says `confirm_before_promote: false` (with true,
    Needs you has them); no promote-setting.txt, or none that says true or false, keeps the count and says not checked."""
    n = len(staged(nb))
    if not n:
        return []
    f = rf / "promote-setting.txt"
    m = re.search(r"^confirm_before_promote:\s*(true|false)\s*$", f.read_text(encoding="utf-8", errors="replace"),
                  re.M) if f.is_file() else None
    if m is None:
        why = "no promote-setting.txt" if not f.is_file() else "no confirm_before_promote in promote-setting.txt"
        return [f"- Staged entries: {n}, not checked ({why}: whether they wait for you is not known)"]
    if m.group(1) == "true":
        return []
    return [f"- Staged entries: {n} — staged before this run, or held by the checker; /wiki-promote"]


def checklist_lines(nb: Path) -> list[str]:
    """Discovery checklists still in _inbox/discovered/ (discovery files a processed one in _inbox/done/)."""
    disc = nb / "_inbox" / "discovered"
    n = len([p for p in disc.glob("*.md") if not p.name.startswith(("_", "README"))]) if disc.is_dir() else 0
    return [f"- Discovery checklists: {n} — still in _inbox/discovered/ (discovery files a processed one in "
            "_inbox/done/); whether it was reviewed is not recorded"] if n else []


def read_scope_file(folder: Path, name: str) -> set[str] | None:
    """The paths a step's scope file lists (the `#` header left out); None when the folder has no such file."""
    f = folder / name
    if not f.is_file():
        return None
    return {l.strip() for l in f.read_text(encoding="utf-8", errors="replace").splitlines()
            if l.strip() and not l.startswith("#")}


def uncovered(nb: Path, scope: list[str], read: set[str], cutoff: datetime | None) -> list[str]:
    """The covered-set rule: the live entries of `scope` (what a step run now would read) that the step run at
    `cutoff` did not cover. Covered is: the full path is in `read` (its scope file), or the stem is that of a staged
    page `read` lists under _inbox/proposed/ (a page read before it was promoted) and exactly one live entry has that
    name; and its last_reviewed day is not after the cut-off's day. Task cards and sessions are never counted."""
    live = [e for e in entries(nb)
            if not (in_tasks(Path(e).relative_to("wiki")) or in_sessions(Path(e).relative_to("wiki")))]
    names: dict[str, int] = {}
    for e in live:
        names[Path(e).stem] = names.get(Path(e).stem, 0) + 1
    staged_stems = {Path(l).stem for l in read if l.startswith("_inbox/proposed/")}
    day = cutoff.date().isoformat() if cutoff else None
    left = []
    for e in sorted(set(scope) & set(live)):
        seen = e in read or (Path(e).stem in staged_stems and names[Path(e).stem] == 1)
        if seen and (day is None or _front((nb / e).read_text(encoding="utf-8", errors="replace"))
                     .get("last_reviewed", "")[:10] <= day):
            continue
        left.append(e)
    return left


# label, result file, scope file, the step's name in a reason, the mode-table key, "mode does not run it", "ran"
ENTRY_BACKLOGS = (
    ("Not semantically linted", "lint-semantic.json", "semantic-scope.txt", "the semantic lint", "semantic",
     "this mode does not run the semantic lint; /wiki-cycle --lint-only --semantic or --full",
     "the semantic lint ran and did not read them (lint-semantic.md); an entry re-reviewed later on the lint's own "
     "day is not counted"),
    ("No claims, or revised since the index", "claims.json", "claims-scope.txt", "the claims step", "claims",
     "this mode does not run claims; /wiki-cycle --claims-only or --full",
     "the claims step ran and did not read them (claims.md); an entry re-reviewed later on that day is not counted"),
    ("Not yet synthesised", "synthesis.json", "synthesis-scope.txt", "synthesis", "synthesis",
     "this mode does not synthesise (only modes that ingest do); /wiki-cycle --ingest-only",
     "synthesis ran and did not read them (synthesis.md)"),
)


def entry_backlog_lines(nb: Path, rf: Path, mode: str | None, problem: str | None) -> list[str]:
    """Entries not semantically linted, without claims, not synthesised, by the covered-set rule: the cut-off is the
    newest completed result of the step in any run folder (this one included) and the entries it read are that
    folder's scope file, so a step run in this run and one run earlier read alike. The wording follows the mode
    and this run's own result (the third state); a synthesis awaiting approval adds no line (Needs you has it)."""
    lines = []
    for label, result, scope_file, name, key, off, ran in ENTRY_BACKLOGS:
        found = newest_step(nb, result, "completed")
        cutoff = found[0] if found else None
        if key == "semantic":
            scope = semantic_scope(nb, cutoff)[0]
        elif key == "claims":
            scope, _all, _why, cutoff = claims_scope(nb)
        else:
            scope = synthesis_scope(nb, cutoff)[0]
        read = read_scope_file(found[1], scope_file) if found else set()
        own = step_status(rf, result)
        if key == "synthesis" and own == "awaiting_approval":
            continue
        n = len(uncovered(nb, scope, read or set(), cutoff))
        if not n:
            continue
        if problem:
            why = f", not checked ({problem})"
        elif read is None:
            why = f", not checked (no {scope_file} in the run folder)"
        elif mode not in STEP_MODES[key]:
            why = f" — {off}"
        elif own is None and key == "semantic" and found and datetime.now().astimezone() - cutoff < timedelta(hours=24):
            why = f" — the semantic lint was skipped: one ran within 24 hours ({found[1].name})"
        elif own is None:
            why = f", not checked ({name} left no {result})"
        elif own == "unreadable":
            why = f", not checked ({result} unreadable)"
        elif own != "completed":
            why = f", not checked ({name} ended {own}; what it covered is unknown)"
        else:
            why = f" — {ran}"
        lines.append(f"- {label}: {n}{why}")
    return lines


def last_run_id(nb: Path, rf: Path) -> str | None:
    """The newest earlier run folder with a `<id>-run-cycle-report.md` whose scratchpad mode is not report-only."""
    found = []
    for d in (nb / "_inbox" / "reports").glob("*/*"):
        if (d.is_dir() and CYCLE_ID.match(d.name) and d.name < rf.name
                and (d / f"{d.name}-run-cycle-report.md").is_file() and cycle_mode(d)[0] != "report-only"):
            found.append(d.name)
    return max(found, default=None)


def step_data(folder: Path, name: str) -> dict:
    """The JSON object of a step result, {} when it is absent, does not parse or is not an object."""
    try:
        data = json.loads((folder / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def usable_findings(data: dict) -> list | None:
    """The `findings` list of a semantic lint result (agentic-design's 2026-10-30 file: one flat list, its length in
    `summary.findings`), or None when it cannot be trusted: no list, not a list, or a length that disagrees."""
    findings, summary = data.get("findings"), data.get("summary")
    if isinstance(findings, list) and isinstance(summary, dict) and summary.get("findings") == len(findings):
        return findings
    return None


def fixes_record(folder: Path) -> dict | None:
    """The run folder's lint-fixes.txt (`lint-fixes` writes it at cycle Step 5): None when absent, else `ok` (both id
    lines read), `answered` (the distinct ids of applied and declined) and `at` (when it was written, tz-aware or None)."""
    f = folder / "lint-fixes.txt"
    if not f.is_file():
        return None
    text = f.read_text(encoding="utf-8", errors="replace")

    def ids(key: str) -> set[int] | None:
        m = re.search(rf"^{key}:[ \t]*(.*)$", text, re.M)
        return parse_ids(m.group(1)) if m else None
    applied, declined, at = ids("applied"), ids("declined"), re.search(r"^at:[ \t]*(\S+)[ \t]*$", text, re.M)
    return {"ok": applied is not None and declined is not None, "answered": (applied or set()) | (declined or set()),
            "at": _parse_time(at.group(1)) if at else None}


def awaiting(n: int, record: dict | None) -> int:
    """Findings still unanswered: all `n` with no readable fixes record, else n minus the distinct answered ids that lie
    inside 1..n (never negative)."""
    if record is None or not record["ok"]:
        return n
    return n - len({i for i in record["answered"] if 1 <= i <= n})


LINT_NOT_FINDINGS = ("files_scanned", "standalone", "backlink_blocks_out_of_step")
LINT_GUARD = "- Lint findings: not checked (the lint predates cycle Step 5; re-run the mechanical lint)"
LINT_STILL = "still present after the cycle Step 5 fixes (not approved, declined, or no fix step covers this kind)"


def lint_lines(rf: Path, mode: str | None, problem: str | None) -> list[str]:
    """The mechanical lint's findings, one line per kind above 0, or why they cannot be counted (the third state, the
    partial lint, the staleness guard against lint-fixes.txt)."""
    name = "lint-mechanical.json"
    status = step_status(rf, name)
    if status is None:
        if problem:
            return []
        if mode not in STEP_MODES["lint"]:
            return ["- Lint findings: not checked (no lint ran this cycle; /wiki-cycle --lint-only)"]
        return [f"- Lint findings: not checked (the mechanical lint left no {name})"]
    if status == "unreadable":
        return [f"- Lint findings: not checked ({name} unreadable)"]
    data = step_data(rf, name)
    reasons = [str(r) for r in data.get("not_checked") or []] if isinstance(data.get("not_checked"), list) else []
    if status == "partial" and reasons:
        return [f"- Lint: not checked — {r}" for r in reasons]
    if status != "completed":
        return [f"- Lint findings: not checked (the mechanical lint ended {status})"]
    summary = data.get("summary")
    if not isinstance(summary, dict):
        return [f"- Lint findings: not checked ({name} has no usable summary)"]
    record = fixes_record(rf)
    if record is not None:
        lint_at = _parse_time(data.get("timestamp", ""))
        if not (lint_at and record["at"] and lint_at >= record["at"]):
            return [LINT_GUARD]
    out = []
    for key, count in summary.items():
        if key in LINT_NOT_FINDINGS or isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            continue
        if problem:
            why = f", not checked ({problem})"
        elif mode not in STEP_MODES["fix"]:
            why = " — no fix step in this mode"
        elif record is None:
            why = ", not checked (the fix step left no lint-fixes.txt)"
        else:
            why = f" — {LINT_STILL}"
        out.append(f"- Lint {key.replace('_', ' ')}: {count}{why}")
    return out


def where_findings(run_id: str) -> str:
    return f"the findings are in lint-semantic.md (run {run_id}); no later cycle step shows them again"


def semantic_lines(rf: Path, mode: str | None, problem: str | None) -> list[str]:
    """This run's semantic findings: what is awaiting the user's approval by the fixes record, or why that cannot be
    said, and the parts the lint did not check."""
    name = "lint-semantic.json"
    status = step_status(rf, name)
    if status is None:
        if problem or mode not in STEP_MODES["semantic"]:
            return []
        return [f"- Semantic findings: not checked (the semantic lint left no {name})"]
    if status == "unreadable":
        return [f"- Semantic findings: not checked ({name} unreadable)"]
    data = step_data(rf, name)
    findings, out = usable_findings(data), []
    if findings is None:
        out.append(f"- Semantic findings: not checked ({name} has no usable findings list)")
    else:
        record = fixes_record(rf)
        left = awaiting(len(findings), record)
        if left:
            if problem:
                why = f", not checked ({problem})"
            elif status != "completed":
                why = f", not checked (the semantic lint ended {status})"
            elif mode not in STEP_MODES["fix"]:
                why = " — no fix step in this mode; the findings are in lint-semantic.md and no later cycle step shows them again"
            elif record is None:
                why = ", not checked (the fix step left no lint-fixes.txt: applied and declined were not recorded)"
            elif not record["ok"]:
                why = ", not checked (lint-fixes.txt unreadable)"
            else:
                why = f" — awaiting your approval; {where_findings(rf.name)}"
            out.append(f"- Semantic findings: {left}{why}")
    parts = data.get("not_checked")
    if isinstance(parts, list) and parts:
        out.append(f"- Semantic lint, parts not checked: {len(parts)} — {'; '.join(str(p) for p in parts)}")
    return out


def lint_backlog(folder: Path) -> tuple[str, int]:
    """What an earlier run's semantic lint left: ('unusable', 0) for a findings list that cannot be trusted, ('empty', 0)
    for one with no finding, ('unrecorded', N) with no readable fixes record, else ('open', unresolved) or ('answered', 0)."""
    findings = usable_findings(step_data(folder, "lint-semantic.json"))
    if findings is None:
        return "unusable", 0
    if not findings:
        return "empty", 0
    record = fixes_record(folder)
    if record is None or not record["ok"]:
        return "unrecorded", len(findings)
    left = awaiting(len(findings), record)
    return ("open", left) if left else ("answered", 0)


def earlier_semantic_lines(nb: Path, rf: Path) -> list[str]:
    """Semantic findings of earlier runs, in every run: the newest completed lint when it is not this run's own, and a
    line for each older completed lint that still has unresolved findings (so a newer lint never silences them). Only
    completed lints are read; this run's own lint is semantic_lines' and is never counted twice."""
    lints = [f for _t, f in step_results(nb, "lint-semantic.json", "completed")]
    mine, out, unrecorded = rf.resolve(), [], 0
    for i, folder in enumerate(lints):
        if folder.resolve() == mine:
            continue
        kind, n = lint_backlog(folder)
        if i == 0:
            if kind == "open":
                out.append(f"- Semantic findings from {folder.name}: {n} — awaiting your approval; "
                           f"{where_findings(folder.name)}; fixes made by hand since are not seen")
            elif kind == "unrecorded":
                out.append(f"- Semantic findings from {folder.name}: {n}, not checked "
                           "(that run recorded no applied or declined findings)")
            elif kind == "unusable":
                out.append(f"- Semantic findings from {folder.name}: not checked (lint-semantic.json has no usable findings list)")
        elif kind == "open":
            out.append(f"- Semantic findings from {folder.name}: {n}, superseded by a newer lint; no longer shown in "
                       f"full; {where_findings(folder.name)}")
        elif kind == "unrecorded":
            unrecorded += 1
    if unrecorded:
        out.append(f"- {unrecorded} earlier lints recorded no applied or declined findings; no longer shown in full")
    return out


def parse_ids(text: str | None) -> set[int] | None:
    """A comma-separated list of whole numbers as a set (empty or None: the empty set); None when a part is not one."""
    ids = set()
    for part in (text or "").split(","):
        part = part.strip()
        if not part:
            continue
        if not re.fullmatch(r"[0-9]+", part):
            return None
        ids.add(int(part))
    return ids


def cmd_lint_fixes(nb: Path, args) -> int:
    """Cycle Step 5's record of which semantic findings the user applied or declined (see the docstring)."""
    rf = Path(args.run_folder)
    if not rf.is_dir():
        print(f"error: no run folder at {rf}", file=sys.stderr)
        return 2
    present = (rf / "lint-semantic.json").is_file()
    findings = usable_findings(step_data(rf, "lint-semantic.json")) if present else []
    if args.show:
        if args.applied is not None or args.declined is not None:
            print("error: --show only prints; give --applied and --declined in a second call", file=sys.stderr)
            return 2
        if not present:
            print("no lint-semantic.json in the run folder: nothing to show")
            return 0
        if findings is None:
            print("error: lint-semantic.json has no usable findings list", file=sys.stderr)
            return 2
        for i, f in enumerate(findings, 1):
            detail = " ".join(str(f.get("detail", "")).split())[:100]
            print(f"{i}. [{f.get('category', '')}] {f.get('file', '')} — {detail}")
        return 0
    applied, declined = parse_ids(args.applied), parse_ids(args.declined)
    if applied is None or declined is None:
        print("error: --applied and --declined take whole numbers separated by commas", file=sys.stderr)
        return 2
    n = len(findings or [])
    outside = sorted(i for i in applied | declined if not 1 <= i <= n)
    if outside:
        print(f"error: finding id(s) {', '.join(map(str, outside))} are not in 1..{n} (the ids --show printed)", file=sys.stderr)
        return 2
    if applied & declined:
        print(f"error: id(s) {', '.join(map(str, sorted(applied & declined)))} are in both --applied and --declined", file=sys.stderr)
        return 2
    fmt = lambda s: ",".join(map(str, sorted(s)))  # noqa: E731
    out = rf / "lint-fixes.txt"
    atomic_write_text(out, f"applied: {fmt(applied)}".rstrip() + f"\ndeclined: {fmt(declined)}".rstrip()
                      + f"\nat: {now_stamp()}\n")
    print(f"lint-fixes: applied {fmt(applied) or 'none'}; declined {fmt(declined) or 'none'} -> {out}")
    return 0


def cmd_left_undone(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    today = _iso_date(args.today or today_label())
    if today is None:
        print(f"error: --today must be a YYYY-MM-DD date, not {args.today!r}", file=sys.stderr)
        return 2
    if not rf.is_dir():
        print(f"error: no run folder at {rf}", file=sys.stderr)
        return 2
    mode, modifiers = cycle_mode(rf)
    problem = mode_problem(mode, rf)
    past, none, bad = review_date_counts(nb, today)
    queues = []
    if past:
        refresh = step_status(rf, STEP_FILES["refresh"])
        if problem:
            queues.append(f"- Past review_after: {len(past)}, not checked ({problem})")
        elif mode not in STEP_MODES["refresh"]:
            queues.append(f"- Past review_after: {len(past)} — this mode does not run refresh; "
                          "/wiki-cycle --refresh-only lists them")
        elif refresh is None:
            queues.append(f"- Past review_after: {len(past)}, not checked (refresh left no refresh.json)")
        elif refresh != "completed":
            queues.append(f"- Past review_after: {len(past)}, not checked (the refresh ended {refresh})")
        else:
            queues.append(f"- Past review_after: {len(past)} — refresh ran; this count is from the dates now "
                          "(refreshing them is your call: /wiki-refresh)")
    if none:
        queues.append(f"- No review_after: {len(none)} — refresh cannot see an entry with no review_after; "
                      "add the date (the lint lists them under Missing lifecycle fields)")
    if bad:
        queues.append(f"- review_after not a date: {len(bad)} — refresh cannot read it; correct the date "
                      "(the lint lists them under Dates not in ISO form)")
    queues += entry_backlog_lines(nb, rf, mode, problem)
    queues += lint_lines(rf, mode, problem)
    queues += semantic_lines(rf, mode, problem)
    queues += earlier_semantic_lines(nb, rf)
    queues += bucket_ticket_lines(nb, mode, problem)
    queues += staged_lines(nb, rf)
    queues += checklist_lines(nb)
    if problem:
        queues.append(f"- Mode: not checked ({problem}); steps that left no file are not known")
    head = f"Left undone: {len(queues)} queue(s)" if queues else "Left undone (disk-state queues): none"
    second = ([f"Disk-state queues are counted now; event lines are from the last run "
               f"({last_run_id(nb, rf) or 'none: no earlier run with a report'})"] if mode == "report-only" else [])
    out = rf / "left-undone.txt"
    atomic_write_text(out, "\n".join([head, *second, *queues, INTERIM_LAST]) + "\n")
    print(f"left-undone: {head}; mode {mode or 'unknown'}; modifiers {','.join(modifiers) or 'none'} -> {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1].strip())
    ap.add_argument("--topic", default=None, help="notebook (default: this project's)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("semantic", "claims", "synthesis"):
        s = sub.add_parser(name)
        s.add_argument("--run-folder", required=True)
        s.add_argument("--all", action="store_true", help="every entry (the user's --lint-all)")
    c = sub.add_parser("checker")
    c.add_argument("--run-folder", required=True)
    c.add_argument("--min-minutes", type=float, default=None)
    c.add_argument("--min-raw-kb", type=float, default=None, help="a raw this big is checked too (0: off)")
    c.add_argument("--sample-every", type=int, default=None, help="spot-check 1 in N other entries (0: off)")
    lg = sub.add_parser("checker-log")
    lg.add_argument("--run-folder", required=True)
    lg.add_argument("--entry", required=True)
    lg.add_argument("--report", required=True)
    cc = sub.add_parser("checker-corrected")
    cc.add_argument("--entry", required=True)
    m = sub.add_parser("models")
    m.add_argument("--run-folder", required=True)
    m.add_argument("--ingester", default=str(HOME_CLAUDE / "agents" / "wiki-ingester-config.json"))
    m.add_argument("--checker", default=str(HOME_CLAUDE / "agents" / "wiki-checker-config.json"))
    m.add_argument("--helpers", default=str(HOME_CLAUDE / "skills" / "wiki-cycle" / "helper-models.json"))
    co = sub.add_parser("cost")
    co.add_argument("--run-folder", required=True)
    co.add_argument("--mark", choices=("start", "end"), required=True)
    co.add_argument("--session-id", default=None)
    sco = sub.add_parser("session-cost")
    sco.add_argument("--session-id", default=None)
    pr = sub.add_parser("promote")
    pr.add_argument("--run-folder", required=True)
    un = sub.add_parser("unfinished")
    un.add_argument("--run-folder", default=None)
    un.add_argument("--mark-interrupted", metavar="CYCLE_ID", default=None)
    un.add_argument("--reason", default=None)
    wr = sub.add_parser("writer")
    wr.add_argument("raws", nargs="+", help="raw files (absolute, or relative to the notebook)")
    wr.add_argument("--ingester", default=str(HOME_CLAUDE / "agents" / "wiki-ingester-config.json"))
    ld = sub.add_parser("left-undone")
    ld.add_argument("--run-folder", required=True)
    ld.add_argument("--today", default=None, help="YYYY-MM-DD, for tests (default: the local date)")
    lf = sub.add_parser("lint-fixes")
    lf.add_argument("--run-folder", required=True)
    lf.add_argument("--show", action="store_true", help="print the findings with their ids; write nothing")
    lf.add_argument("--applied", default=None, help="ids of the findings applied, comma-separated")
    lf.add_argument("--declined", default=None, help="ids of the findings declined, comma-separated")
    args = ap.parse_args()
    if args.cmd == "unfinished" and bool(args.run_folder) == bool(args.mark_interrupted):
        un.error("give --run-folder (to list) or --mark-interrupted (to close one), not both and not neither")
    if args.cmd == "unfinished" and args.mark_interrupted and not args.reason:
        un.error("--mark-interrupted needs --reason \"<why>\"")
    topic = args.topic or (load_config() or {}).get("notebook")
    if not topic:
        print("error: no notebook: pass --topic or run inside a wiki project", file=sys.stderr)
        return 2
    args.topic_name = topic
    nb = Path(topic_root(topic))
    if not (nb / "wiki").is_dir():
        print(f"error: no wiki at {nb}", file=sys.stderr)
        return 2
    return {"semantic": cmd_semantic, "claims": cmd_claims, "synthesis": cmd_synthesis, "checker": cmd_checker,
            "checker-log": cmd_checker_log, "checker-corrected": cmd_checker_corrected, "models": cmd_models,
            "cost": cmd_cost, "session-cost": cmd_session_cost,
            "promote": cmd_promote, "unfinished": cmd_unfinished, "writer": cmd_writer,
            "left-undone": cmd_left_undone, "lint-fixes": cmd_lint_fixes}[args.cmd](nb, args)


if __name__ == "__main__":
    sys.exit(main())
