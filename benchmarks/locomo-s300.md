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
| plainfile | C | | | | running |
| obsidian | C | | | | queued |
| naive-rag | C | | | | queued |
| full-context | C (ceiling) | | | | running |
| basic-memory | B | | | | queued |
| openmemory | B | | | | queued |
| mcp-knowledge-graph | B | | | | queued |
| memori | A | | | | queued |
| memvid | A | | | | queued |
| mem0 · letta · graphiti · cognee · honcho · memobase · langmem · hindsight · memos | A | | | | extraction-heavy batch — scheduled |

*Answer/judge transports for these runs: OpenRouter (Anthropic-native batch
grading pending a key; transport is stamped in every run's metadata per the
methodology).*
