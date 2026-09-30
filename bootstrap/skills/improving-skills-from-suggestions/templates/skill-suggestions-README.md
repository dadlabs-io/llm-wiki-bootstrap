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

One page per improver pass over the skill suggestions other projects sent to this library, named `<date>-<sender> skill suggestions` (`mixed` when a pass took suggestions from several notebooks). A skill suggestion is a four-line note (`Skill`, `Seen in`, `Issue`, `Fix`) a run leaves when a library skill, agent or workflow got in its way. Each page lists every suggestion in its pass with Mark's decision and the task it became, so "what have projects told us about check-freeze?" is a search here.

The files themselves sit unchanged, each with its decision line, in `raw/skill-suggestions/<pass>/`, beside the pass's `proposals.md` (the proposals as they were put to Mark). Suggestions still waiting for a pass are in `_inbox/skill-suggestions/received/`.

Pages are written by the `improving-skills-from-suggestions` skill (`suggestions.py summary`) and filed with `wiki-update.py`. A later pass never edits an earlier page: it gets its own.
