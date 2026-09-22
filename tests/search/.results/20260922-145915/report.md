# Is the cut at 20 right? (18 real queries, k=40)

Run `20260922-145915`, judge `sonnet`, scope `agentic-design`, seed 2.
Queries come from the search log; entries were shuffled before judging.

| Band | Entries judged | Judged useful | Rate |
|---|---|---|---|
| ranks 1-20 | 360 | 140 | 39% |
| ranks 21+ | 340 | 99 | 29% |

- **15 of 18 queries** had at least one useful entry below rank 20 (median 5.0 per query).
- **The single best entry sat below rank 20 in 3 of 18 queries** - the sharper question, since a useful-but-not-best entry in the tail costs little.
- Spend: $4.50.

## What was found below rank 20

**AI software factories Cole Medin**
- #23 (0.300) Cheap Code, Costly Judgment: A Case Study on Governable Agentic Software Engineering (Davis et al., 2026) — case study on governing agentic factory velocity
- #26 (0.280) The Multi-Agent Approach to Controllable Software Development (Itamar Friedman, Qodo — InfoQ/QCon) — Qodo's governance/arbiter multi-agent SDLC angle
- #30 (0.190) Human judgment doesn't leave the software factory, it relocates — when a harness stops being enough, one triage label as — defines software factory, where judgment relocates
- #40 (0.060) AI Auto-Work — Claude-Executor + Codex-Reviewer Full-Cycle Coding Workflow — concrete Claude+Codex full-cycle factory workflow

**Squad agent teams GitHub Copilot CLI Agent Framework**
- #22 (0.580) Paperclip — Open-Source Orchestration for Teams of AI Agents — Orchestration for agent teams, comparable to Squad's model
- #27 (0.560) Claude Agent Teams — Specialized Agents Under an Orchestrator — Defines Claude Agent Teams pattern, distinct from sub-agents
- #33 (0.490) Nate Herk — How to Build Claude Agent Teams Better Than 99% of People — Practitioner tutorial on Claude Agent Teams setup and monitoring
- #34 (0.470) Adoption and Impact of Command-Line AI Coding Agents — Microsoft's Early-2026 Claude Code + Copilot CLI Rollout — Field data on Copilot CLI adoption and impact
- #35 (0.470) Multica — Open-Source Managed-Agents Platform ("Agents as Teammates") — Agents-as-teammates platform, comparable team orchestration model

**Agentic CI/CD's Audit Compliance Gap — Recorded Execution as a First-Class Conce**
- #21 (0.090) Trustworthy Productivity: Securing AI-Accelerated Development (Sriram Madapusi Vasudevan, AWS) — provenance gates parallel Wald's compliance exceptions
- #32 (0.030) Praxen — Open-Source AI Agent Behavior Verification (Exabeam) — declared-vs-observed gap tool, audit-like verification

**agent swarms useful takeaways**
- #21 (0.490) Patterns and Problems in Emerging Multiagent Systems (Anthropic Frontier Red Team, 2026-08-13) — Red-team findings: coordination failures, collusion, no defaults
- #22 (0.480) How to Use OpenAI Codex Subagents Step by Step (Vladislav Guzey / proflead) — Concrete Codex subagent config and beginner traps
- #23 (0.470) Reinforcement Learning for LLM-based Multi-Agent Systems through Orchestration Traces (Zhang, 2026) — RL research gap: no training method for stopping decision
- #25 (0.460) How Anthropic Thinks About Agents, Workflows, and Tasks — Shelly Palmer on Barry Zhang's AIE Talk — Task/workflow/agent taxonomy, 'don't build agents for everything'
- #27 (0.440) How to Run Claude Code Agents in Parallel — Worktrees solve agent collision in parallel runs
- #28 (0.430) SwarmForge — Tmux-Based Agent Coordination — Tmux/worktree-based swarm coordination engineering pattern
- #30 (0.390) From Chaos to Choreography: Multi-Agent Orchestration Patterns That Actually Work — Sandipan Bhaumik — Distributed-systems patterns: circuit breakers, sagas, snapshots
- #32 (0.290) Kim et al. — Towards a Science of Scaling Agent Systems (arxiv 2512.08296) — Empirical: architecture-task alignment, decentralized error amplification
- #34 (0.280) Running Many Claude Code Sessions in Parallel — Human oversight challenge when running many agents
- #35 (0.270) Graph-of-Agents (GoA) — GoA insight: picking fewer agents beats using all
- #36 (0.270) Agency — A File-Based Kanban Orchestrator for Teams of Coding Agents (XDA) — Markdown-file coordination pattern for agent teams

