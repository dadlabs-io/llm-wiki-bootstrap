#!/usr/bin/env python3
"""
Scan a Google Drive folder of curated article links, resolve any
short URLs (share.google, etc.) to their real destinations, dedupe,
and emit a Markdown report of the results.

Designed to be a wiki-cycle producer: the user drops links into a
named Drive folder throughout the week (typically via the iOS / Android
Share-to-Drive sheet, which writes a small text file containing the
article title and a `https://share.google/...` shortened URL); this
script harvests the queue and produces a clean list ready for ingest
or comparison against existing wiki entries.

Behaviour:
  1. Resolve auth — load cached OAuth token, or run a one-time browser
     flow against the supplied client secrets file.
  2. Look up the target folder by name. If not found, exit 2 with a
     clear message so the orchestrator can decide whether to ask the
     user about a possible rename / missing folder, or skip and move on.
  3. List every non-folder file under that folder.
  4. Read each file's text content.
  5. Extract URLs, follow short-URL redirects (share.google, goo.gl,
     forms.gle, etc.) with a real browser User-Agent so the destination
     resolves.
  6. Strip Google Discover tracking suffix (?shem=...).
  7. Dedupe by final URL. Note duplicates in the report.
  8. Write a Markdown report (--out path) and emit a JSON-line summary
     to stdout for orchestrator consumption.
  9. (Default ON, opt out with --no-move-handled) After successful queueing,
     move the source Drive files into <scan-folder>/_completed/<archive-subfolder>/
     so the active scan folder stays clean across cycles. Files that failed
     to queue are LEFT IN PLACE for retry. Requires write Drive scope — the
     first run triggers a one-time re-auth if the cached token only has
     readonly scope. Pass --no-move-handled for a passive dry-run scan that
     leaves the Drive folder untouched.

Setup (one-time):
  1. Create or reuse an OAuth 2.0 Desktop Client in any GCP project that
     has the Google Drive API enabled. Download the client_secret JSON.
  2. Run this script with --client-secrets <path-to-json>. A browser tab
     opens; approve the `drive.readonly` scope. The refresh token is
     cached at ~/.config/wiki-cycle/drive-token.json (override with
     --token-cache).
  3. Subsequent runs are silent.

Usage:
  python3 wiki-fetch-drive-folder.py \\
    --client-secrets ~/Downloads/client_secret_*.json \\
    --folder-name "__FOR CLAUDE" \\
    --out memory-bank/short-term/drive-folder-scan-YYYY-MM-DD.md

Exit codes:
  0  success, report written
  2  target folder not found in Drive (askable condition)
  3  authentication failed / cancelled
  1  any other error
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse


def _default_vault():
    """Resolve vault_root from <cwd>/.claude/wiki-config.json if present,
    otherwise fall back to "llm-wiki/wiki" relative to CWD. Per-project
    installs put wiki content at <project>/llm-wiki/wiki/."""
    import json as _json
    cfg_path = Path.cwd() / ".claude" / "wiki-config.json"
    if cfg_path.exists():
        try:
            cfg = _json.loads(cfg_path.read_text(encoding="utf-8"))
            v = cfg.get("vault_root")
            if v:
                return str(Path(v))
        except (_json.JSONDecodeError, OSError):
            pass
    return str(Path.cwd() / "llm-wiki" / "wiki")
# Force UTF-8 stdout on Windows so Unicode in titles doesn't crash printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_FOLDER_NAME = "__FOR CLAUDE"
DEFAULT_TOKEN_CACHE = Path.home() / ".config" / "wiki-cycle" / "drive-token.json"
DEFAULT_VAULT = _default_vault()
ACTIVITY_LOG = Path.home() / ".config" / "wiki-cycle" / "activity.jsonl"
DEFAULT_ARCHIVE_FOLDER = "_completed"

# Read-only is enough for passive scans (--no-move-handled). The default path
# moves handled files into _completed/, which needs full Drive scope. The
# scope is selected dynamically in main() so explicit dry-runs never escalate auth.
DRIVE_SCOPE_READONLY = "https://www.googleapis.com/auth/drive.readonly"
DRIVE_SCOPE_FULL = "https://www.googleapis.com/auth/drive"

URL_RE = re.compile(r"https?://\S+")
SHORTENER_HOSTS = {
    "share.google", "goo.gl", "g.co", "forms.gle",
    "youtu.be", "t.co", "bit.ly", "ow.ly", "tinyurl.com",
}
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
TRACKING_PARAMS_TO_STRIP = {
    # Google Discover share-tracking (added by share.google)
    "shem",
    # Standard UTM
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
}


def _write_activity_log(entry):
    """Append a structured record to the shared wiki activity log.
    Best-effort — never fails the script."""
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="seconds"))
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _err(msg):
    print(f"Error: {msg}", file=sys.stderr)


def _info(msg):
    print(msg, file=sys.stderr)


def get_drive_service(client_secrets_path, token_cache_path, scopes):
    """Return an authenticated Drive v3 service. Runs OAuth flow if needed.

    If the cached token covers a strict subset of the requested scopes
    (e.g. cached drive.readonly but caller now needs drive), re-auth is
    triggered automatically — Google's oauthlib will detect the mismatch
    and prompt the user to grant the upgraded scope."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        _err(f"missing dependency: {exc}. "
             "Install with: pip install google-api-python-client google-auth-oauthlib")
        sys.exit(1)

    creds = None
    token_cache_path = Path(token_cache_path)

    if token_cache_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_cache_path), scopes)
        except Exception as exc:
            _info(f"Cached token unreadable ({exc}); will re-authenticate.")
            creds = None

    # Force re-auth if cached token is missing any requested scope (scope
    # upgrade — e.g. switching from readonly to full drive for --move-handled).
    if creds and not creds.has_scopes(scopes):
        _info("Cached token missing required scopes; will re-authenticate "
              "with upgraded scope (browser will open).")
        creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as exc:
            _info(f"Token refresh failed ({exc}); will re-authenticate.")
            creds = None

    if not creds or not creds.valid:
        if not client_secrets_path:
            _err("no cached token (or scope upgrade required) and "
                 "--client-secrets not supplied.")
            sys.exit(3)
        client_secrets_path = Path(client_secrets_path).expanduser()
        if not client_secrets_path.exists():
            _err(f"client secrets file not found: {client_secrets_path}")
            sys.exit(3)
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secrets_path), scopes
        )
        # run_local_server opens browser; user approves; flow returns creds
        creds = flow.run_local_server(port=0, prompt="consent")
        token_cache_path.parent.mkdir(parents=True, exist_ok=True)
        token_cache_path.write_text(creds.to_json(), encoding="utf-8")
        _info(f"Token cached at {token_cache_path}")

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def find_or_create_subfolder(service, parent_id, name):
    """Return the Drive ID of the subfolder named `name` under `parent_id`,
    creating it if missing. Used to ensure _completed/<cycle-id>/ exists
    before we move handled files into it."""
    existing = find_folder_id(service, name, parent_id=parent_id)
    if existing:
        return existing
    body = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    created = service.files().create(body=body, fields="id").execute()
    return created["id"]


