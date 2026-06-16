# Memvid

| | |
|---|---|
| Repo | [memvid/memvid](https://github.com/memvid/memvid) |
| Category | Tier A — codec-compressed memory |
| Stars | 15,635 |
| License | Apache-2.0 |
| First surveyed | 2026-06 |
| Architecture shape | **Archive format** — encode corpus → video + index; no incremental writes

## What it is

Encodes memory using video-codec compression for storage density — the most unconventional architecture on the roster. The core idea: encode a corpus of text into a video-like format with an index, achieving extreme storage compression. **No incremental writes** — the entire corpus must be re-encoded when new data arrives. This is an archive format, not a real-time memory system.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~6 minutes (requires numpy and video codec libraries)
- **Dependencies:** Problematic — stale `numpy<2` pin conflicts with modern Python environments
- **Isolation:** Mandatory. The numpy pin is a blocker for shared environments.

### Smoke-gate findings
- **Write-path latency:** **Extremely high** — full re-encode on every update. For a 3-turn corpus, this is fast, but it scales linearly with corpus size.
- **Async ingestion:** None — the re-encode is synchronous and blocking.
- **Storage density:** Best-in-class theoretical storage efficiency. The video-codec approach achieves compression ratios far beyond text or vector stores.
- **No incremental writes:** This is the defining constraint. Memvid is a read-heavy archive, not a write-heavy memory system.

### Bugs & sharp edges found
- **Dependency drift:** Stale `numpy<2` pin breaks in modern Python environments (3.12+). This is a maintenance red flag.
- **No incremental writes:** The architecture fundamentally cannot support streaming or real-time memory updates. Every addition requires a full re-encode.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **Codec compression survives retrieval-precision tests.** The core question: does the lossy compression of video codecs destroy the semantic precision needed for accurate retrieval? Or is the compression surprisingly benign?
2. **Storage density is worth the re-encode cost.** For archival use cases where the corpus is static and queried repeatedly, Memvid's storage efficiency could be revolutionary.
3. **No-incremental-writes is acceptable for batch workloads.** If the use case is "build an archive once, query it many times," the re-encode cost is amortized.

## Verdict so far

**The weird idea that might work for archives.** Memvid is not a real-time memory system — it's an archive format. The `numpy<2` pin is a maintenance concern. For the right use case (static corpus, read-heavy, storage-constrained), it could be brilliant. For standard agent memory (streaming, incremental, real-time), it's a mismatch. The benchmark will reveal whether the compression preserves enough semantic fidelity for accurate retrieval.