**AGENTS.md trim instructions stronger model less scaffolding**
- #21 (0.430) HN — New Research Reassesses the Value of AGENTS.md Files for AI Coding (~30+ Comment Debate, Side B of Contested Pair,  — Stale context files finding, relevant to trimming
- #26 (0.360) My agent.md to Improve LLM-Assisted Code Quality (Fabien Sanglard, 2026) — Context dilution from over-accumulated instructions, needs trimming
- #29 (0.310) KDnuggets — 7 Practical Ways to Reduce Claude Code Token Usage (Mehreen, May 2026) — Lean CLAUDE.md tactic among token-reduction techniques

**how well do agents use test verification techniques**
- #23 (0.460) trailofbits/skills — a Claude Code plugin marketplace where every checker must be able to fail: validator self-test, art — meta-verification standard: every checker must be able to fail
- #28 (0.220) Benchmarking Opus 5 on SlopCodeBench (Dex Horthy, HumanLayer, 2026) — benchmark showing agents write more tests, more smells
- #29 (0.190) Nate Herk — This One Plugin Just 10x'd Claude Code (Superpowers by Jesse Vincent) — controlled experiment measuring verification methodology's real gains
- #30 (0.180) Long-Running Agents Beyond Prompt Engineering — harness-level deterministic validation gates outside the model
- #31 (0.160) Build Iterative Repair Loops with Codex — OpenAI Cookbook (2026) — official Review-Repair-Validate loop with convergence data
- #36 (0.090) Building an Agentic Security Pipeline That Finds, Proves, and Patches Vulnerabilities — a From-Scratch 7B-Model Build Wi — concrete proof-based verification example, crash-not-opinion standard
- #37 (0.090) From Tools to Workflows — Rethinking the SDLC for the AI Age — quantifies review-time verification logjam from AI code

**AI-native software development lifecycle**
- #21 (0.510) Cole Medin on Nate Herk's Podcast -- How to Use Claude Code Better Than 98% of People — plan/build/verify/evolve loop, practical heuristics
- #22 (0.500) Software Development After AI — Part I: The Fundamentals (Luís Soares, 2026) — practitioner restatement: coding speed was never bottleneck
- #23 (0.500) Why Software Requirements Get Easier in an AI Economy — requirements-stage argument, distinct lifecycle claim
- #24 (0.480) Cheap Code, Costly Judgment: A Case Study on Governable Agentic Software Engineering (Davis et al., 2026) — research-level governance-conversion theory, case study
- #26 (0.440) How to Stay in the Driver's Seat as AI Agents Take Over Coding (Matt Bentley) — concrete workflow prescription against over-leverage debt
- #27 (0.430) ACM TechBrief on Vibe Coding (The New Stack) — authoritative risk catalog for AI-driven dev process
- #28 (0.430) 9 Vibe Coding Patterns Stolen From Senior Engineers (Narender Beniwal) — concrete discipline patterns for AI-assisted coding
- #29 (0.420) Adoption and Impact of Command-Line AI Coding Agents — Microsoft's Early-2026 Claude Code + Copilot CLI Rollout — empirical adoption/output evidence, distinct data point
- #30 (0.420) How to Build a Software Factory with Claude Code — From Vibe Coding to Agentic Development — concrete five-layer software factory architecture
- #31 (0.390) Prompts to Loops: The New Jobs of the AI Age — prompt/context/loop engineering as evolving discipline
- #33 (0.280) Context as Code: Build-Time Governance in the Era of Infinite Syntax (Artur Huk, O'Reilly Radar, 2026) — context-compilation governance pattern before generation
- #36 (0.210) The New Age of Software Development — Rising Abstraction and the Developer/Product-Owner Merge — distinct angle: developer/product-owner roles merging
- #38 (0.150) Agentic Code Quality — quality moves from review into constraints around the agent: seven gate dimensions, Rauch's stake — quality gates around agents, build/test stage
- #40 (0.070) How to Build a Self-Improving Product — The Product-Map / Sense / Decide / Act / Learn Loop (Holmes, Department of Produ — distinct sense/decide/act/learn product loop architecture

