#!/usr/bin/env python3
"""Checks for wiki-transcribe.py (local Whisper, 2026-10-05) and the installer's `gpu` extra. Never shipped;
no model, no GPU, no network: transcription, fetching and the GPU slot are replaced by fakes. The real run
(a 57 s reel: 4.8 s on the RTX 4070, 29 s on the CPU) is recorded in the commit, not repeated here.

    uv run python tests/scripts/test_transcribe.py    # exit 0 = every check passed
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

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


tr = load("wiki_transcribe", "wiki-transcribe.py")
inst = load("_install_tooling_t", "_install_tooling.py")

# 1. Device and model.
check("a GPU: large-v3-turbo in float16", tr.choose("auto", None, 1) == ("cuda", "large-v3-turbo", "float16"))
check("no GPU: small in int8 on the CPU", tr.choose("auto", None, 0) == ("cpu", "small", "int8"))
check("--model wins", tr.choose("cpu", "medium", 1) == ("cpu", "medium", "int8"))
try:
    tr.choose("cuda", None, 0)
    check("--device cuda without a GPU is refused", False)
except ValueError as e:
    check("--device cuda without a GPU is refused, naming the gpu extra", "gpu extra" in str(e), e)

# 2. The CPU length limit.
check("an hour on the CPU is too long at 20 min", tr.too_long_for_cpu("cpu", 3600, 20))
check("a reel on the CPU is fine", not tr.too_long_for_cpu("cpu", 57, 20))
check("the GPU has no limit", not tr.too_long_for_cpu("cuda", 3600, 20))
check("--max-cpu-minutes 0 lifts it", not tr.too_long_for_cpu("cpu", 3600, 0))

# 3. The raw: header parses, caption kept, transcript timestamped, no comments.
INFO = {"title": "Video by nicksaraev", "description": 'Comment "PLUGIN" to get these 5 plugins.\nSecond line',
        "uploader": "Nick Saraev", "upload_date": "20260901", "duration": 57,
        "comments": [{"text": "great post"}]}
RESULT = {"text": "Don't use Claude Code. The first is OmniRoute.", "language": "en", "duration": 57.3, "seconds": 4.8,
          "segments": [(0.0, "Don't use Claude Code."), (65.2, "The first is OmniRoute.")]}
raw = tr.render_raw("https://www.instagram.com/reel/X/", INFO, RESULT, "cuda", "large-v3-turbo", "claude-code")
head = yaml.safe_load(raw.split("---")[1])
check("the header parses as YAML, with source, author and how it was transcribed",
      head.get("source_url") == "https://www.instagram.com/reel/X/" and head.get("author") == "Nick Saraev"
      and "large-v3-turbo on cuda" in head.get("transcribed_by", "") and head.get("type") == "media-transcript", head)
check("the caption is kept, whole", "## Caption" in raw and 'Comment "PLUGIN"' in raw and "Second line" in raw)
check("the transcript is timestamped", "[0:00] Don't use Claude Code." in raw and "[1:05] The first is OmniRoute." in raw)
check("comments are left out", "great post" not in raw)
silent = tr.render_raw("u", {"title": "t"}, {**RESULT, "segments": [], "text": ""}, "cpu", "small", "cli")
check("music only: says no speech was found", "no speech found" in silent)


# 4. run(): fakes for the GPU, the slot, fetching and Whisper.
class FakeSlot:
    released = False

    def release(self):
        FakeSlot.released = True


def run(argv, *, cuda=1, slot=True, info=None):
    tr.cuda_devices = lambda: cuda
    tr.gpu_slot = lambda *a, **k: FakeSlot() if slot else None
    calls = {}

    def fake_fetch(url, workdir):
        f = Path(workdir) / "media.m4a"
        f.write_bytes(b"x")
        return f, dict(info or INFO)

    def fake_transcribe(audio, device, model, compute, language=None):
        calls.update(device=device, model=model)
        return dict(RESULT)

    tr.fetch_media, tr.transcribe = fake_fetch, fake_transcribe
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = tr.main(argv)
    return code, out.getvalue(), err.getvalue(), calls


with tempfile.TemporaryDirectory() as td:
    vault = Path(td)
    (vault / "nb" / "wiki").mkdir(parents=True)
    FakeSlot.released = False
    code, out, err, calls = run(["--url", "https://www.instagram.com/reel/X/", "--topic", "nb", "--vault", str(vault),
                                 "--ingested-by", "claude-code"])
    raws = list((vault / "nb" / "raw").glob("*-transcript.md"))
    check("--url saves one raw and prints raw_path=", code == 0 and len(raws) == 1 and "raw_path=" in out, (code, err))
    check("... on the GPU with the GPU model, and the slot is given back",
          calls.get("device") == "cuda" and calls.get("model") == "large-v3-turbo" and FakeSlot.released, calls)
    code, out, err, calls = run(["--url", "u", "--topic", "nb", "--vault", str(vault)], cuda=0)
    check("no GPU: the CPU and the small model", code == 0 and calls.get("device") == "cpu"
          and calls.get("model") == "small", (code, calls, err))
    code, out, err, calls = run(["--url", "u", "--topic", "nb", "--vault", str(vault)], cuda=0,
                                info={**INFO, "duration": 3600})
    check("an hour of audio with no GPU stops with exit 4, saying how to override",
          code == 4 and "--max-cpu-minutes 0" in err and not calls, (code, err))
    code, out, err, calls = run(["--url", "u", "--topic", "nb", "--vault", str(vault), "--max-cpu-minutes", "0"], cuda=0,
                                info={**INFO, "duration": 3600})
    check("--max-cpu-minutes 0 transcribes it anyway", code == 0 and calls.get("device") == "cpu", (code, err))
    code, out, err, calls = run(["--url", "u", "--topic", "nb", "--vault", str(vault)], slot=False)
    check("no GPU slot free in time: exit 5, nothing transcribed", code == 5 and not calls, (code, err))
    local = vault / "talk.m4a"
    local.write_bytes(b"x")
    code, out, err, calls = run(["--file", str(local), "--out", str(vault / "talk.md")])
    check("--file --out writes the transcript there", code == 0 and (vault / "talk.md").is_file(), (code, err))
    code, out, err, calls = run(["--file", str(vault / "missing.m4a")])
    check("a missing file is exit 2", code == 2, (code, err))

    # 5. Windows: the pip NVIDIA libraries' folders go on the DLL path.
    if os.name == "nt":
        for sub in ("cublas", "cudnn"):
            (vault / "Lib" / "site-packages" / "nvidia" / sub / "bin").mkdir(parents=True)
        added = tr.add_cuda_dll_dirs(vault)
        check("the cuBLAS and cuDNN bin folders are added to the DLL path",
              len(added) == 2 and all(a in os.environ["PATH"] for a in added), added)

# 6. The installer's gpu extra: only where nvidia-smi answers, and the status check asks for the same.
real_which, real_run = inst.shutil.which, inst.subprocess.run
inst.shutil.which = lambda name: None
check("no nvidia-smi: no extras", inst.env_extras() == [])
inst.shutil.which = lambda name: "nvidia-smi"
inst.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 0)
check("nvidia-smi answers: the gpu extra", inst.env_extras() == ["gpu"])
inst.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 9)
check("nvidia-smi present but failing (no driver): no extras", inst.env_extras() == [])
seen = []
with tempfile.TemporaryDirectory() as td:
    pkg, dest = Path(td) / "pkg", Path(td) / "dest"
    pkg.mkdir()
    dest.mkdir()
    for n in inst.ENV_FILES:
        (pkg / n).write_text("x", encoding="utf-8")
        (dest / n).write_text("x", encoding="utf-8")
    py = inst.env_python(dest)
    py.parent.mkdir(parents=True)
    py.write_text("", encoding="utf-8")
    inst.find_uv = lambda: "uv"
    inst.subprocess.run = lambda cmd, *a, **k: (seen.append(cmd), subprocess.CompletedProcess(cmd, 0))[1]
    status = inst.tooling_env_status(pkg, dest, extras=["gpu"])
    check("the status check syncs with the machine's extras", status == "current" and seen
          and seen[-1][:6] == ["uv", "sync", "--locked", "--check", "--quiet", "--extra"], seen[-1:])
    inst.build_tooling_env(pkg, dest, extras=["gpu"])
    check("the build syncs with them too", "--extra" in seen[-1] and "gpu" in seen[-1], seen[-1:])
    inst.build_tooling_env(pkg, dest, extras=[])
    check("no GPU: the build asks for no extra", "--extra" not in seen[-1], seen[-1:])
inst.shutil.which, inst.subprocess.run = real_which, real_run

check("wiki-transcribe.py and wiki-fetch-tweet.js are in the install list",
      "wiki-transcribe.py" in inst.TRAVEL_SCRIPTS and "wiki-fetch-tweet.js" in inst.TRAVEL_SCRIPTS)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
