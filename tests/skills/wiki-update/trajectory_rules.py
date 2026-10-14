"""wiki-update's own read-first and never rules, as run checks (task #99; tests/skills/_trajectory.py).

Each rule quotes the SKILL.md line it tests. FILING is a call that files or stages an entry: not a
fetch, a slug lookup, a duplicate check or a re-gate. A search is the helper, its flags, then a
quoted term ("$t" in a loop counts): not --help, --preflight or another maintenance mode, not a
variable that holds the command, and not the script's name inside prose.
"""

FILING = r"wiki-update\.py(?![^\n]*--(fetch-only|slug-for|check-duplicate|regate))[^\n]*--tier\s+['\"]?[1-4]\b"
_FLAGS = r"(?:[ \t]+-[-\w]+(?:[ \t]+[^\s\"'|;&-][^\s\"'|;&]*)?)*[ \t]+[\"'$]"
SEARCH_NO_NOTEBOOK = r"wiki-qmd-query\.py(?![^\n]*--(notebook|help))" + _FLAGS
SEARCH_CUT = r"wiki-qmd-query\.py(?![^\n|;]*--(help|preflight|stats|reindex|depth-check|set-mode))[^\n|;]*(\|\s*(head|tail)\b|\s-k\s*['\"]?([0-9]|[12][0-9])\b)"


def rules(scope: str = "main") -> list[dict]:
    """The same rules for the session that files (wiki-update's suite) and for ingest workers
    (wiki-cycle's suite, scope "workers")."""
    shell = ["Bash", "PowerShell"]
    return [
        # eval-case-writer's rule (task #99, 2026-10-12), replacing "opened the tier rubric before setting
        # --tier": the fetch and the duplicate check now print the rubric, so either one, or a read of the
        # spec, puts it in front of the session. It sees commands, not their output (the writer's caveat)
        {"id": "rubric in front of the session before the first --tier filing", "kind": "run_before", "scope": scope,
         "rule": "the tier rubric and the confidence scale from the frontmatter spec are in front of the session before an entry's tier and confidence are chosen (printed by --fetch-only or --check-duplicate, or read from the spec)",
         "action": FILING, "tool": shell,
         "before": r"wiki-update\.py[^\n]*--(fetch-only|check-duplicate)|wiki-frontmatter-best-practices\.md"},
        {"id": "read fetchers.md before a special fetcher", "kind": "read_before", "scope": scope,
         "rule": "YouTube, PDFs (arXiv papers too), X, Medium, Instagram, pages rendered by JavaScript, a whole GitHub repo, and speech (reels, podcasts, video without captions): fetchers.md",
         "path": r"/fetchers\.md$",
         "action": r"wiki-fetch-(youtube|pdf|page|tweet|repo)|wiki-transcribe\.py", "tool": shell},
        {"id": "arXiv abs link fetched with wiki-fetch-pdf.py before filing", "kind": "run_before", "scope": scope,
         "in_suite": False, "off_until": "2026-11-14",
         "rule": "task #104: an arXiv abs link is filed from the paper's full text, fetched with wiki-fetch-pdf.py, not from the abstract page",
         "action": r"wiki-update\.py(?![^\n]*--(fetch-only|slug-for|check-duplicate|regate))[^\n]*arxiv\.org/abs/2307\.03172",
         "tool": shell,
         "before": r"wiki-fetch-pdf\.py[^\n]*arxiv\.org/abs/2307\.03172"},
        {"id": "whole GitHub repo fetched with wiki-fetch-repo.py before filing", "kind": "run_before", "scope": scope,
         "in_suite": False, "off_until": "2026-11-14",
         "rule": "task #107: a whole GitHub repository is fetched with wiki-fetch-repo.py (fetchers.md, Whole repository), not built by hand",
         "action": r"wiki-update\.py(?![^\n]*--(fetch-only|slug-for|check-duplicate|regate))[^\n]*github\.com/humanlayer/12-factor-agents",
         "tool": shell,
         "before": r"wiki-fetch-repo\.py[^\n]*github\.com/humanlayer/12-factor-agents"},
        # scored only (in_suite False): pasted text still reads as a breach (2026-10-12, 6 of 143)
        {"id": "read the raw before filing", "kind": "read_before", "scope": scope, "in_suite": False,
         "off_until": "2026-11-14",
         "rule": "Read the raw in full", "action": FILING, "tool": shell,
         "path_from_action": r"--raw-path[ \t=]+['\"]?([^\s'\"]+)",
         # a local file or pasted text: --fetch-only copies the session's source into raw/
         "also_from": r"wiki-update\.py(?=[^\n]*--fetch-only)[^\n]*--source[ \t=]+['\"]?(?!https?:)([^\s'\"]+)"},
        {"id": "every search names the notebook", "kind": "never", "scope": scope,
         "rule": "Always pass `--notebook`", "pattern": SEARCH_NO_NOTEBOOK, "tool": shell},
        {"id": "no search cut short (head, tail, -k under 30)", "kind": "never", "scope": scope,
         "rule": "never pipe it through `head` ... A `-k` below 30 or a filter of your own on the output is the same breach",
         "pattern": SEARCH_CUT, "tool": shell},
        {"id": "never re-files with --force", "kind": "never", "scope": scope,
         "rule": "never re-file it with `--force`, which makes a `-2` copy",
         "pattern": r"wiki-update\.py(?![^\n]*--revises)[^\n]*--force", "tool": shell},
        {"id": "never --partial-source on its own", "kind": "never", "scope": scope,
         "rule": "`--partial-source '<why>'` only on the user's word",
         "pattern": r"wiki-update\.py[^\n]*--partial-source", "tool": shell},
    ]


RULES = rules()
