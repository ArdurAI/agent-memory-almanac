# Graphiti (Zep family)

| | |
|---|---|
| Repo | [getzep/graphiti](https://github.com/getzep/graphiti) |
| Category | Tier A — temporal knowledge graph |
| Stars | 27,220 |
| License | Apache-2.0 |
| First surveyed | 2026-06 |
| Architecture shape | **Graph builder** — LLM extracts entities + relations, builds temporal knowledge graph with valid_at/invalid_at edges

## What it is

The open-source piece of the Zep family. Zep Community Edition is retired; Graphiti is the surviving OSS entry. It builds temporal knowledge graphs: entities and relations with temporal validity edges (`valid_at` / `invalid_at`), enabling time-travel queries like "What was true as of January 15?"

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~8 minutes (Neo4j or graph database setup required)
- **Dependencies:** Heavy — requires graph database backend, multiple LLM client libraries
- **Isolation:** Mandatory. The graph extraction pipeline is complex and brittle.

### Smoke-gate findings
- **Write-path latency:** **~35 seconds for 3 turns** — the highest on the roster. Graph extraction is expensive.
- **Async ingestion:** Heavy async pipeline — graph extraction happens in background threads. The `await_ingest` barrier is critical for measuring real cost.
- **Temporal reasoning:** Best-in-class potential — the graph structure explicitly models time. If the query engine uses temporal edges correctly, temporal questions should score very high.
- **Contradiction handling:** Natural fit — contradictions become `invalid_at` edges on old facts and `valid_at` edges on new facts.

### Bugs & sharp edges found
- **Latency is the defining characteristic:** 35s for 3 turns means Graphiti is not suitable for real-time chat. It's a batch/memory-preparation tool.
- **Database dependency:** Requires Neo4j or compatible graph database. This is a significant ops burden compared to file-based or vector-only tools.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **Temporal knowledge graphs beat flat vector stores on temporal questions.** The graph structure should dominate the temporal category. LoCoMo will measure this.
2. **Graph extraction quality justifies the latency.** If the extracted graph captures the right entities and relations, retrieval accuracy should be significantly higher than fact extractors. The 35s cost must be paid back in accuracy.
3. **Contradiction handling is native.** The `valid_at`/`invalid_at` model should pass `contradiction_storm` and `temporal_paradox` scenarios cleanly.

## Verdict so far

**The high-cost, high-potential bet.** 35 seconds for 3 turns is the highest write-path latency on the roster. If Graphiti doesn't dominate the temporal and contradiction categories, its cost is unjustified. The stress suite will be especially revealing — does the graph structure survive contradiction storms and duplicate floods, or does noise degrade the graph quality?

## Important note: Zep CE retirement

`getzep/zep` (4.6k stars) is now "Examples, Integrations & More" only. The open-source piece of the Zep family is **Graphiti**. If a guide tells you to self-host Zep CE, it's stale. Graphiti is the current Zep-family OSS entry on the roster.

