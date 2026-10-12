---
title: "skill-suggestions/ — folder purpose"
date: {{DATE}}
source_url: internal://auto-maintained/skill-suggestions-readme
raw_path: (none — self-authored)
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: {{DATE}}
review_after: {{REVIEW_AFTER}}
tags: [folder-readme, skill-suggestions, navigation]
---

# skill-suggestions/

One page per improver pass over the skill suggestions other projects sent to this library, named `<date>-<sender> skill suggestions` (`mixed` when a pass took suggestions from several notebooks). A skill suggestion is a five-line note (`Skill`, `Seen in`, `Issue`, `Fix`, `Applies to`; four lines before 2026-10-12) a run leaves when a library skill, agent or workflow got in its way. Each page lists every suggestion in its pass with where it applies, Mark's decision and the task it became, and the earlier fixes the pass checked with whether each held, so "what have projects told us about check-freeze?" is a search here.

The files themselves sit unchanged, each with its decision line (and an `Outcome` line once a later pass has judged an accepted fix), in `raw/skill-suggestions/<pass>/`, beside the pass's `proposals.md` (the proposals as they were put to Mark). Suggestions still waiting for a pass are in `_inbox/skill-suggestions/received/`.

Pages are written by the `improving-skills-from-suggestions` skill (`suggestions.py summary`) and filed with `wiki-update.py`. A later pass never edits an earlier page: it gets its own.
