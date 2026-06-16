# Testing & Benchmarking

How the Agent Memory Almanac tests tools, what the harness does, how scoring works, and how to reproduce results.

## Table of Contents

1. [The Three Benchmark Types](#the-three-benchmark-types)
2. [The Seven Dimensions](#the-seven-dimensions)
3. [The Harness Architecture](#the-harness-architecture)
4. [The Canary](#the-canary)
5. [Standard Benchmarks](#standard-benchmarks)
6. [PlatformOps-Mem Benchmark](#platformops-mem-benchmark)
7. [Stress Suite](#stress-suite)
8. [Scoring](#scoring)
9. [Reproducibility](#reproducibility)
10. [Failure Mode Taxonomy](#failure-mode-taxonomy)
11. [Full Methodology](#full-methodology)

---

## The Three Benchmark Types

Every memory tool is tested across three types of benchmarks:

| Type | Purpose | Frequency |
|------|---------|-----------|
| **Standard benchmarks** | Verify vendor claims with published test suites | Every benchmark run |
| **PlatformOps-Mem** | Test memory on actual platform engineering work | Every benchmark run |
| **Stress suite** | Reveal failure modes under pathological conditions | Every benchmark run |

## The Seven Dimensions

Every tool is scored 0-100 on each dimension. The final score is the average of the seven dimensions. All seven are weighted equally because no single dimension captures "good memory infrastructure."

| Dimension | Weight | What it measures | How it's tested |
|-----------|--------|-----------------|-----------------|
| **Retrieval accuracy** | 14.3% | Does it find the right memory when needed? | LoCoMo + PlatformOps-Mem accuracy |
| **Latency** | 14.3% | Time to store, ingest, and retrieve | Instrumented p50, p95, p99 across all operations |
| **Token economics** | 14.3% | Cost per memory operation as corpus grows | Total tokens per question (tool + answering + judging) |
| **Scale behavior** | 14.3% | What happens at 10x, 100x conversation history? | Stress suite: cost_runaway from 10 to 1000 turns |
| **Ops burden** | 14.3% | Services, dependencies, backup, upgrade, debug | Measured setup time + ops notes rubric |
| **Developer experience** | 14.3% | Time-to-first-memory, docs, debuggability, community | Structured rubric + community health metrics |
| **Data sovereignty** | 14.3% | Self-hosting, export, audit, compliance | Feature matrix + data leakage testing |

### Why equal weights?

Memory infrastructure is a balance. A tool that is extremely accurate but requires a 10-service cluster is not obviously better than a slightly less accurate tool that runs in a single container. The equal weights force trade-offs to be visible.

## The Harness Architecture

```
┌─────────────────────────────────────────┐
│  MemoryAdapter (frozen contract)          │
│  ├── add()       → store conversation    │
│  ├── await_ingest() → measure async lag  │
│  ├── search()    → retrieve memories     │
│  ├── export()    → dump state for audit  │
│  └── wipe()      → clean state           │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Telemetry Collector                    │
│  ├── latency (p50/p95/p99)             │
│  ├── token count & cost                  │
│  ├── memory & CPU usage                 │
│  ├── error rate & failure mode taxonomy │
│  └── ops notes (setup time, deps, bugs)  │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Grading Pipeline                         │
│  ├── Deterministic grader (exact match)  │
│  ├── LLM judge (frozen prompts, SHA-256)  │
│  ├── Second pass (confidence < 0.7)      │
│  └── Failure mode taxonomy               │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Results Publisher                        │
│  ├── Raw JSON (per question, per run)     │
│  ├── Summary tables (per tool)            │
│  ├── Cross-verification analysis            │
│  └── Insight extraction                   │
└─────────────────────────────────────────┘
```

### The `await_ingest()` barrier

This is where async-ingestion designs get their cost measured instead of hidden. Tools like Graphiti (graph extraction), Cognee (cognify), Honcho (deriver queue), and Memobase (flush) report "instant" writes but take seconds or minutes to actually make data retrievable. The `await_ingest()` barrier captures this true latency.

### The Telemetry Collector

Every adapter call is instrumented:
- **Latency**: `time.monotonic()` around every call; p50, p95, p99 computed across all runs
- **Tokens**: Total token consumption (tool-internal + answering model + judge model)
- **Cost**: Token counts × provider pricing
- **Memory**: `psutil` or container metrics for memory usage during the run
- **Errors**: Every exception, timeout, or unexpected result is logged with full traceback
- **Ops notes**: Human observations about setup friction, dependency conflicts, documentation quality

## The Canary

The first run of every batch is the **no-memory baseline** (the "canary"). If the benchmark leaked answers anywhere, the canary would score above zero on answerable categories.

**Canary rules**:
- The canary must score exactly **0.000** on all answerable categories (categories 1–4)
- The canary must score exactly **1.000** on the adversarial category (category 5) — it should abstain on everything
- If the canary fails, the entire batch is invalid and must be rerun
- The canary run is published alongside the real results
- The canary adapter is a no-op: `add()` does nothing, `search()` returns nothing, `await_ingest()` returns 0

## Standard Benchmarks

### LoCoMo

[LoCoMo](https://github.com/snap-research/locomo): 1,986 questions over 10 multi-session conversations. The Quest uses a stratified 300-question sample (seed 42) for rapid iteration, with full-1,986 runs for published numbers.

**Categories:**
- 1: multi-hop (43) — requires connecting facts across sessions
- 2: temporal (48) — requires reasoning about event ordering
- 3: open-domain (15) — requires general knowledge + memory
- 4: single-hop (127) — direct recall from a single session
- 5: adversarial (67) — correct answer is to abstain

**Why the adversarial category matters:**
A tool that remembers nothing abstains on everything, scoring a free 22% on overall. We therefore report:
- **Answerable** (categories 1–4): the memory actually working
- **Abstention** (category 5): knowing what it doesn't know
- **Overall**: the blended number most vendors quote

**Pipeline:**
1. Each tool really ingests all 10 conversations through its own write path
2. Really retrieves per question
3. A frozen answering model sees **only the retrieved excerpts** — never gold answers or categories
4. Graded by deterministic rules first (including the adversarial-category abstention check)
5. Frozen LLM judge for the ambiguous rest
6. Confidence < 0.7 triggers a second independent pass
7. Raw per-question records (excerpts, verbatim answers, token usage) are persisted for every run

**Tracks:**
- **Main track**: answerer `claude-sonnet-4-6`, judge `claude-opus-4-8`, both via OpenRouter
- **Open track**: answerer `deepseek-v4-pro`, judge `qwen3.5:397b`, both via Ollama Cloud
- Open-track runs are **never merged or compared head-to-head** with main-track rows

### LongMemEval

A complementary benchmark for long-context memory evaluation. Used for cross-verification and for tools that claim long-context superiority.

## PlatformOps-Mem Benchmark

The benchmark that makes the Quest unique. Tests memory on the actual work of a platform engineer:

1. **infra-continuity** — troubleshooting a problem across multiple sessions
2. **state-mutation** — remembering that infrastructure state has changed
3. **runbook-recall** — retrieving the correct runbook for a given alert
4. **cross-project-isolation** — ensuring memories from project A don't leak into project B
5. **incident-reconstruction** — reconstructing the timeline of a past incident

Each scenario is a realistic multi-turn conversation with embedded questions. The answering model sees only retrieved excerpts. Grading is deterministic + LLM judge, same pipeline as LoCoMo.

## Stress Suite

Pathological conditions that surface how a tool actually behaves in production:

| Test | What it does | What it reveals |
|------|-------------|---------------|
| **contradiction_storm** | Rapidly alternating facts | Does the tool reconcile or append? |
| **duplicate_flood** | 100 near-identical turns | Does retrieval drown in noise? |
| **temporal_paradox** | Facts that change over time | Does the tool preserve history? |
| **concurrent_writers** | Two agents writing simultaneously | Race conditions, locking, consistency |
| **kill_the_backing_store** | Crash and restart | Does the tool recover state? |
| **cost_runaway** | Corpus grows from 10 to 1000 turns | Cost predictability, billing accuracy |

Every scenario produces a pass/fail verdict plus a failure-mode taxonomy classification.

## Scoring

### Per-dimension scoring

Each dimension is scored 0-100 using a rubric. The rubric is published before any scoring happens.

**Example: Retrieval accuracy rubric**

| Score | Criteria |
|-------|----------|
| 90-100 | ≥85% on LoCoMo answerable + ≥80% on PlatformOps-Mem |
| 80-89 | 75-85% on LoCoMo answerable + 70-80% on PlatformOps-Mem |
| 70-79 | 65-75% on LoCoMo answerable + 60-70% on PlatformOps-Mem |
| 60-69 | 55-65% on LoCoMo answerable + 50-60% on PlatformOps-Mem |
| 50-59 | 45-55% on LoCoMo answerable + 40-50% on PlatformOps-Mem |
| 0-49 | <45% on LoCoMo answerable or <40% on PlatformOps-Mem |

### Composite score

The composite score is the average of the seven dimension scores:

```
Composite = (Accuracy + Latency + TokenEconomics + ScaleBehavior + OpsBurden + DevEx + DataSovereignty) / 7
```

The composite is used for ranking, but the per-dimension scores are always published. A tool with a high composite but low ops burden score is a warning sign.

### Confidence intervals

Every score is reported with a confidence interval computed from the standard error across runs. If the intervals overlap between two tools, the difference is not statistically significant.

## Reproducibility

### How to reproduce a benchmark

1. Clone the repo: `git clone https://github.com/ArdurAI/agent-memory-almanac.git`
2. Install dependencies: `pip install -r harness/requirements.txt`
3. Configure providers: copy `harness/.env.example` to `harness/.env` and add API keys
4. Download LoCoMo data from https://github.com/snap-research/locomo and place at `data/locomo.json`
5. Run the benchmark: `python -m harness.runner --benchmark locomo --tool <tool_name> --sample locomo-s300-seed42 --track open`
6. Compare your results to the published results in `benchmarks/`

### What is frozen

| Element | How it's frozen | Where to find it |
|---------|---------------|------------------|
| Judge model | Pinned model name and version | `methodology.md` and `results.json` metadata |
| Judge prompts | SHA-256 hash | `methodology.md` |
| Control variables | Documented values | `results.json` metadata |
| Random seeds | Published integer | `results.json` metadata (seed 42 for LoCoMo) |
| Adapter code | Published in `harness/adapters/` | This repo |
| Test workloads | Published JSON files | `data/` directory |

### What is NOT frozen (and why)

| Element | Why it changes | How we handle it |
|---------|---------------|------------------|
| Tool versions | Tools update | We re-run benchmarks for new versions; old results are archived |
| Provider pricing | Cloud pricing changes | Cost is computed at runtime using current pricing; historical results are annotated |
| Hardware | We may upgrade machines | Hardware spec is recorded in `results.json`; results are hardware-specific |

## Failure Mode Taxonomy

Every incorrect answer is classified into one of seven failure modes:

| Failure mode | Meaning | Example |
|-------------|---------|---------|
| **missing_recall** | Retrieval returned nothing or irrelevant context | Model says "I don't know" because the memory tool failed to retrieve |
| **wrong_fact** | Model gave a specific incorrect answer | Retrieved context contained an outdated fact |
| **wrong_abstention** | Model abstained when it should have answered | Tool failed to retrieve context the model needed |
| **partial** | Model gave a partially correct answer | Retrieved only half the needed context |
| **hallucination** | Model invented information not in the source | Model ignored retrieved context and made something up |
| **cross_project_leak** | Retrieved data from a different project | Tool lacks proper isolation |
| **none** | Correct answer — no failure | |

The failure-mode distribution is published for every tool. This reveals *how* a tool fails, not just *whether* it fails.

## Full Methodology

This document is a summary. The complete, frozen methodology specification is in [`methodology.md`](methodology.md). It includes:
- The exact adapter interface
- The exact judge model and prompts (with SHA-256 stamps)
- The exact answering model strings
- The exact LoCoMo sampling policy
- The exact control variables
- The exact scoring rubrics
- The exact failure-mode taxonomy definitions

The methodology was locked on **2026-06-09** before any tool was evaluated.

## License

Content: CC BY 4.0  
Code: MIT
