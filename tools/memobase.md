# Memobase

| | |
|---|---|
| Repo | [memodb-io/memobase](https://github.com/memodb-io/memobase) |
| Category | Tier A — evolving user profile |
| Stars | 2,748 |
| License | Apache-2.0 |
| First surveyed | 2026-06 |
| Freshness watch | ⚠️ Last push 2026-01-11 (~5 months ago) |
| Architecture shape | **Profile / user-modeler** — maintains structured, evolving user profile; caps LLM calls at exactly 3 per run

## What it is

Maintains a structured, evolving user profile instead of individual memory facts. The key design constraint: **exactly 3 LLM calls per run** — one for extraction, one for profile update, one for retrieval. This is a deliberate cost-control mechanism. The profile is a structured document (JSON schema) that evolves over time.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~6 minutes (requires Memobase server setup)
- **Dependencies:** Moderate — Memobase server, async processing pipeline
- **Isolation:** Recommended. The server process is substantial.

### Smoke-gate findings
- **Write-path latency:** ~5s for 3 turns (3-LLM-call pipeline overhead)
- **Async ingestion:** **Flush-based** — profile updates are batched and flushed asynchronously. The `await_ingest` barrier measures this lag.
- **Cost control:** The 3-LLM-call cap is a hard constraint. For high-throughput use cases, this is a significant cost advantage.
- **Profile structure:** The evolving JSON schema is human-inspectable and queryable.

### Bugs & sharp edges found
- **Freshness watch:** No push in ~5 months (as of June 2026). Still within the 6-month liveness rule, but noted. The project may be in maintenance mode.
- **3-call constraint:** If the extraction or update call fails, the pipeline collapses. There's no graceful degradation.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **40–50% token-savings claim.** The 3-LLM-call cap and profile-based storage should produce significant token savings compared to chunk-based or fact-list-based tools. Telemetry will measure this.
2. **Exactly-3-calls design is production-viable.** The hard constraint should force efficient memory management. If accuracy doesn't degrade, the cost savings are real.
3. **User-profile beats flat facts on persona recall.** The structured profile should capture user preferences and habits better than a flat fact list. PlatformOps-Mem will test this.

## Verdict so far

**The cost-control specialist with a freshness concern.** The 3-LLM-call constraint is the most aggressive cost-control mechanism on the roster. If it delivers competitive accuracy, it's a game-changer for cost-conscious teams. The ~5-month gap since the last push is a yellow flag — the project may be in maintenance mode. The benchmark phase will tell if the cost savings come at an accuracy price.