def move_handled_files(service, queue_results, entries, scan_folder_id,
                        archive_parent_name, archive_subfolder_name):
    """Move every Drive file whose URL was successfully queued into
    <scan_folder>/<archive_parent_name>/<archive_subfolder_name>/.

    For each queued entry, this moves both the winning Drive file AND
    any duplicate-side files that resolved to the same URL during
    scan_folder dedup — otherwise the duplicates would orphan in the
    scan folder and be re-processed forever.

    Returns (moved_count, failed_count, list of (file_id, status, message)).
    Files whose queue attempt failed are intentionally LEFT IN PLACE so
    the user can investigate / retry."""
    # Map winner file_id -> [dup file_ids] from the entries list
    dup_map = {e["file_id"]: e.get("dup_file_ids", []) for e in entries}

    file_ids_to_move = []
    for (fid, status, _msg) in queue_results:
        if status != "queued":
            continue
        file_ids_to_move.append(fid)
        file_ids_to_move.extend(dup_map.get(fid, []))

    if not file_ids_to_move:
        return 0, 0, []

    try:
        archive_parent_id = find_or_create_subfolder(
            service, scan_folder_id, archive_parent_name
        )
        target_folder_id = find_or_create_subfolder(
            service, archive_parent_id, archive_subfolder_name
        )
    except Exception as exc:
        _err(f"failed to create archive folder "
             f"'{archive_parent_name}/{archive_subfolder_name}': {exc}")
        return 0, len(file_ids_to_move), [
            (fid, "error", f"archive folder create failed: {exc}")
            for fid in file_ids_to_move
        ]

    moved = 0
    failed = 0
    results = []
    for file_id in file_ids_to_move:
        try:
            service.files().update(
                fileId=file_id,
                addParents=target_folder_id,
                removeParents=scan_folder_id,
                fields="id, parents",
            ).execute()
            moved += 1
            results.append((file_id, "moved", ""))
        except Exception as exc:
            failed += 1
            results.append((file_id, "error", str(exc)))
            _info(f"  move failed for {file_id}: {exc}")
    return moved, failed, results


