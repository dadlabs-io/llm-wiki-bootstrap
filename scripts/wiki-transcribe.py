#!/usr/bin/env python3
"""
wiki-transcribe.py — transcribe speech locally with Whisper (faster-whisper) and save it as a raw.

For media with no captions of its own: Instagram reels, a YouTube video without captions, an X video,
a podcast episode, or a local audio or video file. Nothing leaves the machine: no cloud speech service.

    # A URL: yt-dlp fetches the audio and the post's caption, the transcript goes to <topic>/raw/
    uv run --project <scripts> python <scripts>/wiki-transcribe.py --topic <topic> --url <url> --ingested-by claude-code

    # A local file: the transcript is printed, or written with --out
    uv run --project <scripts> python <scripts>/wiki-transcribe.py --file talk.m4a [--out talk.md]

Device (2026-10-05, measured on a 57 s reel): an NVIDIA GPU runs large-v3-turbo in float16 (4.8 s; it
takes one of the wiki search's GPU slots while it works, so the two take turns); without one, the CPU
runs `small` in int8 (29 s). `--device` and `--model` override. On the CPU, audio longer than
--max-cpu-minutes (default 20) stops with exit 4 rather than running for hours; --max-cpu-minutes 0
lifts the limit. The CUDA libraries come from the environment's `gpu` extra (installed only on a
machine with an NVIDIA GPU); on Windows their DLL folders are added to the search path here.

A raw holds the post's caption (Mark, 2026-10-05: the substance of a post is often there) and the
transcript, never the comments.

Exit codes: 0 saved or printed; 2 bad input; 3 the media could not be fetched or decoded; 4 too long
for the CPU (the message says how to override); 5 no GPU slot free in time.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _atomic_io import atomic_write_text  # noqa: E402
from _wiki_config import resolve_vault_topic  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GPU_MODEL, CPU_MODEL = "large-v3-turbo", "small"
DEFAULT_MAX_CPU_MINUTES = 20
SLOT_MAX_WAIT = 600


def _err(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)


def add_cuda_dll_dirs(prefix: Path | None = None) -> list[str]:
    """On Windows, put the pip-installed NVIDIA libraries (the `gpu` extra) on the DLL search path:
    ctranslate2 loads cuBLAS and cuDNN by name and does not look in site-packages itself."""
    if os.name != "nt":
        return []
    base = Path(prefix or sys.prefix) / "Lib" / "site-packages" / "nvidia"
    added = []
    for sub in ("cublas", "cudnn", "cuda_nvrtc", "cuda_runtime"):
        d = base / sub / "bin"
        if d.is_dir():
            os.add_dll_directory(str(d))
            os.environ["PATH"] = str(d) + os.pathsep + os.environ.get("PATH", "")
            added.append(str(d))
    return added


def cuda_devices() -> int:
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count()
    except Exception:  # noqa: BLE001 - no CUDA build or no driver: the CPU path
        return 0


def choose(device: str, model: str | None, n_cuda: int) -> tuple[str, str, str]:
    """(device, model, compute type) for the request; `auto` takes the GPU when there is one."""
    if device == "auto":
        device = "cuda" if n_cuda > 0 else "cpu"
    if device == "cuda" and n_cuda == 0:
        raise ValueError("--device cuda, but no CUDA device is available (no NVIDIA GPU, or the gpu extra "
                         "is not installed: re-run the global install on a machine with an NVIDIA GPU)")
    model = model or (GPU_MODEL if device == "cuda" else CPU_MODEL)
    return device, model, ("float16" if device == "cuda" else "int8")


def too_long_for_cpu(device: str, seconds: float | None, max_cpu_minutes: float) -> bool:
    return device == "cpu" and bool(max_cpu_minutes) and (seconds or 0) > max_cpu_minutes * 60


def gpu_slot(max_wait: float = SLOT_MAX_WAIT):
    """One of the wiki search's GPU slots (wiki-qmd-query.py), so Whisper and a search never fill the
    GPU together. Returns the held slot, or None when none came free in time."""
    spec = importlib.util.spec_from_file_location("_wiki_qmd_query", HERE / "wiki-qmd-query.py")
    qmd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qmd)
    n = int(os.environ.get("WIKI_QMD_SLOTS") or 3)
    slot, _waited = qmd.acquire_slot(n, max_wait)
    return slot


def transcribe(audio: str, device: str, model: str, compute: str, language: str | None = None) -> dict:
    """{"text", "segments", "language", "duration", "seconds"}; segments are (start, text)."""
    if device == "cuda":
        add_cuda_dll_dirs()
    from faster_whisper import WhisperModel
    t0 = time.monotonic()
    wm = WhisperModel(model, device=device, compute_type=compute)
    segments, info = wm.transcribe(audio, beam_size=5, vad_filter=True, language=language)
    segs = [(s.start, s.text.strip()) for s in segments if s.text.strip()]
    return {"text": " ".join(t for _s, t in segs), "segments": segs, "language": info.language,
            "duration": info.duration, "seconds": time.monotonic() - t0}


def fetch_media(url: str, workdir: Path) -> tuple[Path, dict]:
    """The audio (or the whole video when no audio-only format exists) and the post's metadata."""
    import yt_dlp
    opts = {"format": "bestaudio/best", "outtmpl": str(workdir / "media.%(ext)s"),
            "quiet": True, "no_warnings": True, "noprogress": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    files = sorted(workdir.glob("media.*"))
    if not files:
        raise RuntimeError("yt-dlp saved no media file")
    return files[0], info


def slugify(text: str, max_len: int = 50) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:max_len].rstrip("-") or "untitled"