**Claude Code prompt caching token cost context compact clear session hygiene**
- #21 (0.590) A Three-Pass Context Compiler for Coding Agents (Emmimal P Alexander, TDS, August 2026) — Three-tier context compiler technique for token reduction
- #27 (0.550) Maximizing the Value of Your Claude Code Sessions (Lydia Hallie, Anthropic, 2026-08-14) — Anthropic first-party checklist: clear, compact, session hygiene
- #28 (0.550) RAGs vs Agents — ByteByteGo Newsletter EP216 (May 2026) — Reverse-engineers Claude Code's own context-management cascade
- #31 (0.530) madeye/mcp-cli: sidecar-daemon + MCP bridge for fork/exec-free agent tools — Benchmarks show MCP bridge cutting cached input tokens
- #32 (0.520) KDnuggets — 7 Practical Ways to Reduce Claude Code Token Usage (Mehreen, May 2026) — Diagnostic framing plus distinct model-switching/subagent tactics
- #33 (0.520) Machine Learning Mastery — Effective Context Engineering for AI Agents: A Developer's Guide (Bala Priya C, April 28 2026 — General context-engineering framework covering prefix caching, budgeting
- #36 (0.500) Ida Silfverskiöld — Agentic AI: How to Save on Tokens — Broadest survey of caching mechanics across providers

**scheduled repository reviewer agent SDK recipe session resumption**
- #23 (0.070) OpenClaw v2026.9.3 — Agent-Owned Skill Workshop, Steerable Subagent Sessions, Repo-Backed Cloud Checkpoints — cloud checkpoints/steerable sessions, relevant resumption architecture comparison

**Hermes Agent Nous Research self-improving agent OpenClaw**
- #25 (0.550) Hermes Agent — Self-Improving Agent with Built-In Learning Loop — Hermes self-improving loop, unique delegation-pattern details
- #27 (0.520) State of Hermes Agent — April 2026 (Ecosystem Snapshot) — Unique Hermes growth stats vs OpenClaw velocity
- #29 (0.500) Hermes Agent (Nous Research) — Self-Improving Agent With Built-In Learning Loop, Migration Path From OpenClaw — Canonical Hermes/Nous/self-improving/OpenClaw-migration entry, most complete
- #30 (0.500) OpenClaw Promised a Self-Hosted AI Assistant — But Hermes Agent Is the One That Delivers It — Direct security comparison of Hermes versus OpenClaw
- #31 (0.480) Hermes Agent v0.21.0 (v2026.8.31) — The Pantheon Release (Bot Mode, Live Subagent Steering, Cron Memory) — Detailed Hermes v0.21.0 multi-agent release features
- #33 (0.470) Nous Research Hermes Agent Profile Builder — Identity, Model, Skills, MCP in One Dashboard Flow — Unique Hermes Profile Builder architecture details
- #34 (0.460) Atropos — Nous Research's RL Environments Framework — Nous Research RL infrastructure powering Hermes models

**choosing a Claude model and effort level rewind subagent haiku sonnet cost**
- #32 (0.200) Intelligence EXPLOSION: Harness Engineering with Pi Agent, Deepseek, and Gemini (IndyDevDan) — Compares running models together vs selecting one, cost spread

**maximizing the value of Claude Code sessions**
- #24 (0.570) Claude Code's Five Built-In Subagents (Faisal, XDA 2026-05-04) — inventory of built-in subagents and permissions
- #25 (0.550) Stop Hitting Claude Code Limits — Paweł Huryn on Product Compass (April 27 2026) — four-cause cost framework with specific dollar savings
- #26 (0.550) CLAUDE.md Authoring Best Practices — canonical CLAUDE.md authoring synthesis and authority stack
- #28 (0.520) Maximizing the Value of Your Claude Code Sessions (Lydia Hallie, Anthropic, 2026-08-14) — Anthropic's own direct explainer, exact topic match
- #32 (0.470) Running an AI-native engineering org (Fiona Fung, Anthropic) — org-level shift toward verification as bottleneck
- #33 (0.450) Boris Cherny (YC) — "We cut 80% of Claude Code's prompt": ablation as method, unhobbling as strategy, and agents maintai — insider ablation strategy and harness-disposable philosophy
- #35 (0.440) Anatomy of a Claude Code Project (Clarvia) — repo structuring so Claude reasons like engineer
- #37 (0.390) Why More Context Makes AI Coding Agents Worse (Abhishek Agarwal, Level Up Coding) — argues less context yields better agent output
- #40 (0.350) Claude Code Six-Primitive Stack: Isolation Spectrum + Declarative Extension Model (Farooq/Ashok, 2026-05-05) — six-primitive mental model and isolation spectrum