def find_folder_id(service, folder_name, parent_id=None):
    """Return the Drive ID of the folder with the given exact name, or None.
    If `parent_id` is set, only match folders inside that parent (used when
    drilling into a subfolder under a known parent). If multiple folders share
    the name, prefer one not in trash and most recently modified."""
    safe_name = folder_name.replace("'", "\\'")
    query = (
        f"name = '{safe_name}' "
        f"and mimeType = 'application/vnd.google-apps.folder' "
        f"and trashed = false"
    )
    if parent_id:
        query += f" and '{parent_id}' in parents"
    resp = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name, modifiedTime, parents)",
        pageSize=10,
    ).execute()
    folders = resp.get("files", [])
    if not folders:
        return None
    folders.sort(key=lambda f: f.get("modifiedTime", ""), reverse=True)
    return folders[0]["id"]


def list_folder_files(service, folder_id):
    """Yield every non-folder file under folder_id, paging as needed."""
    page_token = None
    query = (
        f"'{folder_id}' in parents "
        f"and mimeType != 'application/vnd.google-apps.folder' "
        f"and trashed = false"
    )
    while True:
        resp = service.files().list(
            q=query,
            spaces="drive",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)",
            pageSize=100,
            pageToken=page_token,
        ).execute()
        for f in resp.get("files", []):
            yield f
        page_token = resp.get("nextPageToken")
        if not page_token:
            break


def read_file_text(service, file_id, mime_type):
    """Return the file's text content as a string, or '' if unreadable."""
    try:
        if mime_type == "application/vnd.google-apps.document":
            data = service.files().export(
                fileId=file_id, mimeType="text/plain"
            ).execute()
        elif mime_type and mime_type.startswith("text/"):
            data = service.files().get_media(fileId=file_id).execute()
        else:
            return ""
    except Exception as exc:
        _info(f"  read failed for {file_id}: {exc}")
        return ""
    if isinstance(data, bytes):
        try:
            return data.decode("utf-8", errors="replace")
        except Exception:
            return ""
    return str(data)


def extract_urls(text):
    """Return a list of URLs found in text, in order, with trailing
    punctuation trimmed."""
    urls = []
    for raw in URL_RE.findall(text or ""):
        url = raw.rstrip(".,;:!?)>]\"'")
        urls.append(url)
    return urls


def is_shortener(url):
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return host in SHORTENER_HOSTS


def strip_tracking(url):
    """Remove known share-tracking query params; preserve the rest."""
    try:
        parts = urlparse(url)
    except Exception:
        return url
    if not parts.query:
        return url
    kept = []
    for kv in parts.query.split("&"):
        key = kv.split("=", 1)[0]
        if key in TRACKING_PARAMS_TO_STRIP:
            continue
        kept.append(kv)
    new_query = "&".join(kept)
    return urlunparse(parts._replace(query=new_query))


