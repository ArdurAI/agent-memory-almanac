# Cognee

| | |
|---|---|
| Repo | [topoteretes/cognee](https://github.com/topoteretes/cognee) |
| Category | Tier A — up-front knowledge graph |
| Stars | 17,743 |
| License | Apache-2.0 |
| First surveyed | 2026-06 |
| Architecture shape | **Graph builder** — builds full knowledge graph before queries; local-first, privacy-oriented

## What it is

Builds a full knowledge graph from your data before queries happen, combining graph structure with RAG. The "cognify" step is the key: it processes the entire corpus up-front, extracting entities, relations, and summaries. This is local-first and privacy-oriented — no cloud dependency.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~7 minutes (requires `cognify` pipeline setup)
- **Dependencies:** Heavy — graph processing, multiple LLM client libraries
- **Isolation:** **Mandatory.** Co-installation with basic-memory fails due to `fastapi/starlette` version conflicts.

### Smoke-gate findings
- **Write-path latency:** **High** — the `cognify` step processes the entire corpus up-front. Bulk ingestion is slow but query-time is fast.
- **Async ingestion:** The `cognify` step is synchronous and blocking. For large corpora, this is a batch operation.
- **Graph quality:** The up-front extraction should produce higher-quality graphs than incremental tools, but it requires the entire corpus to be available at ingestion time.
- **Local-first:** No cloud dependency — all processing happens locally.

### Bugs & sharp edges found
- **Dependency conflict:** Direct conflict with basic-memory on `fastapi/starlette`. Installing both in the same environment breaks both.
- **Up-front cost:** The `cognify` step is expensive. For streaming or real-time use cases, this is a poor fit.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **Up-front graph construction beats incremental extraction on accuracy.** If the full-corpus view produces better entity and relation extraction than incremental tools, Cognee should win on multi-hop and temporal questions.
2. **Local-first privacy is worth the cost.** No cloud dependency means no data leakage risk. The trade-off is compute cost on the local machine.
3. **Bulk ingest cost is amortized by fast queries.** If query latency is significantly lower than incremental tools, the up-front cost pays off for read-heavy workloads.

## Verdict so far

**The batch-processing graph builder.** Cognee's up-front `cognify` model is the opposite of real-time streaming. It's designed for corpora that are available in advance and queried repeatedly. The dependency conflict with basic-memory is a real problem for anyone trying to compare tools side-by-side. The benchmark will reveal whether the up-front graph quality justifies the cost.

