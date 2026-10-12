arXiv:2610.04417v1 [cs.SE] 3 Oct 2026
https://arxiv.org/abs/2610.04417

# Does a hint file help coding agents? A nine-participant pilot

Authors: Tomas Ekwueme, Hana Lindqvist
Submitted to arXiv on 3 October 2026. This version has not been peer reviewed.

## Abstract

Coding agents are often given a short hint file that lists a repository's build command, test command and naming rules. We report a pilot in which nine developers each gave the same agent six small tasks, three with a hint file and three without, in random order. With a hint file, the agent passed the repository's tests on the first attempt in 31 of 54 task runs, against 22 of 54 without one. The difference is in the direction the common advice predicts, but nine participants on one repository is too few to rule out chance, and we did not repeat the study with a second agent or a second repository.

## 1. Setup

Participants were developers at two companies who volunteered. The repository was a small web service with a test suite that runs in under a minute. The hint file was written by the authors and held eleven lines. Tasks were fixed in advance: renaming a function, adding a field to a response, fixing a failing test, and three similar ones.

## 2. Results

First-attempt pass: 31 of 54 with a hint file, 22 of 54 without. The agent asked a clarifying question in 4 runs with a hint file and 15 without. Time to a passing result did not differ in a way we could separate from the spread between participants.

## 3. Limits

Nine participants, one repository, one agent version, tasks chosen by the authors. The participants knew which condition they were in. We report the pilot to help plan a larger study, not as evidence for a general effect.