def resolve_url(url, timeout=25):
    """Follow redirects with a browser UA. Return final URL or original
    on failure."""
    try:
        import requests
    except ImportError:
        _err("missing dependency: requests. Install with: pip install requests")
        sys.exit(1)
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": BROWSER_UA},
            allow_redirects=True,
            timeout=timeout,
        )
        return resp.url
    except Exception as exc:
        _info(f"  resolve failed for {url}: {exc}")
        return url


def derive_title(file_name, file_text, source_url):
    """Pick the most informative title we have. Drive file name is often
    truncated for the share-sheet 'Source: X.txt' pattern; the body text
    usually has more, so prefer body text up to the URL."""
    text = (file_text or "").strip()
    if text:
        # take everything up to the first URL on its line
        m = URL_RE.search(text)
        if m:
            head = text[: m.start()].strip().rstrip("-:|").strip()
            if head:
                return head
        first_line = text.splitlines()[0].strip()
        if first_line:
            return first_line
    # Fallback to file name minus .txt
    name = (file_name or "").strip()
    if name.lower().endswith(".txt"):
        name = name[:-4].strip()
    return name or source_url


def queue_entries_into_topic(entries, topic, vault, priority, added_by):
    """For each entry, call wiki-list-add.py to drop a queue file into
    <vault>/<topic>/_inbox/pending/. Returns (queued_count, failed_count,
    list of (file_id, status, message))."""
    add_script = Path(__file__).parent / "wiki-list-add.py"
    if not add_script.exists():
        _err(f"wiki-list-add.py not found next to this script ({add_script})")
        return 0, len(entries), [(e["file_id"], "error", "wiki-list-add.py missing") for e in entries]

    queued = 0
    failed = 0
    results = []
    for e in entries:
        cmd = [
            sys.executable, str(add_script),
            "--topic", topic,
            "--source", e["url"],
            "--vault", vault,
            "--added-by", added_by,
            "--priority", str(priority),
        ]
        if e.get("title"):
            cmd.extend(["--title", e["title"]])
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if proc.returncode == 0:
                queued += 1
                results.append((e["file_id"], "queued", proc.stdout.strip().splitlines()[0] if proc.stdout else ""))
            else:
                failed += 1
                err_msg = (proc.stderr or proc.stdout or "non-zero exit").strip().splitlines()[-1] if (proc.stderr or proc.stdout) else "non-zero exit"
                results.append((e["file_id"], "error", err_msg))
                _info(f"  queue failed for {e['url']}: {err_msg}")
        except subprocess.TimeoutExpired:
            failed += 1
            results.append((e["file_id"], "error", "timeout"))
            _info(f"  queue timeout for {e['url']}")
        except Exception as exc:
            failed += 1
            results.append((e["file_id"], "error", str(exc)))
            _info(f"  queue error for {e['url']}: {exc}")
    return queued, failed, results


