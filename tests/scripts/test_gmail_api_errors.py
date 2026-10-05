#!/usr/bin/env python3
"""Checks that wiki-fetch-gmail.py reports a refused Gmail API call in one line (exit 3), never a
traceback, and that `auth` proves the API answers before it says auth_ok. Never shipped; no Gmail
access: a fake service raises an error shaped like googleapiclient's HttpError.

    uv run python tests/scripts/test_gmail_api_errors.py    # exit 0 = every check passed

Seen 2026-10-05: `auth` printed auth_ok, then `fetch` died with a 40-line traceback (exit 1) because
the Gmail API was not enabled in the OAuth client's Google Cloud project.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GMAIL = ROOT / "scripts" / "wiki-fetch-gmail.py"
sys.path.insert(0, str(ROOT / "scripts"))

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


spec = importlib.util.spec_from_file_location("wiki_fetch_gmail", GMAIL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

NOT_ENABLED = ('<HttpError 403 when requesting https://gmail.googleapis.com/gmail/v1/users/me/labels?alt=json returned '
               '"Gmail API has not been used in project 418582752997 before or it is disabled. Enable it by visiting '
               'https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=418582752997 then '
               'retry.". Details: "[{\'reason\': \'accessNotConfigured\'}]">')


class _Resp:
    def __init__(self, status):
        self.status = status


class HttpError(Exception):  # the name the script recognises, as googleapiclient.errors.HttpError
    def __init__(self, status, text):
        super().__init__(text)
        self.resp = _Resp(status)


class _Call:
    def __init__(self, result=None, exc=None):
        self.result, self.exc = result, exc

    def execute(self):
        if self.exc:
            raise self.exc
        return self.result


class FakeService:
    def __init__(self, labels=None, exc=None):
        self._labels, self._exc = labels or [], exc

    def users(self):
        return self

    def labels(self):
        return self

    def list(self, userId):  # noqa: N803 - the Google client's argument name
        return _Call({"labels": self._labels}, self._exc)


def run(argv, service):
    """Run the script's entry point with a fake Gmail service; (exit code, stdout, stderr)."""
    mod.gmail_service = lambda *_a, **_k: service
    out, err = io.StringIO(), io.StringIO()
    old = sys.argv
    sys.argv = ["wiki-fetch-gmail.py", *argv]
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


check("the script has an entry() that wraps main()", hasattr(mod, "entry"))

if hasattr(mod, "entry"):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        nb = tmp / "notebooks" / "t"
        (nb / "wiki").mkdir(parents=True)
        reg = tmp / "linked-notebooks.json"
        reg.write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}), encoding="utf-8")
        proj = tmp / "project"
        (proj / ".claude").mkdir(parents=True)
        (proj / ".claude" / "wiki-config.json").write_text(
            json.dumps({"notebook": "t", "registry": reg.as_posix()}), encoding="utf-8")
        import os
        os.chdir(proj)
        runf = tmp / "run"

        # 1. fetch, API not enabled: one line, exit 3, the fix named.
        code, out, err = run(["fetch", "--topic", "t", "--run-folder", str(runf), "--no-resolve"],
                             FakeService(exc=HttpError(403, NOT_ENABLED)))
        check("fetch with the API not enabled exits 3", code == 3, code)
        check("... with no traceback", "Traceback" not in err, err[:300])
        check("... saying the Gmail API is not enabled, naming the project", "not enabled" in err and "418582752997" in err,
              err)
        check("... and where to enable it", "gmail.googleapis.com" in err, err)
        check("... in one line", len([ln for ln in err.splitlines() if ln.strip()]) == 1, err)

        # 2. another refusal (401): still one line, exit 3, the status named.
        code, out, err = run(["fetch", "--topic", "t", "--run-folder", str(runf), "--no-resolve"],
                             FakeService(exc=HttpError(401, "<HttpError 401 Request had invalid credentials>")))
        check("another refused call exits 3 in one line, naming its status",
              code == 3 and "Traceback" not in err and "401" in err, (code, err[:300]))

        # 3. auth calls the API: a refusal there fails the sign-in step, not the first cycle.
        code, out, err = run(["auth"], FakeService(exc=HttpError(403, NOT_ENABLED)))
        check("auth with the API not enabled exits 3, not auth_ok", code == 3 and "auth_ok" not in out, (code, out, err))

        # 4. auth with a working API reports the labels it would read.
        labels = [{"name": "...wiki-inbox", "id": "L1"}, {"name": "...wiki-inbox/read", "id": "L2"}]
        code, out, err = run(["auth"], FakeService(labels=labels))
        rep = json.loads(out) if out.strip().startswith("{") else {}
        check("auth with a working API exits 0 with auth_ok", code == 0 and rep.get("status") == "auth_ok", (code, out, err))
        check("... and says whether the label and the done label exist",
              rep.get("label_found") is True and rep.get("done_label_found") is True, rep)
        code, out, err = run(["auth"], FakeService(labels=[{"name": "Inbox", "id": "INBOX"}]))
        rep = json.loads(out) if out.strip().startswith("{") else {}
        check("auth reports a missing label instead of passing silently",
              code == 0 and rep.get("label_found") is False, rep)

        # 5. a bug that is not an API refusal still shows its traceback.
        def boom(*_a, **_k):
            raise ValueError("a real bug")
        mod_gs = mod.gmail_service
        try:
            code, out, err = run(["auth"], FakeService())
            mod.gmail_service = boom
            out2, err2 = io.StringIO(), io.StringIO()
            sys.argv = ["wiki-fetch-gmail.py", "auth"]
            raised = False
            try:
                with contextlib.redirect_stdout(out2), contextlib.redirect_stderr(err2):
                    mod.entry()
            except ValueError:
                raised = True
            check("an error that is not an API refusal is not swallowed", raised)
        finally:
            mod.gmail_service = mod_gs
            os.chdir(ROOT)  # Windows cannot remove the working directory

