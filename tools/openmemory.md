# OpenMemory

| | |
|---|---|
| Repo | [CaviraOSS/OpenMemory](https://github.com/CaviraOSS/OpenMemory) |
| Category | Tier B — MCP, local SQLite |
| Stars | 4,211 |
| License | Apache-2.0 |
| First surveyed | 2026-06 |
| Architecture shape | **MCP server** — local SQLite, hierarchical memory decomposition with temporal graph on top, zero cloud config

## What it is

Local persistent memory for LLM apps (Claude Desktop, Copilot, Codex, etc.): SQLite, hierarchical memory decomposition with a temporal graph on top, zero cloud config. The "zero cloud config" claim is its differentiator — it works entirely offline with no external accounts or API keys.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~3 minutes (pure SQLite, zero external config)
- **Dependencies:** Minimal — SQLite, no LLM client libraries required
- **Isolation:** Not required. The tool is lightweight and self-contained.

### Smoke-gate findings
- **Write-path latency:** **Sub-millisecond** — the fastest on the roster. SQLite writes are near-instant.
- **Async ingestion:** Synchronous — SQLite is blocking but fast.
- **Data sovereignty:** Excellent — everything is a local SQLite file you own.
- **Hierarchical decomposition:** Memories are decomposed into hierarchical layers (session, topic, global). This is an interesting retrieval strategy.

### Bugs & sharp edges found
- **🔴 Privacy-shaped bug:** `delete_all` removes database rows but **not the in-process query cache**. Deleted memories stay retriable for the life of the process. This is a real data-deletion bug — sensitive data is not actually deleted until the process restarts.
- **No LLM in write path:** Like Basic Memory, the caller is the extractor. Retrieval quality depends on the caller.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **Zero cloud config is production-ready.** If SQLite + local processing is sufficient for accurate memory, OpenMemory proves that cloud dependency is unnecessary.
2. **Hierarchical decomposition beats flat storage.** The session/topic/global layers should produce more relevant retrieval than flat keyword or vector search.
3. **Sub-millisecond writes enable real-time use cases.** The fastest write path on the roster makes OpenMemory suitable for high-throughput, low-latency applications.

## Verdict so far

**The fastest and simplest tool with a real deletion bug.** Sub-millisecond writes and zero cloud config are compelling. The `delete_all` cache bug is serious — deleted data remains retrievable until process restart. If the deletion bug is fixed and the hierarchical decomposition produces competitive accuracy, OpenMemory could be the go-to for lightweight, privacy-first deployments. The lack of an LLM in the write path means it's cheap but accuracy-dependent on the caller.

