---
title: "Citation Guard evaluation on 400 test questions"
date: 2026-09-05
source_url: "https://example.com/citation-guard-evaluation"
tier: 2
confidence: medium
tags: [citations, evaluation, grounding]
---

# Citation Guard evaluation on 400 test questions

## TL;DR
Citation Guard eliminates hallucinated citations in generated answers.

## Method
Citation Guard checks every citation in a draft answer against the retrieved documents and removes any citation it cannot match.

## Results
On 400 test questions, 18.2% of baseline answers contained at least one hallucinated citation. With Citation Guard, 12.6% did, a 31% relative reduction. The guard added a median of 90 ms per answer.

## Limits
The guard cannot catch a citation that points to a real document that does not support the claim.
