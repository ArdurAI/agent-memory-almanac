# Honcho

| | |
|---|---|
| Repo | [plastic-labs/honcho](https://github.com/plastic-labs/honcho) |
| Category | Tier A — theory-of-mind user modeling |
| Stars | 4,995 |
| License | AGPL-3.0 |
| First surveyed | 2026-06 |
| Architecture shape | **Profile / user-modeler** — builds user representation via dialectic API, not flat fact list

## What it is

User-modeling memory backend (FastAPI + pgvector). Instead of storing a flat list of facts, Honcho builds a representation of the user via a dialectic API — it models the user's preferences, persona, and context through structured user-model updates. **Disclosure: ArdurAI contributes to Honcho — identical harness, frozen methodology applies.**

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~10 minutes (requires PostgreSQL + pgvector setup)
- **Dependencies:** FastAPI, pgvector, async SQLAlchemy, Redis for caching
- **Isolation:** Recommended. PostgreSQL dependency makes it heavier than file-based tools.

### Smoke-gate findings
- **Write-path latency:** ~4.5s for 3 turns (deriver queue + user-model update)
- **Async ingestion:** **Deriver queue** — user-model updates happen asynchronously. The `await_ingest` barrier measures this lag.
- **Temporal reasoning:** Indirect — user-model snapshots are temporal, but the query path doesn't explicitly surface timestamps to the answering model.
- **Cross-project isolation:** Supports `user_id` and `app_id` partitioning natively.

### Bugs & sharp edges found
- **🔴 Privacy-shaped bug:** Honcho's Redis cache keeps serving search results for a **deleted workspace** until the TTL expires. This means sensitive data remains retrievable after deletion for the duration of the cache TTL.
- **Ops burden:** PostgreSQL + pgvector + Redis is a three-service stack. This is the highest ops burden among Tier A tools.
- **AGPL-3.0 license:** Copyleft — may be a concern for proprietary deployments.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **User-model representations beat fact stores on preference and persona recall.** The dialectic API should outperform flat fact lists on questions about user preferences, personality, and habits. LoCoMo has limited persona questions, but PlatformOps-Mem will test this directly.
2. **The deriver queue enables real-time responsiveness.** Async user-model updates mean the chat path isn't blocked by model inference. The `await_ingest` measurement will quantify this trade-off.
3. **Three-service stack is worth the ops burden.** If user-model accuracy significantly exceeds fact extractors, the PostgreSQL + Redis + FastAPI stack is justified.

## Verdict so far

**The most architecturally interesting Tier A tool, with a real privacy bug.** The user-modeling approach is conceptually distinct from every other tool on the roster. The Redis cache bug is serious — a deleted workspace's data remains accessible for the TTL duration. The AGPL license and three-service ops burden make this a tool for teams that value user-modeling accuracy enough to pay the cost. The benchmark phase will tell if that accuracy premium exists.