**agentic context management memory and cost as architecture problems**
- #21 (0.600) Practical Guide to Memory for Autonomous LLM Agents — Write-Manage-Read — write-manage-read taxonomy arguing memory beats model choice
- #22 (0.600) agentmemory (rohitg00) — Persistent Memory for AI Coding Agents — hooks-based persistent memory capture and session injection
- #24 (0.600) ACON — Optimizing Context Compression for Long-horizon LLM Agents (Kang et al., 2025) — unified compression framework cutting observation and history tokens
- #25 (0.600) Context Graph vs Vector RAG vs Raw Context — A Benchmark for Agent Memory (Nanonets) — empirical benchmark comparing memory retrieval strategies head-to-head
- #26 (0.600) Anthropic — How We Built Our Multi-Agent Research System — hard numbers on multi-agent performance-vs-token-cost tradeoff
- #27 (0.600) TencentDB Agent Memory — 4-Tier Local Memory Pyramid + Symbolic Short-Term Memory — four-tier memory pyramid plus symbolic short-term offload
- #29 (0.600) Mage: Memory as Execution-State Management for Long-Horizon Agents (Chen et al., 2026) — tree-structured execution-state memory bounding context growth
- #30 (0.600) KDnuggets — 7 Practical Ways to Reduce Claude Code Token Usage (Mehreen, May 2026) — seven tactics framed as context architecture, not prompting
- #31 (0.600) Building a Context Pruning Pipeline for Long-Running Agents (Machine Learning Mastery, 2026) — concrete semantic context-pruning pipeline implementation technique
- #32 (0.590) MemMA — Coordinating the Memory Cycle through Multi-Agent Reasoning and In-Situ Self-Evolution (Lin et al., 2026) — multi-agent coordination across memory construction and retrieval
- #33 (0.590) Agent Design Patterns (Lance Martin, Jan 2026) — five reusable context-management design patterns across agents
- #34 (0.580) Building Agent Memory with Knowledge Graphs — RAG vs Temporal Graphs (The Neural Maze, 2026) — temporal knowledge graph as long-lived memory structure
- #36 (0.580) We Built a SOTA RAG System for Code Review. In Qodo 2.4, We Took Most of It Out. — cost/ROI case study for dropping retrieval infrastructure
- #37 (0.580) Harness Engineering: Building the Production Cage for Powerful Domain Agents (Mike Chambers, AWS) — AWS harness splits memory into independently-scalable piece
- #38 (0.580) SMFS (Supermemory) — Agent Memory Exposed as a Filesystem with Semantic `grep` — memory exposed as filesystem via semantic grep hijack
- #39 (0.580) Memori — SQL-Native Agent Memory Infrastructure — SQL-native memory infra with concrete token-cost figure
- #40 (0.580) Citadel — Orchestration/Harness Layer for Claude Code and OpenAI Codex — harness combining repo-local memory and cost telemetry

**agent swarms model economics Cursor**
- #24 (0.500) Using Judgement for Model Delegation (Simon Willison, Jul 2026) — Judgement-based model delegation, cuts token spend directly
- #25 (0.470) Anthropic — How We Built Our Multi-Agent Research System — Foundational multi-agent token-cost data, 15x cost finding
- #27 (0.420) NVIDIA Nemotron 3 Ultra — A 550B Fully-Open MoE Built for Long-Running Agent Orchestration — System-of-models cost-to-task economics for agent orchestration
- #30 (0.370) thread-pm — Product Manager Skill for Orchestrating Independent Codex App Threads (hashimwarren) — RICE-based economic budget allocation across swarm threads
- #33 (0.200) SwarmForge — Tmux-Based Agent Coordination — Concrete tmux-based agent swarm coordination architecture

**knowledge graph provenance agent memory truth maintenance contradiction invalida**
- #23 (0.450) icarus-memory-infra — Local-First, Markdown-Native Agent Memory with Provenance, Supersession, and Non-Destructive Rollb — markdown memory with provenance, supersession, rollback
- #24 (0.440) `getzep/graphiti` — Temporal Context Graphs for AI Agents — temporal knowledge graph with fact validity windows
- #30 (0.300) MRAgent: Memory is Reconstructed, Not Retrieved — Graph Memory for LLM Agents (Ji et al., 2026) — cue-tag-content graph memory, iterative reconstruction
- #36 (0.200) Agent Memory Architecture — Best Practices — canonical doctrine synthesizing memory-architecture principles
- #38 (0.170) Enterprise AI Agents Keep Failing Because They Forget What They Learned — Decision Context Graphs — decision context graph reconstructs why/provenance paths
- #39 (0.150) MemOS — A Memory Operating System for AI Agents (Li et al., 2025) — MemCube explicitly bundles content, provenance, versioning

**Read:** the cut looks too tight — raise k or show more on demand.
