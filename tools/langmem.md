# LangMem

| | |
|---|---|
| Repo | [langchain-ai/langmem](https://github.com/langchain-ai/langmem) |
| Category | Tier A — LangChain memory layer |
| Stars | 1,496 |
| License | MIT |
| First surveyed | 2026-06 |
| Architecture shape | **Fact extractor** — LangChain's first-party memory layer

## What it is

LangChain's first-party memory layer; the default choice inside that ecosystem. It provides memory primitives (conversation buffer, vector store memory, entity memory) that integrate natively with LangChain's agent and chain abstractions.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~4 minutes (pip install if you already have LangChain)
- **Dependencies:** LangChain ecosystem — if you're already using LangChain, the marginal cost is near zero
- **Isolation:** Not required for LangChain projects. External to the LangChain ecosystem, it's less compelling.

### Smoke-gate findings
- **Write-path latency:** ~2s for 3 turns (LangChain memory integration overhead)
- **Async ingestion:** Synchronous — standard LangChain memory is blocking
- **Ecosystem lock-in:** The value is entirely in the LangChain integration. Used outside LangChain, it's just another memory library.
- **Flexibility:** Supports multiple memory types (buffer, vector, entity) via configuration.

### Bugs & sharp edges found
- None in the smoke gate.
- **Ecosystem dependency:** If you're not using LangChain, LangMem offers no advantage over Mem0 or other standalone tools.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **First-party integration beats third-party adapters.** The LangChain-native integration should be smoother than bolting Mem0 or Letta onto a LangChain project. The smoke gate confirms this — install is trivial if you already have LangChain.
2. **Neutral adapter performance is competitive.** The key question: when tested through a neutral adapter (not the LangChain-native path), does LangMem's core memory quality compete with standalone tools? The benchmark will test this.
3. **Ecosystem lock-in is worth it for LangChain users.** If you're already in the LangChain ecosystem, the marginal cost of LangMem is near zero. The benchmark will verify whether the quality matches the convenience.

## Verdict so far

**The ecosystem-native choice.** LangMem's value proposition is entirely about LangChain integration. If you're not using LangChain, there's no reason to choose it over Mem0 or Basic Memory. If you are using LangChain, it's the path of least resistance. The neutral-adapter benchmark will be revealing — if LangMem's core memory quality is competitive even outside its native ecosystem, it's a stronger tool than its ecosystem-specific positioning suggests.