# 6. archive (2026-10-05, cycle 2026-10-05-01): a handled email is moved to the done label AND marked read;
#    one the user already deleted (Gmail answers 404) is gone, not a failure; any other refusal still fails.
class ArchiveService:
    def __init__(self, gone=(), refuse=()):
        self.calls, self.gone, self.refuse = [], set(gone), set(refuse)

    def users(self):
        return self

    def labels(self):
        return self

    def messages(self):
        return self

    def list(self, userId):  # noqa: N803
        return _Call({"labels": [{"name": "...wiki-inbox", "id": "L1"}, {"name": "...wiki-inbox/read", "id": "L2"}]})

    def modify(self, userId, id, body):  # noqa: A002, N803 - the Google client's argument names
        if id in self.gone:
            return _Call(exc=HttpError(404, f"<HttpError 404 Requested entity was not found: {id}>"))
        if id in self.refuse:
            return _Call(exc=HttpError(500, "<HttpError 500 Backend Error>"))
        self.calls.append((id, body))
        return _Call({"id": id})


with tempfile.TemporaryDirectory() as td:
    runf = Path(td) / "run"
    runf.mkdir()
    step = {"skill": "wiki-fetch-gmail", "cycle_id": "c1", "step": "email-fetch", "timestamp": "t", "status": "completed",
            "summary": {"emails_seen": 3, "candidates": 0, "full_text_emails": 0, "known": 0, "junk_dropped": 0,
                        "queued": 0, "archived": 0},
            "queued": [], "skipped": [], "deferred": [], "notes": "", "errors": [], "label": "...wiki-inbox",
            "done_label": "...wiki-inbox/read", "source": "gmail", "reviewed": True, "archived_ids": [],
            "emails": [{"id": i, "subject": i, "sender": "s", "date": "d", "words": 1, "web_url": "", "full_text": False,
                        "file": ""} for i in ("m1", "m2", "m3")], "candidates": []}
    (runf / "email-fetch.json").write_text(json.dumps(step), encoding="utf-8")
    svc = ArchiveService(gone={"m2"})
    code, out, err = run(["archive", "--run-folder", str(runf)], svc)
    bodies = dict(svc.calls)
    check("archive moves a handled email to the done label and marks it read",
          bodies.get("m1", {}).get("addLabelIds") == ["L2"]
          and set(bodies.get("m1", {}).get("removeLabelIds", [])) == {"L1", "UNREAD"}, (code, svc.calls, err[:300]))
    after = json.loads((runf / "email-fetch.json").read_text(encoding="utf-8"))
    check("an email the user already deleted (404) counts as handled, not failed",
          code == 0 and "m2" in after.get("archived_ids", []) and not after.get("errors"), (code, out, after.get("errors")))
    check("... and the step notes it as gone", "m2" in json.dumps(after.get("gone_ids", after.get("notes", ""))), after.get("notes"))
    after["archived_ids"], after["errors"] = [], []
    (runf / "email-fetch.json").write_text(json.dumps(after), encoding="utf-8")
    code, out, err = run(["archive", "--run-folder", str(runf)], ArchiveService(refuse={"m3"}))
    after = json.loads((runf / "email-fetch.json").read_text(encoding="utf-8"))
    check("any other refusal is still a failure, left for next time",
          code == 1 and "m3" not in after.get("archived_ids", []) and after.get("errors"), (code, after.get("errors")))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