def unique_path(target: Path) -> Path:
    if not target.exists():
        return target
    n = 2
    while (cand := target.with_name(f"{target.stem}-{n}{target.suffix}")).exists():
        n += 1
    return cand


def _q(s: str) -> str:
    return '"' + (s or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_raw(url: str, info: dict, result: dict, device: str, model: str, ingested_by: str) -> str:
    """The raw: header, the post's caption, then the transcript with a timestamp per segment."""
    caption = (info.get("description") or "").strip()
    uploader = info.get("uploader") or info.get("channel") or ""
    title = info.get("title") or (caption.splitlines()[0][:80] if caption else url)
    dur = int(result["duration"] or info.get("duration") or 0)
    fm = ["---", f"title: {_q(title)}", f"source_url: {url}", f"author: {_q(uploader)}",
          f"upload_date: {info.get('upload_date') or ''}", f"duration_seconds: {dur}",
          f"fetched_at: {datetime.now().astimezone().isoformat(timespec='seconds')}",
          f"ingested_by: {ingested_by}",
          f"transcribed_by: faster-whisper {model} on {device} ({result['seconds']:.0f}s)",
          f"language: {result['language']}", f"word_count: {len(result['text'].split())}",
          "type: media-transcript", "---", ""]
    body = [f"# {title}", "", f"**Author**: {uploader}  ", f"**Source**: <{url}>", "",
            "## Caption", "", caption or "_(no caption)_", "", "## Transcript", ""]
    if result["segments"]:
        body += [f"[{int(s) // 60}:{int(s) % 60:02d}] {t}" for s, t in result["segments"]]
    else:
        body.append("_(no speech found: music or silence only)_")
    return "\n".join(fm + body) + "\n"


def run(args) -> int:
    try:
        device, model, compute = choose(args.device, args.model, cuda_devices() if args.device != "cpu" else 0)
    except ValueError as e:
        _err(str(e))
        return 2
    with tempfile.TemporaryDirectory() as td:
        if args.url:
            try:
                media, info = fetch_media(args.url, Path(td))
            except Exception as e:  # noqa: BLE001 - yt-dlp raises many kinds; the message is what matters
                _err(f"could not fetch the media: {' '.join(str(e).split())[:300]}")
                return 3
        else:
            media, info = Path(args.file), {"title": Path(args.file).stem}
            if not media.is_file():
                _err(f"no such file: {media}")
                return 2
        if too_long_for_cpu(device, info.get("duration"), args.max_cpu_minutes):
            _err(f"{info['duration'] / 60:.0f} min of audio on the CPU (no GPU here) would take a long time; "
                 f"limit {args.max_cpu_minutes:g} min. Run it on a machine with a GPU, or pass "
                 "--max-cpu-minutes 0 to transcribe anyway")
            return 4
        slot = None
        if device == "cuda":
            slot = gpu_slot()
            if slot is None:
                _err(f"no GPU slot came free in {SLOT_MAX_WAIT}s (the wiki search holds them); retry later")
                return 5
        try:
            print(f"Transcribing with {model} on {device}…", file=sys.stderr)
            result = transcribe(str(media), device, model, compute, args.language)
        except Exception as e:  # noqa: BLE001 - a file the decoder cannot read, a model that cannot load
            _err(f"transcription failed: {' '.join(str(e).split())[:300]}")
            return 3
        finally:
            if slot is not None:
                slot.release()
    print(f"  {result['duration']:.0f}s of audio, {len(result['text'].split())} words, "
          f"{result['seconds']:.1f}s on {device}", file=sys.stderr)
    if not args.url:
        text = render_raw(str(media), info, result, device, model, args.ingested_by)
        if args.out:
            atomic_write_text(Path(args.out), text)
            print(f"out={args.out}")
        else:
            print(text)
        return 0
    vault, topic = resolve_vault_topic(args.topic, args.vault)
    raw_dir = Path(vault) / topic / "raw"
    if not raw_dir.parent.is_dir():
        _err(f"notebook '{topic}' not found at {raw_dir.parent}")
        return 2
    raw_dir.mkdir(parents=True, exist_ok=True)
    title = info.get("title") or info.get("description") or "media"
    raw_path = unique_path(raw_dir / f"{datetime.now():%Y-%m-%d}-{args.slug or slugify(title)}-transcript.md")
    atomic_write_text(raw_path, render_raw(args.url, info, result, device, model, args.ingested_by))
    print(f"Saved raw transcript: {raw_path}")
    print(f"raw_path={raw_path}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="a reel, video or episode URL yt-dlp can fetch; needs --topic")
    src.add_argument("--file", help="a local audio or video file")
    p.add_argument("--topic", help="the notebook whose raw/ gets the transcript (with --url)")
    p.add_argument("--vault", default=None, help="legacy vault root; default: resolve --topic through the registry")
    p.add_argument("--out", help="with --file: write the transcript here instead of printing it")
    p.add_argument("--slug", default=None)
    p.add_argument("--ingested-by", default="cli")
    p.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    p.add_argument("--model", default=None, help=f"default: {GPU_MODEL} on a GPU, {CPU_MODEL} on the CPU")
    p.add_argument("--language", default=None, help="e.g. en; default: detected")
    p.add_argument("--max-cpu-minutes", type=float, default=DEFAULT_MAX_CPU_MINUTES,
                   help="on the CPU, refuse longer audio (exit 4); 0 = no limit")
    args = p.parse_args(argv)
    if args.url and not args.topic:
        p.error("--url needs --topic (the notebook whose raw/ gets the transcript)")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
