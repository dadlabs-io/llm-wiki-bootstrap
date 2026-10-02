#!/usr/bin/env python3
"""A machine with no GPU searches by keyword only, and never loads a qmd model (task #63). Never shipped.

    python tests/scripts/test_search_mode.py    # exit 0 = every check passed

qmd's full search (`qmd query`) runs three models. With no GPU they fall back to the CPU and take every
core: on 2026-10-02 one full search on the CPU used ~9,900 CPU-seconds and hung the laptop without
finishing. So each machine has a search mode in ~/.claude/wiki-config.json: `full` (the GPU search, as
before) or `keyword` (`qmd search`, qmd's keyword index, no model). The installer sets it from the GPU
check and never switches a machine on its own; `wiki-qmd-query.py --set-mode full` switches once a GPU
is there. These checks run the search helper in-process with qmd itself replaced by a recorder, so no
model and no real search ever runs.
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

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tmp = Path(tempfile.mkdtemp(prefix="search-mode-"))
cfg_path = tmp / "wiki-config.json"
os.environ["WIKI_GLOBAL_CONFIG"] = str(cfg_path)
os.environ["WIKI_QMD_SLOT_DIR"] = str(tmp / "slots")
os.environ.pop("WIKI_SEARCH_MODE", None)


def write_cfg(data: dict):
    cfg_path.write_text(json.dumps(data), encoding="utf-8")


def read_cfg() -> dict:
    return json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}


# ---------- the setting (_wiki_config) ----------
import _wiki_config as wc  # noqa: E402

check("_wiki_config has search_mode / set_search_mode", hasattr(wc, "search_mode") and hasattr(wc, "set_search_mode"))
if hasattr(wc, "search_mode"):
    if cfg_path.exists():
        cfg_path.unlink()
    check("no setting reads as full (machines installed before the setting existed)", wc.search_mode() == "full",
          wc.search_mode())
    write_cfg({"search_mode": "keyword", "registry": "x.json"})
    check("search_mode: keyword reads as keyword", wc.search_mode() == "keyword", wc.search_mode())
    write_cfg({"search_mode": "lite"})
    check("an unknown value reads as keyword (the side that never loads a model)", wc.search_mode() == "keyword",
          wc.search_mode())
    os.environ["WIKI_SEARCH_MODE"] = "full"
    check("WIKI_SEARCH_MODE overrides the file", wc.search_mode() == "full", wc.search_mode())
    os.environ.pop("WIKI_SEARCH_MODE")
    write_cfg({"search_mode": "keyword", "registry": "x.json", "bootstrap_source": "C:/b"})
    wc.set_search_mode("full")
    after = read_cfg()
    check("set_search_mode writes the mode", after.get("search_mode") == "full", after)
    check("set_search_mode keeps the other keys", after.get("registry") == "x.json" and after.get("bootstrap_source") == "C:/b", after)
    try:
        wc.set_search_mode("lite")
        check("set_search_mode refuses an unknown mode", False)
    except ValueError:
        check("set_search_mode refuses an unknown mode", True)

# ---------- the search helper ----------
q = load("wqq", "wiki-qmd-query.py")
calls: list[list[str]] = []


def fake_run_qmd(argv, timeout):
    calls.append(list(argv))
    return 0, "[]\n" if "--json" in argv else "", "Reranking 7 chunks\n"


q.run_qmd = fake_run_qmd
q.collections = lambda: {}


def run_main(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    old = sys.argv
    sys.argv = ["wiki-qmd-query.py", *argv]
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = q.main()
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else 2
    finally:
        sys.argv = old
    return rc, out.getvalue(), err.getvalue()


check("parse_gpu_inspect exists", hasattr(q, "parse_gpu_inspect"))
if hasattr(q, "parse_gpu_inspect"):
    check("CUDA available -> cuda", q.parse_gpu_inspect("CUDA: available\nVulkan: available\n") == "cuda")
    check("Metal available -> metal (a Mac)", q.parse_gpu_inspect("Metal: available\n") == "metal")
    check("Vulkan only -> no GPU (Vulkan is the backend that hung)",
          q.parse_gpu_inspect("CUDA: not available\nVulkan: available\n") is None)
    check("no output -> no GPU", q.parse_gpu_inspect("") is None)

# keyword machine: a search runs `qmd search`, never a model
write_cfg({"search_mode": "keyword"})
calls.clear()
rc, out, err = run_main(["--all-notebooks", "tiered context loading", "--json"])
check("keyword: the search exits 0", rc == 0, err.strip()[-300:])
check("keyword: qmd was called once", len(calls) == 1, calls)
check("keyword: it ran `qmd search`", bool(calls) and calls[0][0] == "search", calls)
check("keyword: never `qmd query`, `vsearch` or `embed`", not any(c[0] in ("query", "vsearch", "embed") for c in calls), calls)
check("keyword: no reranker flag (-C)", bool(calls) and "-C" not in calls[0], calls)
check("keyword: the status line says keyword", "keyword" in err.lower(), err.strip()[-300:])

# keyword machine: preflight passes without a GPU check
q.gpu_backend = lambda: (_ for _ in ()).throw(AssertionError("GPU check ran on a keyword machine"))
rc, out, err = run_main(["--preflight"])
check("keyword: --preflight exits 0 without a GPU check", rc == 0, err.strip()[-300:])
check("keyword: --preflight names the mode", "keyword" in err.lower(), err.strip()[-300:])

# keyword machine: the depth check has no reranker to measure
calls.clear()
rc, out, err = run_main(["--depth-check", "--notebook", "llm-wiki-bootstrap"])
check("keyword: --depth-check exits 2 (nothing measured) and says why", rc == 2 and "keyword" in err.lower(),
      (rc, err.strip()[-200:]))
check("keyword: --depth-check runs no search", not calls, calls)

# full machine: unchanged, the GPU search
write_cfg({"search_mode": "full"})
calls.clear()
rc, out, err = run_main(["--all-notebooks", "tiered context loading"])
check("full: the search exits 0", rc == 0, err.strip()[-300:])
check("full: it ran `qmd query`", bool(calls) and calls[0][0] == "query", calls)
check("full: with the reranker ceiling -C", bool(calls) and "-C" in calls[0], calls)

q.gpu_backend = lambda: (None, "CUDA: not available")
rc, out, err = run_main(["--preflight"])
check("full: --preflight fails with no GPU", rc == 2, err.strip()[-200:])
q.gpu_backend = lambda: ("metal", "Metal: available")
rc, out, err = run_main(["--preflight"])
check("full: --preflight passes on Metal", rc == 0, err.strip()[-200:])

# switching
write_cfg({"search_mode": "keyword", "registry": "x.json"})
q.gpu_backend = lambda: (None, "CUDA: not available")
rc, out, err = run_main(["--set-mode", "full"])
check("--set-mode full is refused with no GPU, saying so", rc == 2 and "gpu" in err.lower(),
      err.strip()[-200:])
check("... and the setting stays keyword", read_cfg().get("search_mode") == "keyword", read_cfg())
q.gpu_backend = lambda: ("cuda", "CUDA: available")
rc, out, err = run_main(["--set-mode", "full"])
check("--set-mode full works once the GPU check passes", rc == 0 and read_cfg().get("search_mode") == "full",
      (rc, read_cfg(), err.strip()[-200:]))
check("... keeps the other keys", read_cfg().get("registry") == "x.json", read_cfg())
check("... and says to build the meaning index (qmd embed)", rc == 0 and "qmd embed" in (out + err), (out + err)[-300:])
q.gpu_backend = lambda: (_ for _ in ()).throw(AssertionError("GPU check ran for --set-mode keyword"))
rc, out, err = run_main(["--set-mode", "keyword"])
check("--set-mode keyword needs no GPU check", rc == 0 and read_cfg().get("search_mode") == "keyword",
      (rc, read_cfg(), err.strip()[-200:]))

# ---------- the installer: sets it once, never switches on its own ----------
it = load("it", "_install_tooling.py")
check("_install_tooling has configure_search_mode", hasattr(it, "configure_search_mode"))
if hasattr(it, "configure_search_mode"):
    gpu = lambda: ("cuda", "CUDA: available")  # noqa: E731
    nogpu = lambda: (None, "CUDA: not available")  # noqa: E731

    write_cfg({"registry": "x.json"})
    msg = it.configure_search_mode(gpu, config_path=cfg_path)
    check("install, no setting, GPU -> full", read_cfg().get("search_mode") == "full", (msg, read_cfg()))
    check("... keeps the other keys", read_cfg().get("registry") == "x.json", read_cfg())

    write_cfg({})
    msg = it.configure_search_mode(nogpu, config_path=cfg_path)
    check("install, no setting, no GPU -> keyword", read_cfg().get("search_mode") == "keyword", (msg, read_cfg()))
    check("... and says how to switch later", "--set-mode full" in msg, msg)

    write_cfg({"search_mode": "keyword"})
    msg = it.configure_search_mode(gpu, config_path=cfg_path)
    check("refresh, keyword, a GPU now -> stays keyword", read_cfg().get("search_mode") == "keyword", (msg, read_cfg()))
    check("... and says a GPU is available and how to switch", "--set-mode full" in msg and "gpu" in msg.lower(), msg)

    write_cfg({"search_mode": "full"})
    msg = it.configure_search_mode(nogpu, config_path=cfg_path)
    check("refresh, full, GPU check fails -> stays full", read_cfg().get("search_mode") == "full", (msg, read_cfg()))
    check("... and warns, naming --set-mode keyword", "--set-mode keyword" in msg, msg)

    write_cfg({"search_mode": "full"})
    msg = it.configure_search_mode(gpu, config_path=cfg_path)
    check("refresh, full, GPU -> unchanged", read_cfg() == {"search_mode": "full"} and "unchanged" in msg, (msg, read_cfg()))

    write_cfg({})
    msg = it.configure_search_mode(nogpu, config_path=cfg_path, dry_run=True)
    check("dry run writes nothing", read_cfg() == {}, (msg, read_cfg()))

# ---------- the lint's re-index advice ----------
lint = load("lint", "wiki-lint-mechanical.py")
check("the lint has reindex_command", hasattr(lint, "reindex_command"))
if hasattr(lint, "reindex_command"):
    write_cfg({"search_mode": "keyword"})
    check("keyword: the lint says `qmd update`, not `qmd embed`",
          "qmd update" in lint.reindex_command() and "embed" not in lint.reindex_command(), lint.reindex_command())
    write_cfg({"search_mode": "full"})
    check("full: the lint says `qmd update && qmd embed`", lint.reindex_command() == "qmd update && qmd embed",
          lint.reindex_command())

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