def render_markdown(folder_name, folder_id, entries, duplicates, scanned_at,
                     queued_into=None, queued_count=None, queue_failed=None,
                     moved_into=None, moved_count=None, move_failed=None):
    """Return the report as a Markdown string."""
    lines = []
    lines.append(f"# Drive Folder Scan — `{folder_name}`")
    lines.append("")
    lines.append(f"**Generated:** {scanned_at}")
    lines.append(f"**Folder ID:** `{folder_id}`")
    lines.append(f"**Unique URLs:** {len(entries)}")
    lines.append(f"**Duplicates collapsed:** {len(duplicates)}")
    if queued_into:
        if queue_failed:
            lines.append(f"**Queued into:** `{queued_into}/_inbox/pending/` — {queued_count} queued, {queue_failed} failed")
        else:
            lines.append(f"**Queued into:** `{queued_into}/_inbox/pending/` — {queued_count} queued")
    if moved_into:
        if move_failed:
            lines.append(f"**Moved to:** `{moved_into}/` — {moved_count} moved, {move_failed} failed (only successfully-queued files are moved)")
        else:
            lines.append(f"**Moved to:** `{moved_into}/` — {moved_count} moved (only successfully-queued files are moved)")
    lines.append("")
    lines.append("Source: each Drive file is read, URLs are extracted, "
                 "short-URLs are followed to their destination, share-tracking "
                 "(`?shem=…`, UTM) is stripped, and duplicates are collapsed.")
    lines.append("")
    lines.append("## Articles")
    lines.append("")
    lines.append("| # | Title | URL |")
    lines.append("|---|---|---|")
    for i, e in enumerate(entries, start=1):
        title = (e["title"] or "").replace("|", "\\|").replace("\n", " ").strip()
        lines.append(f"| {i} | {title} | {e['url']} |")
    if duplicates:
        lines.append("")
        lines.append("## Duplicates collapsed")
        lines.append("")
        for d in duplicates:
            lines.append(
                f"- `{d['file']}` resolved to the same URL as "
                f"`{d['kept_file']}` ({d['url']})"
            )
    lines.append("")
    return "\n".join(lines) + "\n"


