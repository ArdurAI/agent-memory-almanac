# LoCoMo s300 — rolling results

**Benchmark**: [LoCoMo](https://github.com/snap-research/locomo) (1,986 questions
over 10 multi-session conversations), stratified 300-question sample, seed 42
(`locomo-s300-seed42`). Full-1,986 runs follow for published numbers; the sample
is disclosed on every row.

**Pipeline** (no mocks, by construction): each tool really ingests all 10
conversations through its own write path → really retrieves per question → a
frozen answering model (`claude-sonnet-4-6`) sees **only the retrieved
excerpts** — never gold answers or categories → graded by deterministic rules
first (including the adversarial-category abstention check), frozen LLM judge
(`claude-opus-4-8`) for the ambiguous rest. Raw per-question records
(excerpts, verbatim answers, token usage) are persisted for every run.

## How to read the columns

LoCoMo's category 5 (67/300 questions) is **adversarial**: the correct answer
is to abstain. A tool that remembers nothing abstains on everything — so the
*overall* column rewards amnesia with a free 22%. We therefore report:

- **Answerable** — accuracy on categories 1–4 (multi-hop, temporal,
  open-domain, single-hop): the memory actually working.
- **Abstention** — category 5: knowing what it *doesn't* know.
- **Overall** — the blended number most vendors quote.

## The canary, and why you can trust this table

The first run of every batch is the **no-memory baseline** through the
identical pipeline. If the benchmark leaked answers anywhere, it would score
above zero on answerable categories. Result:

| Tool | Answerable (cat 1–4) | Abstention (cat 5) | Overall | Graded by |
|------|---------------------|--------------------|---------|-----------|
| no-memory (canary) | **0.000** (0/233) | 1.000 | 0.223 | 300 deterministic / 0 judge |

Zero on all 233 answerable questions, every failure `missing_recall` — the
answerer honestly says "I don't know" when retrieval gives it nothing.
**0.223 overall is the blanket-abstainer reference line**: any tool below it,
or at ~0 answerable, is doing nothing.

## Results (updated as runs complete)

| Tool | Tier | Answerable | Abstention | Overall | Status |
|------|------|-----------|------------|---------|--------|
| no-memory | C (canary) | 0.000 | 1.000 | 0.223 | ✅ 2026-06-09 |
| plainfile | C | | | | paused at 213/300 (provider limit) |
| obsidian | C | | | | paused (provider limit) |
| naive-rag | C | | | | queued |
| full-context | C (ceiling) | | | | paused at 145/300 (provider limit) |
| basic-memory | B | | | | queued |
| openmemory | B | | | | queued |
| mcp-knowledge-graph | B | | | | queued |
| memori | A | | | | queued |
| memvid | A | | | | queued |
| mem0 · letta · graphiti · cognee · honcho · memobase · langmem · hindsight · memos | A | | | | extraction-heavy batch — scheduled |

*Answer/judge transports for these runs: OpenRouter (Anthropic-native batch
grading pending a key; transport is stamped in every run's metadata per the
methodology).*

---

## Open-model track (D8) — same pipeline, open models end-to-end

While the main track's provider quota resets, the same s300 benchmark runs as
a **separate series** on open models: answerer `deepseek-v4-pro`, judge
`qwen3.5:397b` (deliberately different families to avoid same-family grading
bias), both via Ollama Cloud. Open-track runs are tagged and stamped in
metadata; they are never merged or compared head-to-head with main-track rows
— the answerer differs, so the tables differ.

The open track ran its own canary first: no-memory scored 0.000 answerable /
1.000 abstention — same leak-free profile as the main track.

**5 of 10 tools in** (cheap tier; extraction-heavy Tier A still queued). The
first real result worth its salt: **basic-memory clears the naive-RAG baseline**
— the bar a memory tool must beat to justify its machinery.

### OPEN track — results

| Tool | Tier | Answerable | Abstention | Overall | Graded (det/llm) | Judge |
|------|------|-----------|------------|---------|------------------|-------|
| basic-memory | B | 0.335 | 0.881 | 0.457 | 216/84 | qwen3.5:397b |
| obsidian | C | 0.309 | 0.895 | 0.440 | 212/88 | qwen3.5:397b |
| naive-rag | C | 0.300 | 0.895 | 0.433 | 224/76 | qwen3.5:397b |
| plainfile | C | 0.249 | 0.910 | 0.397 | 233/67 | qwen3.5:397b |
| no-memory | C | 0.000 | 1.000 | 0.223 | 300/0 | qwen3.5:397b |

Still running: openmemory, mcp-knowledge-graph, memori, memvid, full-context,
then the extraction-heavy Tier A batch.

### OPEN track — per category (answerable)

| Tool | multi-hop | temporal | open-domain | single-hop |
|------|-----------|----------|-------------|------------|
| basic-memory | 0.116 | 0.229 | 0.067 | 0.480 |
| obsidian | 0.023 | 0.375 | 0.133 | 0.402 |
| naive-rag | 0.140 | 0.000 | 0.200 | 0.480 |
| plainfile | 0.093 | 0.000 | 0.133 | 0.409 |
| no-memory | 0.000 | 0.000 | 0.000 | 0.000 |

The temporal column keeps telling the same story: the three tools that put
timestamps where the answering model can see them (obsidian, basic-memory, and
later the graph/profile tools) score on temporal questions; the two that bury
timestamps in metadata (plainfile, naive-rag) score 0.000. Answerer/judge are
deepseek-v4-pro / qwen3.5:397b via Ollama Cloud; main-track Claude numbers
land separately.

### Finding: timestamp visibility is worth ~37 temporal points by itself

plainfile and obsidian use the same naive keyword search — yet obsidian scores
0.375 on temporal questions where plainfile scores 0.000. The only difference:
obsidian's notes inline each turn's timestamp into the retrieved text, so the
answering model can see dates and resolve "when did X happen." plainfile keeps
timestamps in metadata the answerer never receives.

If you build or operate agent memory: **putting timestamps inside the
retrieved text is the cheapest temporal-reasoning upgrade available** — no
graph, no extraction, no LLM in the write path. We record this as a finding
rather than retro-tuning the adapters; the series stays internally consistent.

Raw run summaries: [`data/benchmarks/`](../data/benchmarks/).
