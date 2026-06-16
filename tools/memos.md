# MemOS

| | |
|---|---|
| Repo | [MemTensor/MemOS](https://github.com/MemTensor/MemOS) |
| Category | Tier A — memory operating system |
| Stars | 9,689 |
| License | Apache-2.0 |
| First surveyed | 2026-06 |
| Architecture shape | **OS-style manager** — scheduling, lifecycle, and governance for heterogeneous memory types

## What it is

A 'memory OS' layer: scheduling, lifecycle, and governance for heterogeneous memory types rather than a single store. MemOS manages multiple memory backends (vector, graph, SQL, cache) and decides which to use for which query. It abstracts the storage layer so the agent doesn't need to know whether it's talking to a vector store or a graph database.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~8 minutes (requires configuring multiple backends)
- **Dependencies:** Heavy — orchestrates multiple storage systems
- **Isolation:** Recommended. The multi-backend setup is complex.

### Smoke-gate findings
- **Write-path latency:** ~6s for 3 turns (multi-backend routing + storage)
- **Async ingestion:** Depends on the backing store. If using a graph backend, there's async extraction lag.
- **Heterogeneous storage:** The core abstraction — MemOS routes writes to the appropriate backend and queries across all of them.
- **Lifecycle management:** Automatic memory lifecycle (hot → warm → cold → archive) based on access patterns.

### Bugs & sharp edges found
- None in the smoke gate.
- **Complexity tax:** Managing multiple backends is inherently more complex than a single store. The ops burden is higher than any single-backend tool.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **The OS abstraction earns its complexity against simpler extractors.** If multi-backend routing produces better accuracy than any single backend, the complexity is justified. If not, it's overhead.
2. **Lifecycle management reduces cost without sacrificing accuracy.** Hot/cold/archive tiers should reduce token burn and storage cost. Telemetry will measure this.
3. **Heterogeneous storage beats homogeneous storage on diverse workloads.** Different query types (factual vs. temporal vs. multi-hop) should benefit from different backends. The benchmark will test whether the routing is smart enough to exploit this.

## Verdict so far

**The most ambitious architecture on the roster.** MemOS is trying to be the Kubernetes of memory — orchestrate heterogeneous backends, manage lifecycle, and abstract complexity. The question is whether the orchestration overhead pays for itself in accuracy. The benchmark phase will be revealing: if the multi-backend routing doesn't produce clear accuracy gains, the complexity is unjustified. For teams already running multiple memory systems, MemOS might be the unification layer they need.

