# Methodology: How the Quest Tests Memory Tools

The Agent Memory Almanac is built on a single principle: **the methodology must be frozen before any tool runs.** This prevents the classic benchmark failure mode where the test is tweaked until the desired result appears.

This document is the complete specification of the Quest's testing methodology. It was written and locked on **2026-06-09** before any tool was evaluated.

---

## The frozen-before-results rule

The following elements were fixed on 2026-06-09 and are SHA-256-stamped in every result:

1. **Adapter interface** (`harness/adapter.py`) — the single point of control between the harness and every tool
2. **Judge model and prompts** (`harness/judge.py`) — deterministic rules + LLM judge pipeline
3. **Answering model** — per track, pinned to exact model strings
4. **LoCoMo sampling policy** — seed 42, stratified 300-question sample
5. **Control variables** — same tool-internal LLM wherever the tool is configurable
6. **Failure-mode taxonomy** — seven categories, defined below
7. **Scoring dimensions** — seven dimensions, weighted equally

**No element was changed after the first tool ran.** If a bug is found in the harness, it is documented and fixed for the *next* edition's methodology lock, not retroactively applied to past results.

---

## The bar every tool must clear

A memory tool has **no reason to exist** unless it beats both baselines:

- **naive RAG** on **accuracy** — if the tool doesn't retrieve better than chunk + embed + cosine, why use it?
- **full-context stuffing** on **cost** — if the tool costs more than just sending the entire conversation to the model every time, why use it?

Tools that fail to clear both bars are documented as **not justified**.

---

## The adapter contract

Every tool on the roster speaks through the same `MemoryAdapter` interface:

```python
class MemoryAdapter(ABC):
    def add(self, conversation_turns: list[dict]) -> None
    def await_ingest(self, timeout_sec: float = 60.0) -> float
    def search(self, query: str, k: int = 5) -> list[str]
    def export(self) -> dict
    def wipe(self) -> None
```

**Design constraints:**
- No mocks: the adapter must call the real tool, not a stub
- No caching across runs: `wipe()` must return a clean state
- No answer leakage: the adapter must not use the gold answer or question category
- Telemetry is automatic: the harness wraps every method with timing

The `await_ingest()` barrier is critical. Async-ingestion designs (Graphiti's graph extraction, Cognee's cognify, Honcho's deriver queue, Memobase's flush) get their cost measured instead of hidden. A tool that reports "instant" writes but takes 30 seconds to actually make data retrievable is not instant — the harness captures this.

---

## Benchmarks

### 1. LoCoMo (standard comparability)

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

The first run of every batch is the **no-memory canary**. If the benchmark leaked answers anywhere, the canary would score above zero on answerable categories. The canary scored **0.000** on all 233 answerable questions — the benchmark does not leak.

**Pipeline:**
1. Each tool really ingests all 10 conversations through its own write path
2. Really retrieves per question
3. A frozen answering model sees **only the retrieved excerpts** — never gold answers or categories
4. Graded by deterministic rules first (including the adversarial-category abstention check)
5. Frozen LLM judge (`claude-opus-4-8`) for the ambiguous rest
6. Confidence < 0.7 triggers a second independent pass
7. Raw per-question records (excerpts, verbatim answers, token usage) are persisted for every run

**Tracks:**
- **Main track**: answerer `claude-sonnet-4-6`, judge `claude-opus-4-8`, both via OpenRouter
- **Open track**: answerer `deepseek-v4-pro`, judge `qwen3.5:397b`, both via Ollama Cloud
- Open-track runs are **never merged or compared head-to-head** with main-track rows — the answerer differs, so the tables differ

### 2. PlatformOps-Mem (Quest differentiator)

The benchmark that makes the Quest unique. Tests memory on the actual work of a platform engineer:

1. **infra-continuity** — troubleshooting a problem across multiple sessions
2. **state-mutation** — remembering that infrastructure state has changed
3. **runbook-recall** — retrieving the correct runbook for a given alert
4. **cross-project-isolation** — ensuring memories from project A don't leak into project B
5. **incident-reconstruction** — reconstructing the timeline of a past incident

