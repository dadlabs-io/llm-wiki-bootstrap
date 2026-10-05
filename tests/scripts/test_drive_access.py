#!/usr/bin/env python3
"""Checks that wiki-fetch-drive-folder.py's sign-in matches what the machine actually has, and that
a setup problem is reported in one line naming the fix. Never shipped; no Drive access: tokens are
temporary files and a fake service stands in for Google.

    uv run python tests/scripts/test_drive_access.py    # exit 0 = every check passed

Seen 2026-10-05 (cycle shakedown): a look-only scan (--no-move-handled) asked to refresh a full-Drive
token as read-only, Google refused (invalid_scope), and the script then wanted client_secrets.json,
which was not on the machine, though the token carries the client. A Drive API that is not enabled
would have ended as "unexpected error: <HttpError ...>", exit 1.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DRIVE = ROOT / "scripts" / "wiki-fetch-drive-folder.py"
sys.path.insert(0, str(ROOT / "scripts"))

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


spec = importlib.util.spec_from_file_location("wiki_fetch_drive_folder", DRIVE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

FULL, READONLY = mod.DRIVE_SCOPE_FULL, mod.DRIVE_SCOPE_READONLY
NOT_ENABLED = ('<HttpError 403 when requesting https://www.googleapis.com/drive/v3/files returned "Google Drive API has '
               'not been used in project 418582752997 before or it is disabled. Enable it by visiting '
               'https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=418582752997 then '
               'retry.". Details: "[{\'reason\': \'accessNotConfigured\'}]">')


def token(path: Path, scopes, expiry="2099-01-01T00:00:00Z"):
    path.write_text(json.dumps({
        "token": "ya29.fake", "refresh_token": "1//fake", "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "123-abc.apps.googleusercontent.com", "client_secret": "GOCSPX-fake", "scopes": scopes,
        "expiry": expiry}), encoding="utf-8")


class _Resp:
    def __init__(self, status):
        self.status = status


class HttpError(Exception):  # the name the script recognises, as googleapiclient.errors.HttpError
    def __init__(self, status, text):
        super().__init__(text)
        self.resp = _Resp(status)


class _Call:
    def __init__(self, fn):
        self.fn = fn

    def execute(self):
        return self.fn()


class FakeDrive:
    """files().list answers a folder lookup by name; or raises, as a project without the API does."""

    def __init__(self, folders=(), exc=None):
        self.folders, self.exc, self.calls = list(folders), exc, 0

    def files(self):
        return self

    def list(self, q="", **_kw):
        def run():
            self.calls += 1
            if self.exc:
                raise self.exc
            return {"files": [{"id": f"id-{n}", "name": n, "modifiedTime": "2026-10-01T00:00:00Z"}
                              for n in self.folders if f"name = '{n}'" in q]}
        return _Call(run)


def run_main(argv, service):
    mod.get_drive_service = lambda *_a, **_k: service
    out, err = io.StringIO(), io.StringIO()
    old = sys.argv
    sys.argv = ["wiki-fetch-drive-folder.py", *argv]
    code = None
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = mod.entry()
            except SystemExit as e:
                code = e.code
    finally:
        sys.argv = old
    return code, out.getvalue(), err.getvalue()


real_get = mod.get_drive_service
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)

    # 1. A full-Drive token serves a look-only scan as it is: its own scopes, so a refresh asks Google for
    #    what was granted (asking for drive.readonly is what Google refused with invalid_scope).
    full_tok = tmp / "full.json"
    token(full_tok, [FULL])
    check("the script has load_cached_creds()", hasattr(mod, "load_cached_creds"))
    if hasattr(mod, "load_cached_creds"):
        creds = mod.load_cached_creds(full_tok, [READONLY])
        check("a full-Drive token is accepted for a read-only scan", creds is not None)
        check("... keeping its own full scope, so a refresh asks for what was granted",
              creds is not None and FULL in (creds.scopes or []), getattr(creds, "scopes", None))
        ro_tok = tmp / "ro.json"
        token(ro_tok, [READONLY])
        check("a read-only token is not accepted when the run moves files (full scope needed)",
              mod.load_cached_creds(ro_tok, [FULL]) is None)
        check("a read-only token serves a read-only scan", mod.load_cached_creds(ro_tok, [READONLY]) is not None)

    # 2. With no client_secrets.json, the client recorded in the token is used (as the Gmail script does).
    check("the script has client_config()", hasattr(mod, "client_config"))
    if hasattr(mod, "client_config"):
        cfg = mod.client_config(None, full_tok)
        check("no secrets file: the token's own client is used",
              (cfg or {}).get("installed", {}).get("client_id") == "123-abc.apps.googleusercontent.com", cfg)
        check("no secrets file and no token: nothing to sign in with", mod.client_config(None, tmp / "none.json") is None)

    # 3. The API not enabled: one line, exit 3, the fix named.
    check("the script has an entry() that wraps main()", hasattr(mod, "entry"))
    if hasattr(mod, "entry"):
        code, out, err = run_main(["--subfolder", "agentic-design", "--no-move-handled"],
                                  FakeDrive(exc=HttpError(403, NOT_ENABLED)))
        check("a scan with the Drive API not enabled exits 3", code == 3, (code, err[:300]))
        check("... in one line, no traceback, naming the API, the project and where to enable it",
              len([ln for ln in err.splitlines() if ln.strip()]) == 1 and "Traceback" not in err
              and "Drive API is not enabled" in err and "418582752997" in err and "drive.googleapis.com" in err, err)
        code, out, err = run_main(["--no-move-handled"], FakeDrive(exc=HttpError(401, "<HttpError 401 invalid creds>")))
        check("another refused call exits 3 in one line, naming its status",
              code == 3 and "401" in err and "Traceback" not in err, (code, err[:300]))

        # 4. --auth-only proves the API answers and reports the folders it will scan.
        code, out, err = run_main(["--auth-only", "--subfolder", "agentic-design"],
                                  FakeDrive(folders=["__FOR CLAUDE", "agentic-design"]))
        rep = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
        check("--auth-only with a working API exits 0 with auth_ok", code == 0 and rep.get("status") == "auth_ok",
              (code, out, err))
        check("... and says the folder and the subfolder were found",
              rep.get("folder_found") is True and rep.get("subfolder_found") is True, rep)
        code, out, err = run_main(["--auth-only", "--subfolder", "agentic-design"], FakeDrive(folders=["__FOR CLAUDE"]))
        rep = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
        check("--auth-only reports a missing subfolder instead of passing silently",
              code == 0 and rep.get("subfolder_found") is False, rep)
        code, out, err = run_main(["--auth-only"], FakeDrive(exc=HttpError(403, NOT_ENABLED)))
        check("--auth-only with the API not enabled exits 3, not auth_ok", code == 3 and "auth_ok" not in out,
              (code, out, err))

    mod.get_drive_service = real_get

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
