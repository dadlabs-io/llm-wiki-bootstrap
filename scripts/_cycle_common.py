"""What the /wiki-cycle scope commands (wiki-cycle-scope.py) and the run-state reporting (_run_state.py) both read: the
notebook's entries and staged pages, the cut-off times, the walk over the run folders' step results, the one place a
scope file is written, and the three scope functions the `semantic`, `claims` and `synthesis` commands and the
`left-undone` counter share. Moved here unchanged from wiki-cycle-scope.py so the import runs one way:
wiki-cycle-scope.py imports this module and _run_state.py, _run_state.py imports this module, and this module
imports neither."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _entry_checks import split_frontmatter
from _atomic_io import atomic_write_text


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


def write_scope(run_folder: Path, name: str, paths: list[str], why: str) -> Path:
    """One path per line under a `#` header line, so an empty scope is never a zero-byte
    file (the stray-file sweeps delete those; the first suite run flagged one)."""
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


def _front(text: str) -> dict:
    """The frontmatter, by the one shared parser (task #177)."""
    return split_frontmatter(text, flat=True)[0]