Each scenario is a realistic multi-turn conversation with embedded questions. The answering model sees only retrieved excerpts. Grading is deterministic + LLM judge, same pipeline as LoCoMo.

### 3. Stress suite (failure modes)

Pathological conditions that surface how a tool actually behaves in production:

1. **contradiction_storm** — rapidly alternating facts; does the tool reconcile or append?
2. **duplicate_flood** — 100 near-identical turns; does retrieval drown in noise?
3. **temporal_paradox** — facts that change over time; does the tool preserve history?
4. **concurrent_writers** — two agents writing to the same memory simultaneously
5. **kill_the_backing_store** — crash and restart; does the tool recover state?
6. **cost_runaway** — measure token burn and latency as corpus grows from 10 to 1000 turns

Every scenario produces a pass/fail verdict plus a failure-mode taxonomy.

---

## Seven scoring dimensions

Every tool is scored on seven dimensions, weighted equally:

1. **Retrieval accuracy** — answerable accuracy on LoCoMo + PlatformOps-Mem
2. **Latency** — p50, p95, and p99 write-path latency (add + await_ingest + search)
3. **Token economics** — total tokens consumed per question (tool-internal + answering + judging)
4. **Scale behavior** — how latency and cost change from 10 to 1000 turns (stress suite)
5. **Ops burden** — services required, dependencies, backup/restore complexity, upgrade path
6. **Developer experience** — time-to-first-memory, documentation quality, debuggability
7. **Data sovereignty** — cloud dependency, data leakage risk, export portability

The overall score is the average of the seven dimension scores. No single dimension dominates.

---

## The judge pipeline

### Stage 1: Deterministic grader

For exact-match types and adversarial abstention checks:
- Exact string match (case-insensitive)
- Substring containment for short factual answers
- Abstention detection ("I don't know", "not sure", "insufficient information", etc.)
- Adversarial category: abstention is correct, any answer is wrong

### Stage 2: LLM judge

Frozen model (`claude-opus-4-8` on main track, `qwen3.5:397b` on open track). Frozen prompt (SHA-256 stamped). The judge sees:
- The question
- The ground-truth answer
- The model's answer
- The category

Output: correct (bool), confidence (0.0–1.0), failure_mode, reason.

### Stage 3: Second pass

If confidence < 0.7, a second independent pass runs. If the two passes disagree, the conservative fallback is **incorrect**.

---

## Failure-mode taxonomy

Every incorrect answer is classified into one of seven failure modes:

| Failure mode | Meaning | Example |
|-------------|---------|---------|
| **missing_recall** | Retrieval returned nothing or irrelevant context | Model says "I don't know" because the memory tool failed to retrieve the needed fact |
| **wrong_fact** | Model gave a specific incorrect answer | Retrieved context contained an outdated fact, or the model hallucinated |
| **wrong_abstention** | Model abstained when it should have answered | The tool failed to retrieve context the model needed, or the model was overly cautious |
| **partial** | Model gave a partially correct answer | Retrieved only half the needed context |
| **hallucination** | Model invented information not in the source | The model ignored retrieved context and made something up |
| **cross_project_leak** | Retrieved data from a different project | Tool lacks proper isolation |
| **none** | Correct answer — no failure | |

The failure-mode distribution is published for every tool. This reveals *how* a tool fails, not just *whether* it fails.

---

## Published vs. reproduced

Vendors publish their own benchmark numbers. For every tool with published claims, the Almanac includes a **published vs. reproduced** table:

| Benchmark | Vendor claims | Quest reproduces | Delta | Verdict |
|-----------|--------------|------------------|-------|---------|
| ... | ... | ... | ... | ... |

Deltas > 5 points are flagged for investigation. The Quest never assumes vendor malice — differences are often due to different model versions, sampling strategies, or evaluation protocols. The raw data is published so readers can judge for themselves.

---

## Disclosure

ArdurAI contributes to Honcho, which is on the roster. Mitigation:
- Identical harness for every tool
- Methodology frozen and published before results
- Raw data always published
- Honcho's tool entry includes the same disclosure

---

## License

This methodology document is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — share and adapt with attribution to **ArdurAI / Agent Memory Almanac**.
