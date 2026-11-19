"""
What a /wiki-cycle run left behind, and the record of cycle Step 5's fixes: the `unfinished`, `left-undone` and
`lint-fixes` commands of wiki-cycle-scope.py, which imports them from here and dispatches them (its docstring has
their usage lines). This docstring is the one source of their rules, file shapes and wording tables.

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
to <rf>/left-undone.txt and read by /wiki-report (task #240, lesson #9; Mark's rule: after a run, anything left
undone is named, with the count and why). Exit 2, nothing written, for a `--today` that is not a calendar date
(YYYY-MM-DD), a run folder or notebook that is not there. It changes no entry and writes no `*-scope.txt`. Run it from
the project whose notebook is counted: a working folder whose .claude/wiki-config.json names another notebook is
not a supported case (this session's bucket is read from that file, so it would label the wrong bucket as this
session's). It counts the disk-state queues (review dates, tickets, staged entries, checklists), the entries not
linted, without claims and not synthesised, the lint findings, the semantic findings and the earlier runs' semantic
findings, the dropped, failed and deferred sources and the tier-4 deferrals, and, in a `--report-only` run, copies the
last run's event lines.

  File shape. Line 1 is a header the script writes: `Left undone: <N> queue(s)`, N the number of queue lines below
  it, `Mode: not checked` lines and `, not checked` lines included (each is something not known to be empty), or
  `Left undone: nothing` when there are none. A `--report-only` file has a second line, `Disk-state queues are counted
  now; event lines are from the last run (<id>)`, which is not a queue line and not counted in N; the last run is the
  newest earlier run folder that holds a `<id>-run-cycle-report.md` and whose scratchpad mode is not report-only
  (`none: no earlier run with a report` when there is none). Then the queue lines, `- <queue>: <N> — <reason and way
  out>`.

  Event lines and the last run. The lint findings, this run's semantic findings, the sources and the tier-4 deferrals
  are the run's event lines. A run that is not `--report-only` writes them to <rf>/left-undone-events.txt (a `#` header
  line, then one line each; an absent file means a run before the install). A `--report-only` run writes no such file,
  and instead of computing those lines (it ran no step) copies the last run's, each ending `(from <id>)`; with no
  last run they read `- Events of the last run: not checked (no earlier run with a report)`, with a last run that left
  no events file `(that run left no left-undone-events.txt)`. Everything else is counted fresh in every run, the
  earlier runs' semantic findings too (standing backlogs read from the lint files, never copied or written to the
  events file). A report-only run is never the last run, so nothing nests.

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
  stripped. No review_after: the key is absent. Not a date: present and not a calendar date. The one count printed at
  0: in a mode that runs refresh (and with the mode readable and not contradicted), a refresh.json that is absent or
  not completed gives `- Past review_after: 0, not checked (refresh left no refresh.json)` (or `the refresh ended
  <status>`), because the dates alone do not show that refresh ran; it is what keeps such a run from reading nothing.

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
  this one included (newest_step; claims: C is when claims-index.json was last written (with no index: the newest
  completed claims.json's timestamp)), and S is the scope file
  (semantic-scope.txt, claims-scope.txt, synthesis-scope.txt) in that folder, the exact list the step read. What a
  step run now would read, from the scope functions the semantic, claims and synthesis commands share (semantic_scope,
  claims_scope, synthesis_scope), is the scope-now at C; of it only live wiki entries count (task cards, sessions and
  staged pages never), and an entry is covered, so not counted, when its full path is in S, or its stem is that of an S
  line under _inbox/proposed/ (a staged page read before it was promoted; the stem bridges only when exactly one live
  entry has that name), and its last_reviewed day is not after C's day: a step compares days, so an entry re-reviewed
  later on C's own day is covered (a stated under-count), one re-reviewed on a later day is counted whatever S says.
  With no completed result anywhere, nothing is covered and scope-now is every entry (synthesis: every research entry
  when a best-practices page exists, else none; claims: scope-now is the entries no index claim comes from plus those
  revised since the index was written, every entry only when there is no index). The wording by mode and this run's own result: the mode does not run
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
  line, `- <N> earlier lints recorded no applied or declined findings; no longer shown in full`, a lint with an empty
  list prints and counts nothing, and one whose findings list cannot be trusted (any earlier completed lint, the newest
  or not) reads `- Semantic findings from <id>: not checked (lint-semantic.json has no usable findings list)`. These
  lines are counted in the header and are never added to an awaiting figure.

  Sources (update.json, discover.json; event lines). One line per item, `- Source <url, else slug, else id, else item>:
  <skipped|deferred|failed> — <reason as the file holds it, whitespace collapsed>` (`(no reason recorded)` when it has
  none; an error's reason is its `message`): from update.json every skipped, deferred and errors item, from
  discover.json every skipped item except one whose reason says "already covered" (nothing was queued for it; an
  ingest skip of that kind stays, its ticket is still in the bucket), and never a source whose ticket in a configured
  bucket carries `retry:` or `save_as_pdf:` (Needs you names those; compared as the exact `source:` string, so a link in
  another form is listed twice, harmlessly). A step a mode runs that left no file: `- Sources: not checked (ingest left
  no update.json)` or `(discovery left no discover.json)`; a mode that does not run it, an unknown mode or a
  contradiction (the Mode line says it) adds none; a file that cannot be read `- Sources: not checked (<file>
  unreadable)`, also when the list it holds is not a list. Discovery's deferred and errors are not read.

  Tier-4 deferrals (event lines), only when this run folder holds discover.json (it ran discovery) and `--no-confirm-discovery`
  is among the modifiers; an unattended run that did not write the flag into its scratchpad produces no line and no
  not-checked line (the stated silent miss). The checklist is `<run date>-discovery.md` (the first ten characters of the cycle id)
  in _inbox/discovered/, else _inbox/done/. A candidate line is `- [ ] **N.** [Title](url) — tier N — **Why**: …`; an
  unticked one saying `tier 4` right after the link whose link the notebook does not hold (the check behind
  `wiki-feeds.py known`, loaded once for all links, no subprocess) is `- Source <url>: deferred — tier 4: needs your
  review (--no-confirm-discovery)`. A held link (known reports it held, in the wiki, staged, pending, done or a bucket;
  known reads only the first 30 lines of a ticket, so a ticket with its source: later reads new and may add a line) is
  not a deferral. No checklist in either folder: `- Tier-4 sources: not checked (no discovery checklist for <date>)`.

`lint-fixes`: the fixes record of cycle Step 5, the one fact no step file holds (which semantic findings the user
applied or declined). `--show` prints the findings of <rf>/lint-semantic.json from its `findings` list, one per line,
`<id>. [<category>] <file> — <first 100 characters of detail>` (a newline in the detail becomes a space), the id the
1-based position in that list, so the model copies ids the script printed and never counts; it writes nothing, and with
no lint-semantic.json says so and exits 0. `--applied <ids> --declined <ids>` (comma-separated, either may be left out)
writes <rf>/lint-fixes.txt, `applied: <ids>`, `declined: <ids>` and `at: <now_stamp()>`, the ids sorted and each once.
With no ids at all it writes two empty lists, which is how cycle Step 5 records a run whose lint was skipped. Exit 2 and
nothing written for an id that is not a whole number, outside 1..N (N is 0 when there is no usable lint-semantic.json),
in both lists, or for `--show` together with ids, and for a run folder that is not there.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text
from _cycle_common import (
    _front, _parse_time, claims_scope, entries, newest_step, semantic_scope, staged, step_results, synthesis_scope,
    write_scope)
from _wiki_config import in_sessions, in_tasks, now_stamp, today_label


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
EVENTS_FILE = "left-undone-events.txt"


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


def session_buckets(tri, nb: Path) -> list[dict]:
    """The notebook's configured buckets; frontmatter that does not parse reads as the one-bucket default, as no README
    gives. Only a README that does not parse into buckets falls back (a YAML syntax error, or YAML of the wrong shape:
    not a mapping, `buckets` not a list of mappings); a read error or any other failure surfaces."""
    parse_errors: tuple[type[BaseException], ...] = (AttributeError, TypeError, ValueError)
    try:
        from yaml import YAMLError  # optional: without PyYAML buckets() reads a regex fallback that raises none
        parse_errors += (YAMLError,)
    except ImportError:
        pass
    try:
        return tri.buckets(nb)[0]
    except UnicodeDecodeError:
        raise  # an undecodable README is a read error, though UnicodeDecodeError is a ValueError
    except parse_errors:
        return [{"folder": "main", "reader": tri.me()}]


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
    bs = session_buckets(tri, nb)
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
            scope, _all, _why, written = claims_scope(nb)
            cutoff = written or cutoff
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


def last_run(nb: Path, rf: Path) -> Path | None:
    """The last run: the newest earlier run folder with a `<id>-run-cycle-report.md` whose scratchpad mode is not
    report-only (a report-only run is never chosen, so a copy never nests)."""
    found = [d for d in (nb / "_inbox" / "reports").glob("*/*")
             if d.is_dir() and CYCLE_ID.match(d.name) and d.name < rf.name
             and (d / f"{d.name}-run-cycle-report.md").is_file() and cycle_mode(d)[0] != "report-only"]
    return max(found, key=lambda d: d.name, default=None)


def copied_event_lines(last: Path | None) -> list[str]:
    """A --report-only run's event lines: the last run's left-undone-events.txt, each line ending `(from <id>)`."""
    if last is None:
        return ["- Events of the last run: not checked (no earlier run with a report)"]
    f = last / EVENTS_FILE
    if not f.is_file():
        return [f"- Events of the last run: not checked (that run left no {EVENTS_FILE})"]
    return [f"{l} (from {last.name})" for l in f.read_text(encoding="utf-8", errors="replace").splitlines()
            if l.startswith("- ")]


# the step results that list sources: file, the mode-table key, the step's name in a reason, the lists read
SOURCE_STEPS = (("update.json", "ingest", "ingest", (("skipped", "skipped"), ("deferred", "deferred"), ("errors", "failed"))),
                ("discover.json", "discover", "discovery", (("skipped", "skipped"),)))


def ticket_marked_sources(nb: Path) -> set[str]:
    """The `source:` of every bucket ticket carrying `retry:` or `save_as_pdf:` (Needs you names those)."""
    tri = _triage()
    return {src for _folder, _path, src, front in tri.intake_tickets(nb, session_buckets(tri, nb))
            if "retry" in front or "save_as_pdf" in front}


def source_lines(nb: Path, rf: Path, mode: str | None, problem: str | None) -> list[str]:
    """One line per source the run's ingest skipped, deferred or failed and its discovery skipped (a discovery drop
    for 'already covered' was never queued, and a source whose ticket is in Needs you is left out); a step the mode
    runs that left no file, or one that cannot be read, is not checked."""
    out, marked = [], None
    for name, step, label, lists in SOURCE_STEPS:
        status = step_status(rf, name)
        if status is None:
            if not problem and mode in STEP_MODES[step]:
                out.append(f"- Sources: not checked ({label} left no {name})")
            continue
        data = step_data(rf, name)
        if status == "unreadable" or any(not isinstance(data.get(k, []), list) for k, _ in lists):
            out.append(f"- Sources: not checked ({name} unreadable)")
            continue
        for key, verb in lists:
            for item in data.get(key, []):
                rec = item if isinstance(item, dict) else {"url": item}
                src = str(next((rec[k] for k in ("url", "slug", "id", "item") if rec.get(k)), "(no source recorded)"))
                reason = " ".join(str(rec.get("reason") or rec.get("message") or "").split())
                if name == "discover.json" and "already covered" in reason.lower():
                    continue
                marked = ticket_marked_sources(nb) if marked is None else marked
                if src not in marked:
                    out.append(f"- Source {src}: {verb} — {reason or '(no reason recorded)'}")
    return out


TIER4 = re.compile(r"^\s*-\s*\[ \]\s.*?\]\((?P<url>[^)\s]+)\)\s*[—–-]+\s*tier\s*4\b", re.I)


def _feeds():
    """wiki-feeds.py's module (its file name has a dash), loaded as _triage() loads wiki-triage.py."""
    spec = importlib.util.spec_from_file_location("_wiki_feeds_pkg", Path(__file__).resolve().parent / "wiki-feeds.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tier4_lines(nb: Path, rf: Path, modifiers: list[str]) -> list[str]:
    """The unticked tier-4 candidates of this run's discovery checklist that the notebook does not hold, deferred by an
    unattended run. Only a run whose folder holds discover.json and whose scratchpad lists --no-confirm-discovery."""
    if not (rf / "discover.json").is_file() or "--no-confirm-discovery" not in modifiers:
        return []
    day = rf.name[:10]
    found = [f for f in (nb / "_inbox" / d / f"{day}-discovery.md" for d in ("discovered", "done")) if f.is_file()]
    if not found:
        return [f"- Tier-4 sources: not checked (no discovery checklist for {day})"]
    urls = [m.group("url") for l in found[0].read_text(encoding="utf-8", errors="replace").splitlines()
            if (m := TIER4.match(l))]
    if not urls:
        return []
    feeds = _feeds()
    held = feeds.known_sources(nb)
    return [f"- Source {u}: deferred — tier 4: needs your review (--no-confirm-discovery)"
            for u in urls if feeds.source_key(u) not in held]


def step_data(folder: Path, name: str) -> dict:
    """The JSON object of a step result, {} when it is absent, does not parse or is not an object."""
    try:
        data = json.loads((folder / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def usable_findings(data: dict) -> list | None:
    """The `findings` list of a semantic lint result (agentic-design's semantic lint file: one flat list, its length in
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
        if kind == "unusable":
            out.append(f"- Semantic findings from {folder.name}: not checked (lint-semantic.json has no usable findings list)")
        elif i == 0:
            if kind == "open":
                out.append(f"- Semantic findings from {folder.name}: {n} — awaiting your approval; "
                           f"{where_findings(folder.name)}; fixes made by hand since are not seen")
            elif kind == "unrecorded":
                out.append(f"- Semantic findings from {folder.name}: {n}, not checked "
                           "(that run recorded no applied or declined findings)")
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
    def fmt(ids: set[int]) -> str:
        return ",".join(map(str, sorted(ids)))
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
    refresh = step_status(rf, STEP_FILES["refresh"])
    if past or (not problem and mode in STEP_MODES["refresh"] and refresh != "completed"):
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
    reporting = mode == "report-only"
    last = last_run(nb, rf) if reporting else None
    events = copied_event_lines(last) if reporting else (
        lint_lines(rf, mode, problem) + semantic_lines(rf, mode, problem) + source_lines(nb, rf, mode, problem)
        + tier4_lines(nb, rf, modifiers))
    queues += events
    queues += earlier_semantic_lines(nb, rf)
    queues += bucket_ticket_lines(nb, mode, problem)
    queues += staged_lines(nb, rf)
    queues += checklist_lines(nb)
    if problem:
        queues.append(f"- Mode: not checked ({problem}); steps that left no file are not known")
    head = f"Left undone: {len(queues)} queue(s)" if queues else "Left undone: nothing"
    second = ([f"Disk-state queues are counted now; event lines are from the last run "
               f"({last.name if last else 'none: no earlier run with a report'})"] if reporting else [])
    out = rf / "left-undone.txt"
    if not reporting:
        atomic_write_text(rf / EVENTS_FILE, f"# {EVENTS_FILE}: {len(events)} event line(s) (cycle {rf.name})\n"
                          + "".join(l + "\n" for l in events))
    atomic_write_text(out, "\n".join([head, *second, *queues]) + "\n")
    print(f"left-undone: {head}; mode {mode or 'unknown'}; modifiers {','.join(modifiers) or 'none'} -> {out}")
    return 0
