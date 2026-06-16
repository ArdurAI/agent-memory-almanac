# Hindsight

| | |
|---|---|
| Repo | [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) |
| Category | Tier A — cognitive-architecture memory |
| Stars | 16,076 |
| License | MIT |
| First surveyed | 2026-06 |
| Architecture shape | **Graph builder** — separates facts, experiences, observations, opinions into distinct networks with time-anchored, entity-linked memories

## What it is

Organizes memory into separate networks for facts, experiences, observations, and opinions — separating evidence from inference. By Vectorize (MIT license). Runs in-process or via Docker. This is the "cognitive architecture" approach to memory: different types of knowledge live in different stores and are retrieved differently.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~6 minutes (Docker or in-process)
- **Dependencies:** Moderate — Vectorize SDK, embedding model, optional Docker
- **Isolation:** Recommended but not mandatory.

### Smoke-gate findings
- **Write-path latency:** ~5s for 3 turns (multi-network classification + embedding + storage)
- **Async ingestion:** In-process is synchronous; Docker mode has minor container lag
- **Multi-network storage:** Facts, experiences, observations, and opinions are stored in separate networks. This is the core architectural claim.
- **Time-anchored:** Every memory is timestamped and entity-linked.

### Bugs & sharp edges found
- None in the smoke gate.
- **Vendor comparison note:** Hindsight claims SOTA on long-horizon benchmarks. Vectorize also publishes tool comparisons, so these claims get the same independent verification as everyone else's. The Quest will reproduce them.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **SOTA on long-horizon conversational benchmarks.** The multi-network architecture should outperform monolithic stores on complex reasoning tasks. LoCoMo will verify or refute this.
2. **Evidence-inference separation improves accuracy.** By separating facts from opinions, the retrieval system should return more reliable evidence for answering questions. The stress suite will test this with contradiction scenarios.
3. **In-process mode is production-viable.** Running in-process without a separate database server should reduce ops burden while maintaining performance.

## Verdict so far

**The most theoretically interesting graph architecture.** The evidence-inference separation is a genuine cognitive-science insight applied to agent memory. The MIT license and in-process option make it accessible. The SOTA claims are bold — the benchmark phase will tell if they hold up under independent testing. The multi-network approach is computationally more expensive than single-store tools, so the accuracy premium must be real.