def scan_folder(service, folder_name, folder_id):
    """Read every file in the folder, resolve and dedupe URLs.

    Each returned entry carries `file_id` (the winner) and `dup_file_ids`
    (file_ids of any other Drive files that resolved to the same URL).
    The move step uses dup_file_ids to clean up duplicate-side files
    once the winner is successfully queued — otherwise they'd be left
    orphaned in the Drive folder and re-scanned forever."""
    seen_urls = {}  # canonical url -> entry
    duplicates = []
    files = list(list_folder_files(service, folder_id))
    _info(f"Found {len(files)} files in '{folder_name}'.")

    for f in files:
        text = read_file_text(service, f["id"], f.get("mimeType", ""))
        if not text:
            continue
        urls = extract_urls(text)
        if not urls:
            continue
        # Take the first URL — these files are one-link captures by convention
        raw_url = urls[0]
        if is_shortener(raw_url):
            resolved = resolve_url(raw_url)
        else:
            resolved = raw_url
        final = strip_tracking(resolved)
        title = derive_title(f.get("name", ""), text, final)

        if final in seen_urls:
            duplicates.append({
                "file": f.get("name", f["id"]),
                "file_id": f["id"],
                "kept_file": seen_urls[final]["file"],
                "url": final,
            })
            seen_urls[final].setdefault("dup_file_ids", []).append(f["id"])
            continue
        seen_urls[final] = {
            "title": title,
            "url": final,
            "file": f.get("name", f["id"]),
            "file_id": f["id"],
            "dup_file_ids": [],
        }

    return list(seen_urls.values()), duplicates


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--folder-name", default=DEFAULT_FOLDER_NAME,
        help=f"Parent Drive folder (default: {DEFAULT_FOLDER_NAME!r})",
    )
    parser.add_argument(
        "--subfolder", default=None,
        help="Optional subfolder name under --folder-name. When set, the scan "
             "targets <folder-name>/<subfolder>/ instead of the top-level "
             "<folder-name>/. Used by wiki-cycle to drill into a topic-specific "
             "subfolder (e.g., --subfolder agentic-design).",
    )
    parser.add_argument(
        "--client-secrets", default=os.environ.get("WIKI_DRIVE_CLIENT_SECRETS"),
        help="Path to OAuth 2.0 Desktop Client JSON (only needed first run; "
             "or set WIKI_DRIVE_CLIENT_SECRETS env var)",
    )
    parser.add_argument(
        "--token-cache", default=str(DEFAULT_TOKEN_CACHE),
        help=f"Cached OAuth token path (default: {DEFAULT_TOKEN_CACHE})",
    )
    parser.add_argument(
        "--out", default=None,
        help="Write the Markdown report to this path. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--ask-on-missing", action="store_true",
        help="Print a prompt to stderr asking the user when the folder is missing "
             "(orchestrator can decide whether to surface to human).",
    )
    parser.add_argument(
        "--queue-into", default=None,
        help="If set, queue each unique URL into <vault>/<topic>/_inbox/pending/ "
             "via wiki-list-add.py (e.g. --queue-into agentic-design)",
    )
    parser.add_argument(
        "--queue-vault", default=DEFAULT_VAULT,
        help=f"Vault root for --queue-into (default: {DEFAULT_VAULT})",
    )
    parser.add_argument(
        "--queue-priority", default="3",
        help="Priority 0-9 for queued entries (default 3)",
    )
    parser.add_argument(
        "--queue-added-by", default="drive-fetch",
        help="added_by label on queued entries (default 'drive-fetch')",
    )
    parser.add_argument(
        "--auth-only", action="store_true",
        help="Run the OAuth flow (if not already cached), confirm the token, "
             "then exit. No folder listing, no queueing, no moves. Used by "
             "/new-project to walk the user through Drive setup up front.",
    )
    parser.add_argument(
        "--move-handled", action=argparse.BooleanOptionalAction, default=True,
        help="After successful queueing, move each handled Drive file into "
             "<scan-folder>/_completed/<archive-subfolder>/ (folders auto-created). "
             "Files that failed to queue are LEFT IN PLACE for retry. "
             "DEFAULT ON so the Drive folder doesn't accumulate the same items "
             "across cycles. Pass --no-move-handled for a passive dry-run scan. "
             "Requires write Drive scope — first run triggers a one-time re-auth "
             "if the cached token only has readonly scope.",
    )
    parser.add_argument(
        "--archive-folder", default=DEFAULT_ARCHIVE_FOLDER,
        help=f"Top-level archive folder name under the scan folder "
             f"(default: {DEFAULT_ARCHIVE_FOLDER!r}). Only used with --move-handled.",
    )
    parser.add_argument(
        "--archive-subfolder", default=None,
        help="Subfolder under --archive-folder for this run's files "
             "(typically the wiki-cycle cycle_id, e.g. '2026-05-03-01'). "
             "Defaults to a UTC timestamp. Only used with --move-handled.",
    )
    args = parser.parse_args()

    started = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Pick the narrowest scope that covers what we'll do.
    # --auth-only always requests full scope so the cached token works for
    # subsequent runs that default --move-handled on (avoids a re-auth loop).
    if args.move_handled or args.auth_only:
        scopes = [DRIVE_SCOPE_FULL]
    else:
        scopes = [DRIVE_SCOPE_READONLY]
    service = get_drive_service(args.client_secrets, args.token_cache, scopes)

    if args.auth_only:
        # OAuth completed (get_drive_service ran the flow if needed and cached
        # the token). Emit a structured success signal and exit.
        result = {
            "status": "auth_ok",
            "token_cache": str(args.token_cache),
            "scopes": scopes,
        }
        print(json.dumps(result))
        _write_activity_log({
            "script": "wiki-fetch-drive-folder",
            "result": "auth_only_ok",
            "scopes": scopes,
        })
        return 0

    parent_id = find_folder_id(service, args.folder_name)
    if not parent_id:
        msg = (f"folder '{args.folder_name}' not found in your Drive. "
               "It may have been renamed, moved to a shared drive, or trashed.")
        _err(msg)
        if args.ask_on_missing:
            print(f"ASK_USER: {msg}", file=sys.stderr)
        _write_activity_log({
            "script": "wiki-fetch-drive-folder",
            "folder_name": args.folder_name,
            "result": "folder_not_found",
        })
        # Emit a stable JSON line so an orchestrator can react
        print(json.dumps({"status": "folder_not_found",
                          "folder_name": args.folder_name}))
        return 2

    # Drill into a subfolder if requested (wiki-cycle invocation)
    if args.subfolder:
        scan_folder_id = find_folder_id(service, args.subfolder, parent_id=parent_id)
        if not scan_folder_id:
            msg = (f"subfolder '{args.subfolder}' not found inside "
                   f"'{args.folder_name}'. The subfolder may not exist yet, "
                   f"may be misnamed (must match wiki topic exactly), or "
                   f"may be trashed.")
            _err(msg)
            if args.ask_on_missing:
                print(f"ASK_USER: {msg}", file=sys.stderr)
            _write_activity_log({
                "script": "wiki-fetch-drive-folder",
                "folder_name": args.folder_name,
                "subfolder": args.subfolder,
                "result": "subfolder_not_found",
            })
            print(json.dumps({"status": "subfolder_not_found",
                              "folder_name": args.folder_name,
                              "subfolder": args.subfolder}))
            return 2
        scan_label = f"{args.folder_name}/{args.subfolder}"
        folder_id = scan_folder_id
    else:
        scan_label = args.folder_name
        folder_id = parent_id

    entries, duplicates = scan_folder(service, scan_label, folder_id)

    queued_count = None
    queue_failed = None
    queue_results = None
    if args.queue_into and entries:
        _info(f"Queueing {len(entries)} entries into '{args.queue_into}/_inbox/pending/'...")
        queued_count, queue_failed, queue_results = queue_entries_into_topic(
            entries, args.queue_into, args.queue_vault,
            args.queue_priority, args.queue_added_by,
        )
        _info(f"Queue result: {queued_count} queued, {queue_failed} failed.")

    moved_count = None
    move_failed = None
    moved_into_path = None
    archive_subfolder_used = None
    if args.move_handled and queue_results:
        archive_subfolder_used = args.archive_subfolder or datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%dT%H%M%SZ")
        moved_into_path = (
            f"{scan_label}/{args.archive_folder}/{archive_subfolder_used}"
        )
        _info(f"Moving handled files into '{moved_into_path}/'...")
        moved_count, move_failed, _move_results = move_handled_files(
            service, queue_results, entries, folder_id,
            args.archive_folder, archive_subfolder_used,
        )
        _info(f"Move result: {moved_count} moved, {move_failed} failed.")

    md = render_markdown(
        scan_label, folder_id, entries, duplicates, started,
        queued_into=args.queue_into,
        queued_count=queued_count, queue_failed=queue_failed,
        moved_into=moved_into_path,
        moved_count=moved_count, move_failed=move_failed,
    )

    if args.out:
        out_path = Path(args.out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        _info(f"Wrote report: {out_path}")
        report_target = str(out_path)
    else:
        sys.stdout.write(md)
        report_target = "stdout"

    log_entry = {
        "script": "wiki-fetch-drive-folder",
        "folder_name": args.folder_name,
        "subfolder": args.subfolder,
        "scanned_path": scan_label,
        "folder_id": folder_id,
        "unique_urls": len(entries),
        "duplicates": len(duplicates),
        "report": report_target,
        "result": "ok",
    }
    if args.queue_into:
        log_entry["queued_into"] = args.queue_into
        log_entry["queued"] = queued_count
        log_entry["queue_failed"] = queue_failed
    if args.move_handled:
        log_entry["moved_into"] = moved_into_path
        log_entry["moved"] = moved_count
        log_entry["move_failed"] = move_failed
        log_entry["archive_subfolder"] = archive_subfolder_used
    _write_activity_log(log_entry)

    # Stable JSON-line summary for orchestrator consumption
    summary = {
        "status": "ok",
        "folder_name": args.folder_name,
        "subfolder": args.subfolder,
        "scanned_path": scan_label,
        "folder_id": folder_id,
        "unique_urls": len(entries),
        "duplicates": len(duplicates),
        "report": report_target,
    }
    if args.queue_into:
        summary["queued_into"] = args.queue_into
        summary["queued"] = queued_count
        summary["queue_failed"] = queue_failed
    if args.move_handled:
        summary["moved_into"] = moved_into_path
        summary["moved"] = moved_count
        summary["move_failed"] = move_failed
        summary["archive_subfolder"] = archive_subfolder_used
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        _err("interrupted")
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as exc:
        _err(f"unexpected error: {exc}")
        sys.exit(1)
