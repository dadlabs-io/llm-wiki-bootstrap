---
title: "Chunking notes for design documents"
date: 2026-08-20
source_url: "https://example.com/chunking-notes"
tier: 2
confidence: high
tags: [chunking, documents, retrieval]
---

# Chunking notes for design documents

## TL;DR
Chunks of 512 tokens with a 64-token overlap worked best for our design documents.

## Setup
We compared chunk sizes of 256, 512 and 1024 tokens on 120 design documents. Two reviewers rated answer relevance on a five-point scale.

## Results
512-token chunks gave the best answer relevance, rated 4.1 out of 5. A 64-token overlap reduced answers that missed text sitting on a chunk boundary.
