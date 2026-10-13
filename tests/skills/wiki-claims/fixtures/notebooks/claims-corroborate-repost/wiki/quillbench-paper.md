---
title: "Quillbench: a benchmark for tool-call planning"
date: 2026-08-20
source_url: "https://arxiv.example.org/abs/2610.04417"
tier: 1
confidence: high
tags: [quillbench, benchmark, planning]
---

# Quillbench: a benchmark for tool-call planning

## TL;DR
Quillbench scores how well a model plans a sequence of tool calls. The paper reports that the planner model Marlin-7B reached 63.8% task accuracy on Quillbench.

## Benchmark
Quillbench holds 1,200 multi-step tasks, each needing between three and nine tool calls. A task counts as solved only when every call is correct and in order.

## Results
Marlin-7B reached 63.8% task accuracy on Quillbench. The strongest baseline, a prompted general model, reached 51.2% on the same tasks.

## Limitations
The tasks are in English only, and each model was run once.
