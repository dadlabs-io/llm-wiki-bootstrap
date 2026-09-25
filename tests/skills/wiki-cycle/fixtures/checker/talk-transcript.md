---
title: "Keeping an agent's context small (test talk)"
source_url: https://www.youtube.com/watch?v=skilltest01
video_id: skilltest01
channel: Skilltest Conf
duration_seconds: 1260
duration: 21m
type: youtube-transcript
word_count: 520
---

# Keeping an agent's context small (test talk) — Transcript

**Channel**: Skilltest Conf
**Duration**: 21m

---

## Transcript

so today I want to walk through nine techniques we use to keep an agent's context small
and um the first one is the obvious one trim tool results before they go back into the window
keep the part the step asked for and drop the rest
the second technique is summarise old turns once a conversation passes a budget
the third is retrieve instead of paste so the agent searches the notes it needs rather than carrying everything
the fourth technique is a stable prompt prefix so caching makes the repeated part cheap
the fifth is splitting work across sub agents each with a narrow brief and its own window
the sixth technique is writing a short handoff file at the end of a session instead of keeping the transcript
the seventh is pruning memories that nobody has read in a month
the eighth technique is capping each tool's output at a fixed size and telling the model where the full result lives
and in our tests these together cut token use by about a third on long tasks
not more than that a third
okay and the ninth technique the one people skip is checkpoint rollback
you snapshot the context before a risky step and when the step fails you restore the snapshot
instead of letting the failed attempt and all its error output stay in the window
we saw that single change stop most of the runaway loops we had
so that's the nine thanks
