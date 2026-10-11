## At a glance

<!-- wiki-tasks next-id: 6 -->
Every task, one line each, by owner. A number is never reused. "waiting" is a status: the task stays with its owner. A task leaves this list only when the user says so: a task the user calls done is removed, and one the session finished is marked `done` until the user agrees to remove it. A task's details go in Task details below, under its number.

### Mark

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 1 | Pick a domain registrar for the docs site | to do | yours |
| 4 | Review the onboarding guide draft | waiting | the draft from main |

### main

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 2 | Write the onboarding guide draft | doing | section 3 |
| 3 | Clean up the old build scripts | to do |  |

### Unassigned

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 5 | Decide whether to add a dark theme | parked | an idea |

## Task details

### #1: Pick a domain registrar for the docs site

Compare Gandi and Porkbun on renewal price and DNSSEC; the budget ceiling is 30 euros a year.

### #3: Clean up the old build scripts

Keep make-release.sh; the three deploy-*.sh files are unused since the CI move.

## NOW
Writing the onboarding guide (task 2).

## QUEUE
2. Onboarding guide: sections 1 and 2 are done; section 3 covers the install steps.
