# Is the cut at 20 right? (17 real queries, k=40)

Run `20260922-142336`, judge `sonnet`, scope `agentic-design`, seed 1.
Queries come from the search log; entries were shuffled before judging.

| Band | Entries judged | Judged useful | Rate |
|---|---|---|---|
| ranks 1-20 | 340 | 119 | 35% |
| ranks 21+ | 332 | 48 | 14% |

- **14 of 17 queries** had at least one useful entry below rank 20 (median 1.0 per query).
- Spend: $4.40.

## What was found below rank 20

**security review hooks sandboxing AI agent code**
- #21 (0.570) The Next Evolution of the Agents SDK — Sandbox-Native Harness With AGENTS.md, Skills, MCP, apply_patch, and shell as Fir — native sandbox execution built into agent SDK
- #24 (0.550) Claude Code Hooks — Canonical Event Reference — canonical technical reference for hooks mechanism
- #25 (0.550) APM — Agent Package Manager (Microsoft) — security plane for agent config supply chain
- #26 (0.550) We Let an AI Agent Execute Bash and Lived to Talk About It (Sarah Sanders, PostHog, AI Engineer 2026) — deterministic sandboxing/deny-by-default for shell-capable agent
- #27 (0.550) awesome-security-hardening — Curated Hardening Guides, Benchmarks and Audit Tools (decalage2) — OS-level hardening reference for agent runtime sandboxing
- #28 (0.550) OpenClaw Promised a Self-Hosted AI Assistant — But Hermes Agent Is the One That Delivers It — contrasts broken vs designed-in agent security/isolation
- #32 (0.520) Codex Security (Formerly Aardvark) — Threat-Model-Driven Application Security Agent With Validation in Sandboxes (OpenAI — threat-model-driven security agent with sandboxed validation
- #34 (0.510) Gabriel Cohen (NanoClaw) — Minimal Code, Maximum Isolation — container-per-agent isolation architecture, concrete design
- #35 (0.500) security-guidance — Anthropic's official three-layer security review plugin for Claude Code: regex warnings on every edi — hook-shaped three-layer security review plugin, core match
- #36 (0.500) Building an Agentic Security Pipeline That Finds, Proves, and Patches Vulnerabilities — a From-Scratch 7B-Model Build Wi — open-model vulnerability-finding pipeline with sandbox proof
- #37 (0.490) Why, and how you need to sandbox AI-Generated Code? — Harshil Agrawal, Cloudflare — core framework: isolates vs containers for agent code
- #39 (0.470) Building an Agentic PR Reviewer with Antigravity SDK — agentic security-review architecture with isolated reviewer

**Claude Code auto mode permission classifier**
- #21 (0.490) Boris Cherny's Opus 4.7 Setup — As Reported by XDA (Faisal, 2026-05-05) — notes auto mode's classifier gating and tier availability

**Skills API Files API Claude Platform**
- #26 (0.560) Anthropic Cookbook — Managed Agents Data Analyst Agent — Shows Files API calls in practice on Claude Platform

**Best-Practices Candidate Concepts — Integration Backlog  --json**
- #25 (0.560) Concept Gaps — Things Mentioned, Not Yet Covered — Sibling tracker; defines this backlog's scope boundary
- #26 (0.550) Best-Practices Candidate Concepts — Integration Backlog — Exact match — this is the tracker itself

**You Only Have Weeks Left to Vibe Code (Michal Malewicz, Medium, 2026-06-29) Mich**
- #39 (0.020) Agentic Engineering Patterns (Simon Willison) — Master Practitioner Guide — Defines vibe coding vs agentic engineering vocabulary

**Mem0 Zep LongMemEval LoCoMo benchmark agent memory**
- #22 (0.610) MRAgent: Memory is Reconstructed, Not Retrieved — Graph Memory for LLM Agents (Ji et al., 2026) — New graph-memory system beats baselines on both benchmarks
- #28 (0.550) Memori — SQL-Native Agent Memory Infrastructure — SQL-native memory system reports LoCoMo accuracy number
- #30 (0.520) Anatomy of Agentic Memory — Taxonomy and Empirical Analysis — Critiques benchmark validity/cost across memory systems
- #32 (0.500) `mem0ai/mem0` — Intelligent Memory Layer for AI Agents — Mem0 repo page: adoption, claims, LOCOMO accuracy figures
- #33 (0.490) State of AI Agent Memory 2026 — Mem0 cross-vendor benchmark synthesis — Mem0's own synthesis contrasting LOCOMO vs LongMemEval numbers
- #34 (0.470) LOCOMO — Evaluating Very Long-Term Conversational Memory — Canonical LoCoMo benchmark paper entry, directly on-topic

