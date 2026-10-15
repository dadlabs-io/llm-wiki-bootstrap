#!/usr/bin/env python3
"""Checks for wiki-fetch-youtube.py's fallback (task #156, 2026-10-15): when YouTube's subtitle endpoint answers
HTTP 429, the fetcher transcribes the audio with wiki-transcribe.py instead of failing (cycles 2026-10-12-02,
2026-10-14-01 and -02 lost five talks to the 429; the audio download is not rate-limited). Never shipped; no
network, no model, no GPU: yt-dlp, fetching the audio and Whisper are replaced by fakes.

    uv run python tests/scripts/test_fetch_youtube_429.py    # exit 0 = every check passed
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
sys.path.insert(0, str(ROOT / "scripts"))

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


yt = load("wiki_fetch_youtube", "wiki-fetch-youtube.py")
tr = load("wiki_transcribe_t", "wiki-transcribe.py")
yt.time.sleep = lambda s: None  # the old retry loop backs off for 75 s; never wait in a test

INFO = {"id": "Uv0nAf_7tyU", "title": "Managed Agents part 1", "channel": "Anthropic", "uploader": "Anthropic",
        "description": "A talk.", "duration": 1800, "upload_date": "20261001"}
JSON3 = {"events": [{"tStartMs": 0, "segs": [{"utf8": "Hello and welcome."}]}]}


def fake_ydl(mode: str, calls: list):
    """A stand-in for yt_dlp.YoutubeDL: 'ok' writes the subtitle file, '429' and 'other' raise."""
    class FakeYDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, url, download=True):
            calls.append(url)
            if mode == "429":
                raise yt.DownloadError("ERROR: Unable to download video subtitles for 'en': "
                                       "HTTP Error 429: Too Many Requests")
            if mode == "other":
                raise yt.DownloadError("ERROR: [youtube] Uv0nAf_7tyU: Video unavailable")
            Path(self.opts["outtmpl"] + ".en.json3").write_text(json.dumps(JSON3), encoding="utf-8")
            return dict(INFO)
    return FakeYDL


def run(mode: str, vault: Path, *, cuda=1, duration=1800):
    calls: list = []
    transcribed: dict = {}
    yt.yt_dlp.YoutubeDL = fake_ydl(mode, calls)
    tr.cuda_devices = lambda: cuda
    tr.gpu_slot = lambda *a, **k: type("S", (), {"release": lambda self: None})()

    def fake_fetch(url, workdir):
        f = Path(workdir) / "media.m4a"
        f.write_bytes(b"x")
        return f, {**INFO, "duration": duration}

    def fake_transcribe(audio, device, model, compute, language=None):
        transcribed.update(device=device)
        return {"text": "Hello and welcome.", "language": "en", "duration": float(duration), "seconds": 3.0,
                "segments": [(0.0, "Hello and welcome.")]}

    tr.fetch_media, tr.transcribe = fake_fetch, fake_transcribe
    yt.load_transcriber = lambda: tr
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = yt.fetch_to_raw(str(vault), "nb", "https://www.youtube.com/watch?v=Uv0nAf_7tyU", "claude-code")
        except Exception as e:  # noqa: BLE001 - the red run may lack load_transcriber's caller; report, don't crash
            code = f"raised {type(e).__name__}: {e}"
    return code, out.getvalue(), err.getvalue(), calls, transcribed


with tempfile.TemporaryDirectory() as td:
    vault = Path(td)
    (vault / "nb" / "wiki").mkdir(parents=True)
    raw_dir = vault / "nb" / "raw"

    # 1. Subtitles answer 429: the audio is transcribed instead, and the raw is a Whisper transcript.
    code, out, err, calls, transcribed = run("429", vault)
    raws = sorted(raw_dir.glob("*-transcript.md")) if raw_dir.is_dir() else []
    check("a subtitle 429 still ends in exit 0 and one raw", code == 0 and len(raws) == 1, (code, err[-300:]))
    check("... the raw is a Whisper transcript (type: media-transcript)",
          bool(raws) and "type: media-transcript" in raws[0].read_text(encoding="utf-8"))
    check("... stdout names the fallback and gives raw_path=",
          "Fallback: transcribed (subtitles HTTP 429)" in out and "raw_path=" in out, out[-300:])
    check("... the subtitle request is not retried after a 429", len(calls) == 1, len(calls))
    check("... on the GPU", transcribed.get("device") == "cuda", transcribed)
    for r in raws:
        r.unlink()

    # 2. No GPU and a long talk: the transcriber's own limit holds; its exit code and reason come through.
    code, out, err, calls, transcribed = run("429", vault, cuda=0, duration=3600)
    check("no GPU and an hour of audio: exit 4, the override named, nothing transcribed or saved",
          code == 4 and "--max-cpu-minutes 0" in err and not transcribed
          and not (raw_dir.is_dir() and list(raw_dir.glob("*.md"))), (code, err[-300:]))

    # 3. Any other download error behaves as before: retried, then exit 1, no transcription.
    code, out, err, calls, transcribed = run("other", vault)
    check("another download error: retried, exit 1, no fallback",
          code == 1 and len(calls) > 1 and not transcribed and "Fallback" not in out, (code, len(calls), out[-200:]))

    # 4. Subtitles that work: a caption transcript as before, no fallback.
    code, out, err, calls, transcribed = run("ok", vault)
    raws = sorted(raw_dir.glob("*-transcript.md")) if raw_dir.is_dir() else []
    check("subtitles that work: one youtube-transcript raw, no fallback",
          code == 0 and len(raws) == 1 and "type: youtube-transcript" in raws[0].read_text(encoding="utf-8")
          and not transcribed and "Fallback" not in out, (code, err[-300:]))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
