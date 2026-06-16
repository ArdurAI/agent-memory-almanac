# mcp-knowledge-graph

| | |
|---|---|
| Repo | [shaneholloman/mcp-knowledge-graph](https://github.com/shaneholloman/mcp-knowledge-graph) |
| Category | Tier B — MCP, entity graph |
| Stars | 864 |
| License | MIT |
| First surveyed | 2026-06 |
| Architecture shape | **MCP server** — persistent memory via local knowledge graph of entities, relations, and observations

## What it is

Persistent memory via a local knowledge graph of entities, relations, and observations; the maintained evolution of the reference MCP memory server. The graph is stored as JSON files on disk. This is the simplest graph-based memory tool on the roster — no database required, just files.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~2 minutes (pure Python, no external services)
- **Dependencies:** Minimal — no database, no LLM client libraries
- **Isolation:** Not required. Lightweight and self-contained.

### Smoke-gate findings
- **Write-path latency:** ~1.5s for 3 turns (entity extraction + JSON serialization)
- **Async ingestion:** Synchronous — JSON writes are blocking but fast.
- **Graph quality:** The caller is the extractor — entity and relation quality depends on the calling agent's prompt engineering.
- **Storage:** Pure JSON files on disk. Human-inspectable and version-control-friendly.

### Bugs & sharp edges found
- **🔴 Cross-project contamination:** `mcp-knowledge-graph` silently writes to a **global shared store** when the working directory lacks project markers. Memories from different projects land in one file. This means **Project A's data leaks into Project B's memory** by default.
- **No project-scoping by default:** Users must manually add project markers to every working directory. This is a dangerous default.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **The reference-architecture graph holds up beyond toy scale.** The simplest graph memory tool should be competitive on small-to-medium corpora. The benchmark will test whether it degrades at scale.
2. **JSON-file storage is sufficient for production.** No database dependency means zero ops burden. The question is whether JSON serialization becomes a bottleneck.
3. **Cross-project scoping is the user's responsibility.** The default global-store behavior is a design choice, not a bug. The Quest evaluates tools as they ship — dangerous defaults are documented as findings.

## Verdict so far

**The simplest graph tool with a dangerous default.** The JSON-file approach is refreshingly minimal. The cross-project contamination bug is serious — a memory tool shouldn't leak data between projects by default. The lack of an LLM in the write path means accuracy is caller-dependent. For small projects with explicit project markers, it's lightweight and effective. For multi-project workflows, the default behavior is a data-leak risk.

