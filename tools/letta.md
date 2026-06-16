# Letta (MemGPT)

| | |
|---|---|
| Repo | [letta-ai/letta](https://github.com/letta-ai/letta) |
| Category | Tier A — OS-style memory manager |
| Stars | 23,224 |
| License | Apache-2.0 |
| First surveyed | 2026-06 |
| Architecture shape | **OS-style manager** — agent loop manages its own memory: core blocks ↔ archival store, paged storage

## What it is

Treats the LLM like an operating system managing its own memory: core context (RAM), recall store (recent history), archival store (long-term), with the model paging information in and out. The agent runs a full loop per message — it decides what to remember, what to recall, and what to forget.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~10 minutes (requires Letta server setup)
- **Dependencies:** Heavy — Letta server, Python SDK, model provider configuration
- **Isolation:** Recommended. The server process is substantial.

### Smoke-gate findings
- **Write-path latency:** **High** — Letta runs a full agent loop per message. Each turn triggers the LLM to decide what to store, recall, and forget. This is inherently slower than passive storage.
- **Async ingestion:** None — the agent loop is the write path. Every message is processed synchronously through the full reasoning loop.
- **Self-management:** The agent decides what to remember. This is a feature (smart filtering) and a bug (the agent might miss critical facts).
- **BYO-provider bug:** The `bring-your-own-provider` feature **cannot work at all** unless the provider is literally named `openai-proxy` (handle-validation bug). This means users with custom endpoints cannot use Letta without patching.

### Bugs & sharp edges found
- **🔴 BYO-provider handle bug:** Provider names other than `openai-proxy` fail validation. This is a hard blocker for anyone not using OpenAI directly.
- **Latency cost:** Every message triggers a full LLM call. At scale, this is the most expensive write path on the roster.
- **State opacity:** The agent's internal memory decisions are not inspectable. Debuggability is lower than explicit storage tools.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **Self-managed paging beats externally-managed retrieval at scale.** If the agent's own memory decisions are better than a human-designed retrieval pipeline, Letta should win on accuracy. The cost is latency.
2. **Best for long-running agents.** The OS metaphor should pay off in long-horizon conversations where the agent needs to manage its own context window. LoCoMo will test this.
3. **The agent loop is the right abstraction.** The full-reasoning-per-message model should produce more coherent memory than passive fact extraction. The stress suite will test whether the agent handles contradictions and noise correctly.

## Verdict so far

**The most philosophically distinct tool.** Letta's OS metaphor is the deepest conceptual architecture on the roster. The BYO-provider bug is a hard blocker for non-OpenAI users. The latency cost is inherent to the design — every message triggers an LLM call. If the self-management accuracy doesn't significantly exceed passive tools, the cost is unjustified. The benchmark phase will be decisive.

