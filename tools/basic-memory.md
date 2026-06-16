# Basic Memory

| | |
|---|---|
| Repo | [basicmachines-co/basic-memory](https://github.com/basicmachines-co/basic-memory) |
| Category | Tier B — MCP, markdown-native |
| Stars | 3,173 |
| License | AGPL-3.0 |
| First surveyed | 2026-06 |
| Architecture shape | **MCP server** — markdown-on-disk, human-browsable, no LLM in write path

## What it is

MCP server storing everything as plain Markdown on disk. The folder doubles as an Obsidian vault, so the agent's knowledge graph is human-browsable and editable. No LLM in the write path — the calling agent is the extractor, and Basic Memory provides storage + search. This makes it cheap and client-agnostic, but retrieval quality depends on whoever is calling.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~5 minutes with `pip install basic-memory`
- **Dependencies:** Broken at every resolvable version of its `fastmcp` dependency — co-installation with cognee produces direct conflicts on `fastapi/starlette`
- **Isolation:** Mandatory. Do not install in the same environment as cognee or mem0.

### Smoke-gate findings
- **Write-path latency:** ~1.2s for 3-turn ingestion (file I/O + markdown rendering)
- **Async ingestion:** Synchronous — no lag to measure
- **Timestamp handling:** Inlines timestamps into markdown notes, so the answering model can see them. This is the key to its temporal performance.
- **Data sovereignty:** The strongest data-sovereignty story on the roster — everything is a local file you own.

### Bugs & sharp edges found
- **Dependency drift:** `fastmcp` version conflict breaks the CLI at every resolvable version. The tool is effectively uninstallable in a shared environment.
- **No LLM in write path:** A feature, not a bug, but means retrieval quality is entirely up to the caller's prompt engineering.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Abstention | Overall |
|-----------|--------|--------|------------|------------|---------|
| LoCoMo s300 | **open** | ✅ **complete** | **0.335** | **0.881** | **0.457** |
| LoCoMo s300 | main | queued | — | — | — |
| Stress suite | — | queued | — | — | — |
| PlatformOps-Mem | — | queued | — | — | — |

### Open-track per-category breakdown

| Category | Accuracy | Notes |
|----------|----------|-------|
| multi-hop | 0.116 | Struggles with cross-session connections |
| temporal | 0.229 | **Timestamp visibility pays off** — second-best temporal score |
| open-domain | 0.067 | Weak on general knowledge questions |
| single-hop | 0.480 | Strong on direct recall |

## Key finding: first tool to clear the naive-RAG baseline

Basic Memory is the first tool in the open track to justify its machinery: **0.335 answerable** edges past the naive-RAG bar (0.300). This is a significant milestone — it proves that a simple MCP server with markdown storage can outperform raw vector retrieval on long-horizon memory tasks.

## Claims under independent test

1. **Human-readable storage doesn't cost retrieval accuracy.** ✅ **Partially verified** — it beats naive-RAG, but the gap is narrow (3.5 points). The full main track will tell if this holds under Claude grading.
2. **Strongest data-sovereignty story.** ✅ **Verified** — everything is local markdown. No cloud tether, no external API.
3. **Dependency drift is endemic.** ✅ **Verified** — the tool is broken in shared environments.

## Verdict so far

**The minimal viable memory.** Basic Memory proves that you don't need a graph database or LLM extraction to beat naive RAG — you just need timestamps in the retrieved text and a clean storage layer. The dependency drift is a real ops problem, but in isolation it works. The narrow margin over naive-RAG (0.335 vs 0.300) means the full main track and stress suite will be decisive.

