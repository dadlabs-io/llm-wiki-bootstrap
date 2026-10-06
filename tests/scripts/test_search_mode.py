#!/usr/bin/env python3
"""A machine with no GPU searches by keyword only, and never loads a qmd model (task #63); every machine
runs the word-pair keyword search (task #64). Never shipped.

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


def _row(name: str, i: int = 0) -> dict:
    return {"docid": f"#{i:06d}", "score": 0.5, "file": f"qmd://C:/nb/wiki/{name}.md", "line": 1,
            "title": name, "snippet": f"about {name}"}


def fake_run_qmd(argv, timeout):
    """qmd, recorded. `search <q>`: 20 rows of its own plus five shared by every search;
    `query`: the full search's three rows (shared-0 among them), as JSON or qmd's text layout."""
    calls.append(list(argv))
    if argv[0] == "search":
        slug = argv[1].replace(" ", "_")
        rows = [_row(f"shared-{i}", i) for i in range(5)] + [_row(f"{slug}-{i}", i) for i in range(20)]
        return 0, json.dumps(rows), ""
    full = [_row("shared-0"), _row("full-1", 1), _row("full-2", 2)]
    if "--json" in argv:
        return 0, json.dumps(full), "Reranking 7 chunks\n"
    return 0, q.render_text(full), "Reranking 7 chunks\n"


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
check("keyword: every qmd call is `search`", bool(calls) and all(c[0] == "search" for c in calls), calls)
check("keyword: never `qmd query`, `vsearch` or `embed`", not any(c[0] in ("query", "vsearch", "embed") for c in calls), calls)
check("keyword: searched the key words together and in every pair",
      sorted(c[1] for c in calls) == sorted(["tiered context loading", "tiered context", "tiered loading",
                                             "context loading"]), sorted(c[1] for c in calls))
check("keyword: no reranker flag (-C)", bool(calls) and not any("-C" in c for c in calls), calls)
try:
    kw_rows = json.loads(out)
except ValueError:
    kw_rows = []
check("keyword: JSON out, at most k=30 rows, each file once",
      0 < len(kw_rows) <= 30 and len({r["file"] for r in kw_rows}) == len(kw_rows), len(kw_rows))
check("keyword: an entry every search found ranks first (fused by rank)",
      bool(kw_rows) and kw_rows[0]["file"].endswith("shared-0.md"), kw_rows[:1])
check("keyword: the status line says keyword", "keyword" in err.lower(), err.strip()[-300:])
check("key_terms drops stop words and repeats",
      q.key_terms("Microsoft Agent Framework agent and workflow channels")
      == ["Microsoft", "Agent", "Framework", "workflow", "channels"],
      q.key_terms("Microsoft Agent Framework agent and workflow channels"))
long_q = "the quick brown fox and a lazy dog over the hill near river bank"
check("at most 8 key words: the whole + 28 pairs", len(q.keyword_queries(long_q)) == 29
      and q.key_terms(long_q)[-1] == "river", (len(q.keyword_queries(long_q)), q.key_terms(long_q)))
check("one or two key words: a single search", q.keyword_queries("tiered context") == ["tiered context"],
      q.keyword_queries("tiered context"))

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
check("full: then the word-pair keyword searches, all `search`",
      len(calls) == 5 and all(c[0] == "search" for c in calls[1:]), [c[:2] for c in calls])
check("full: text output adds the keyword finds under their own heading, after the full results",
      "## Also found by keyword search" in out and out.index("full-2") < out.index("## Also found by keyword search"),
      out[-300:])
calls.clear()
rc, out, err = run_main(["--all-notebooks", "tiered context loading", "--json"])
try:
    full_rows = json.loads(out)
except ValueError:
    full_rows = []
mine = [r for r in full_rows if r.get("found_by") == "full"]
extra = [r for r in full_rows if r.get("found_by") == "keyword"]
check("full JSON: the full search's own rows first, marked found_by full",
      [r["file"].rsplit("/", 1)[-1] for r in mine] == ["shared-0.md", "full-1.md", "full-2.md"]
      and full_rows[:3] == mine, [r.get("found_by") for r in full_rows[:4]])
check("full JSON: then at most 20 keyword finds, marked found_by keyword", 0 < len(extra) <= 20, len(extra))
check("full JSON: no keyword find repeats a full result",
      not ({r["file"] for r in extra} & {r["file"] for r in mine}), [r["file"] for r in extra][:3])
check("full: the status line counts the keyword finds", "found only by keyword search" in err, err.strip()[-300:])
calls.clear()
rc, out, err = run_main(["--all-notebooks", "tiered context loading", "--json", "--keyword-extra", "0"])
check("full: --keyword-extra 0 runs no keyword search", rc == 0 and len(calls) == 1 and calls[0][0] == "query",
      [c[:2] for c in calls])

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

# ---------- --reindex: update the index, then embed on a full machine only (task #81 P1) ----------
embed_saw_free_slot: list[bool] = []
_plain_fake = q.run_qmd


def reindex_fake(argv, timeout):
    if argv and argv[0] == "embed":
        probe = q.Slot(q.slot_dir() / "slot-1.lock")
        free = probe.try_acquire()
        if free:
            probe.release()
        embed_saw_free_slot.append(free)
        calls.append(list(argv))
        return 0, "", "Done! Embedded 12 chunks from 3 documents in 2s\n"
    if argv and argv[0] == "update":
        calls.append(list(argv))
        return 0, "Updated 3 files\n", ""
    return _plain_fake(argv, timeout)


q.run_qmd = reindex_fake
write_cfg({"search_mode": "keyword"})
calls.clear()
rc, out, err = run_main(["--reindex"])
check("reindex, keyword: exits 0", rc == 0, (rc, err.strip()[-200:]))
check("reindex, keyword: runs `qmd update` only, never `embed`", calls == [["update"]], calls)
write_cfg({"search_mode": "full"})
calls.clear()
embed_saw_free_slot.clear()
rc, out, err = run_main(["--reindex"])
check("reindex, full: exits 0", rc == 0, (rc, err.strip()[-200:]))
check("reindex, full: `qmd update` then `qmd embed`", calls == [["update"], ["embed"]], calls)
check("reindex, full: every GPU slot is held while it embeds", embed_saw_free_slot == [False], embed_saw_free_slot)
check("reindex, full: reports what it embedded", "Embedded 12 chunks" in (out + err), (out + err)[-200:])
check("reindex: the slots are free again afterwards", q.acquire_slot(3, 0)[0] is not None)
q.run_qmd = lambda argv, timeout: (calls.append(list(argv)) or (1, "", "boom: index locked\n"))
calls.clear()
rc, out, err = run_main(["--reindex"])
check("reindex: a failed `qmd update` exits non-zero, says why, and does not embed",
      rc not in (0, None) and "boom" in err and calls == [["update"]], (rc, calls, err.strip()[-200:]))
q.run_qmd = lambda argv, timeout: (calls.append(list(argv)) or (None, "", ""))
calls.clear()
rc, out, err = run_main(["--reindex"])
check("reindex: a timeout exits 124", rc == 124, (rc, err.strip()[-200:]))
q.run_qmd = _plain_fake

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
