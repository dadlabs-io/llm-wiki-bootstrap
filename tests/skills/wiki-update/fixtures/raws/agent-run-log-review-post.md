---
title: What a weekly read of our agent run logs found in six weeks
date: 2026-09-21
source_url: https://medium.com/@priya-raman-eng/skilltest-weekly-agent-run-log-review
ingested_by: skilltest
---

# What a weekly read of our agent run logs found in six weeks

I am Priya Raman. I run the platform team that operates our coding agents, and I wrote this up because I changed how we look at their runs and then counted what happened.

Until August we only looked at a run when someone complained. Since 4 August I read, every Monday, a sample of sixty runs from the previous week: twenty that ended in a failure, twenty that ended with a user correction, and twenty chosen at random. For each one I wrote one line naming the step where the run went wrong, then grouped the lines.

Over six weeks that was 360 runs and 214 lines. Three groups held 71 percent of them: the agent reading a stale file after another step had changed it (88 lines), a tool result cut off at its size limit with no sign that it was cut (41 lines), and a retry that repeated the same failing call (23 lines).

We fixed those three in order. After the stale-file fix, the share of sampled runs that ended in a failure fell from 31 percent to 22 percent. After the truncation marker was added, it fell to 17 percent. The retry fix moved it by about one point, which is inside the week-to-week noise I saw before I changed anything (plus or minus three points).

What I would not claim: the sample is from one team, on one set of tools, and I was the only reader, so another reader might group the lines differently. I did not run a control team. The numbers above are the ones from our own run store, and I can share the grouping sheet.

If you want to try it, the cheapest version is one hour on Monday and a spreadsheet with two columns: the run id and the step that went wrong.
