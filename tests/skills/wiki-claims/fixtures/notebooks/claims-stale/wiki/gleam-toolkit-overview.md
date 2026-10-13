---
title: "Gleam tracing toolkit overview"
date: 2026-03-04
source_url: "https://example.com/gleam-overview"
tier: 2
confidence: medium
tags: [gleam, tracing, observability]
---

# Gleam tracing toolkit overview

## TL;DR
Gleam is an open-source tracing toolkit for agent runs. The current release is 2.1, which ships 12 exporters.

## What it does
Gleam records every model call and tool call of an agent run as a span and groups the spans into one trace per run.

## Releases
The current release is Gleam 2.1, published in March 2026. It ships 12 exporters, including OTLP, Jaeger and a JSON-lines file exporter.
