# Published vs. Reproduced — Comparison Table

For every tool with published benchmark claims, this table tracks the delta between what the vendor published and what the Quest independently reproduced.

> **Rule:** Deltas > 5 points are flagged. The Quest never assumes vendor malice — differences are often due to different model versions, sampling strategies, or evaluation protocols. Raw data is published for every run so readers can audit.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Quest reproduces within 5 points of vendor claim |
| ⚠️ | Quest reproduces with 5–15 point delta — investigate |
| 🔴 | Quest reproduces with >15 point delta — significant discrepancy |
| ➖ | No vendor claim published for this benchmark |
| 🕐 | Quest run pending — results not yet available |

---

## Mem0

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|--------|
| LoCoMo | Answerable | ➖ | 🕐 | 🕐 | — | pending |
| LoCoMo | Overall | ➖ | 🕐 | 🕐 | — | pending |
| LongMemEval | R@5 | ➖ | 🕐 | 🕐 | — | pending |
| Token savings | vs. full-context | ➖ | 🕐 | 🕐 | — | pending |

---

## Letta (MemGPT)

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|--------|
| LoCoMo | Answerable | ➖ | 🕐 | 🕐 | — | pending |
| LoCoMo | Overall | ➖ | 🕐 | 🕐 | — | pending |
| Long-horizon | Accuracy | ➖ | 🕐 | 🕐 | — | pending |

---

## Graphiti (Zep)

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|--------|
| LoCoMo | Temporal | ➖ | 🕐 | 🕐 | — | pending |
| LoCoMo | Overall | ➖ | 🕐 | 🕐 | — | pending |

---

## Cognee

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|-------|
| LoCoMo | Answerable | ➖ | 🕐 | 🕐 | — | pending |
| Bulk ingest | Time | ➖ | 🕐 | 🕐 | — | pending |

---

## Hindsight

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|--------|
| LoCoMo | Answerable | ➖ | 🕐 | 🕐 | — | pending |
| Long-horizon | SOTA | ➖ | 🕐 | 🕐 | — | pending |

> **Note:** Hindsight claims SOTA on long-horizon benchmarks. Vectorize (the vendor) also publishes tool comparisons. These claims receive the same independent verification as every other tool's claims.

---

## Memvid

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|--------|
| LoCoMo | Answerable | ➖ | 🕐 | 🕐 | — | pending |
| Storage | Compression ratio | ➖ | 🕐 | 🕐 | — | pending |

---

## Memori

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|-------|
| LoCoMo | Answerable | ➖ | 🕐 | 🕐 | — | pending |

---

## MemOS

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|-------|
| LoCoMo | Answerable | ➖ | 🕐 | 🕐 | — | pending |

---

## Honcho

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|-------|
| LoCoMo | Answerable | ➖ | 🕐 | 🕐 | — | pending |
| Persona recall | Accuracy | ➖ | 🕐 | 🕐 | — | pending |

> **Disclosure:** ArdurAI contributes to Honcho. Identical harness, frozen methodology, raw data published.

---

## OpenMemory

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|-------|
| LoCoMo | Answerable | ➖ | 🕐 | 🕐 | — | pending |

---

## Basic Memory

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|--------|
| LoCoMo | Answerable | ➖ | 🕐 | **0.335** | — | open track complete |
| LoCoMo | Overall | ➖ | 🕐 | **0.457** | — | open track complete |

> **Finding:** First tool to clear the naive-RAG baseline (0.300 answerable) in the open track. The margin is narrow (3.5 points), so the main-track Claude results will be decisive.

---

## mcp-knowledge-graph

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|--------|
| LoCoMo | Answerable | ➖ | 🕐 | 🕐 | — | pending |

---

## claude-mem

| Benchmark | Metric | Vendor claim | Quest (main) | Quest (open) | Delta | Status |
|-----------|--------|------------|--------------|--------------|-------|--------|
| LoCoMo | Answerable | ➖ | **deferred** | **deferred** | — | native-session eval planned |

> **Note:** claude-mem has no queryable API; it will be evaluated in its native Claude Code environment rather than through the standard adapter.

---

## Baselines

| Tool | LoCoMo Answerable (open) | LoCoMo Overall (open) | Role |
|------|--------------------------|----------------------|------|
| no-memory | 0.000 | 0.223 | Canary — proves benchmark doesn't leak |
| plainfile | 0.249 | 0.397 | Minimal storage baseline |
| obsidian | 0.309 | 0.440 | Timestamp-visibility baseline |
| naive-rag | 0.300 | 0.433 | The bar every tool must clear |
| full-context | 🕐 | 🕐 | Cost ceiling |

---

## How to read this table

1. **Vendor claims are self-reported** — they come from the tool's README, documentation, or published papers.
2. **Quest reproduces** — these are independent runs through the frozen harness.
3. **Deltas matter** — a 5-point difference is noise; a 15-point difference is a methodology mismatch or a claim that doesn't hold.
4. **Raw data is published** — every Quest run has a `run.json` and `per_question.jsonl` in `data/benchmarks/`. You can reproduce any number yourself.

---

*Last updated: 2026-06-16*
*Methodology lock: 2026-06-09*
