# Mem0

| | |
|---|---|
| Repo | [mem0ai/mem0](https://github.com/mem0ai/mem0) |
| Category | Tier A — fact extractor |
| Stars | 58,186 |
| License | Apache-2.0 |
| First surveyed | 2026-06 |
| Architecture shape | **Fact extractor** — LLM extracts salient facts, reconciles with ADD/UPDATE/DELETE/NOOP, stores in vector store

## What it is

The most popular agent-memory library (58k stars). Instead of storing raw conversation chunks, Mem0 extracts salient facts and reconciles them against existing memory. New information triggers one of four operations: ADD, UPDATE, DELETE, or NOOP. This consolidation step is the core claim — it prevents memory bloat and handles contradictions by design.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~5 minutes with `pip install mem0ai` and an OpenAI API key
- **Dependencies:** 47 direct dependencies (moderate); conflicts with `fastmcp` versions when co-installed with basic-memory
- **Isolation recommendation:** Run in its own venv

### Smoke-gate findings
- **Write-path latency:** ~2.3s for 3-turn ingestion (fact extraction + reconciliation overhead)
- **Async ingestion:** Synchronous — no `await_ingest` lag to measure
- **Contradiction handling:** Reconciles via UPDATE operation; appears to prefer the latest fact (passes `contradiction_storm` in theory)
- **Cross-project isolation:** Supports `user_id` and `agent_id` partitioning natively

### Bugs & sharp edges found
- None surfaced in the smoke gate. Mem0 is the most polished Tier A tool in terms of setup experience.
- **Dependency note:** Co-installation with basic-memory fails due to `fastmcp` version conflict. Plan isolation.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **Consolidation beats raw chunking on accuracy.** Mem0's fact-extraction + reconciliation should outperform naive RAG and plain-file baselines. The LoCoMo run will measure this.
2. **Contradiction storms are handled by design.** The UPDATE operation should resolve the `contradiction_storm` scenario cleanly.
3. **Token savings via consolidation.** Fewer stored facts than raw chunks should translate to lower retrieval token burn. Telemetry will measure this.

## Verdict so far

**Most polished Tier A install.** Mem0 is the reference implementation for the fact-extractor shape. The real question is whether consolidation overhead (latency + LLM cost per write) pays for itself in retrieval accuracy. The benchmark phase will answer that.