**dynamic workflows parallel background subagent scheduling**
- #21 (0.370) ralphex (umputun) — Autonomous Plan-Driven Claude Code Orchestrator With Multi-Phase Review Pipeline — Autonomous background orchestrator with worktree-isolated parallel plans
- #24 (0.340) Synapse AI — Deterministic-DAG Multi-Agent Orchestration Platform with a Self-Hosted AI Builder (synapseorch-ai, 2026) — Deterministic DAG orchestrator, contrasts dynamic workflows
- #28 (0.130) Anthropic — How We Built Our Multi-Agent Research System — Foundational lead+parallel-subagent research architecture with numbers
- #30 (0.070) Microsoft Agent Framework at BUILD 2026 — Agent Harness, CodeAct, Handoff orchestration details

**managed agents Managed Deep Agents LangChain**
- #33 (0.500) Claude Managed Agents — Anthropic's Agent Infrastructure — Builder-oriented analysis of Managed Agents, distinct from news
- #36 (0.470) The Runtime Behind Production Deep Agents — Harness vs Runtime, and the Production Primitive Map (Runkle & Trivedy, Lang — Runtime/harness primitive map for production Deep Agents

**Building a Context Pruning Pipeline for Long-Running Agents (Machine Learning Ma**
- #21 (0.550) Building a Context Pruning Pipeline for Long-Running Agents (Machine Learning Mastery, 2026) — Exact target article describing the pruning pipeline itself
- #22 (0.530) Escaping the Context Bottleneck (ContextCurator) — RL-trained context curator prunes noise while preserving anchors
- #23 (0.510) Context vs. Memory Engineering in Agentic AI Systems — Defines context vs memory engineering boundary relevant to pruning
- #24 (0.510) Chroma Context-1 — Training a Self-Editing Search Agent — Self-editing search agent with active prune_chunks tool
- #26 (0.500) Lance Martin on High Signal - Agent Harness, Reduce/Offload/Isolate, and the Bitter Lesson at the Application Layer — Reduce/Offload/Isolate triad and harness-bottleneck test framework
- #27 (0.500) GenericAgent — Context Information Density Maximization — Truncation+compression layer architecture, alternative pruning approach
- #28 (0.490) Context Management for Deep Agents (Curme & Daugherty, LangChain 2026-01-28) — Threshold-triggered offloading and summarization techniques for deep agents
- #29 (0.490) Less Context, Better Agents — Recency Pruning + Summarization for Tool-Using Enterprise Agents (Lodha, Pahlavikhah Varno — Controlled ablation proving recency pruning plus summarization works
- #30 (0.470) Shell + Skills + Compaction: Tips for Long-Running Agents (OpenAI Developers, 2026) — Compaction-as-default primitive specifically for long-running agents
- #32 (0.430) LangChain — Context Engineering for Agents (Lance Martin) — Foundational context engineering strategies frame pruning's purpose
- #33 (0.420) Mage: Memory as Execution-State Management for Long-Horizon Agents (Chen et al., 2026) — Tree-based execution-state management for long-horizon tasks
- #34 (0.360) Optimizing AI Agent Memory — Tiered Context and Aggressive Compaction — Practical tiered-context plus aggressive compaction recipe

**workflows as config files vs workflows as code orchestration debate**
- #21 (0.050) Gabriel Cohen (NanoClaw) — Minimal Code, Maximum Isolation — Explicit no-config-file, minimal-code counter-philosophy example

**scheduled repository reviewer resumable session schema validated agent**
- #23 (0.100) Build Long-Running AI Agents That Pause, Resume, and Never Lose Context with ADK (Saboo + Dong, Google Developers Blog 2 — Google ADK recipe for pausing/resuming long-running agents
- #40 (0.050) Long-Running Agents Beyond Prompt Engineering — Durable event-sourced execution and validation gates for agents

**Foundry hosted agent deployment CodeAct sandbox**
- #26 (0.070) Microsoft Agent Framework 1.0 — TechCommunity Vendor-Primary — Agent Framework 1.0 GA that Foundry features build on

**Claude Code memory compared to custom memory system**
- #28 (0.500) Claude Memory Compiler -- LLM Personal Knowledge Base — Concrete custom memory compiler built on Claude Code
- #35 (0.460) I Added Claude Code's Memory to My Workflows and My Automation Became Effortless — Native memory inherited via CLI vs manual restuffing

**agents write code to call tools instead of individual tool calls MCP code execut**
- #35 (0.360) AI Agent Tool Design: What Works and What Doesn't (Bala Priya C, MachineLearningMastery 2026) — names loading-all-tools-every-turn as a failure mode

**Read:** borderline — a useful entry turns up below the cut often enough to discuss.
