# Project Intent & Philosophy

## Why this almanac exists

Agent memory is the most under-tested layer of the AI infrastructure stack. Every agent framework claims to "remember conversations," but what that actually means ranges from "appends to a text file" to "builds a knowledge graph with temporal reasoning." The accuracy claims are inflated, the latency numbers are theoretical, and the failure modes are undocumented.

This almanac exists because nobody independently verifies memory tools the way a platform engineer has to live with them: ops burden, failure modes, scale curves, cost, and real-world edge cases. It is the **public record of independent verification** for agent memory systems.

## Core principles

### 1. Frozen methodology before results

The harness, judge model, prompts, and scoring rubric are **fixed and published before any tool is tested**. This prevents "cherry-picking" the methodology that favors a particular vendor. If a tool doesn't fit the harness, we adapt the adapter — not the rules.

### 2. The two-bar test

Every memory tool must clear two bars to justify its existence:
- **Beat naive RAG on accuracy** — if the tool doesn't retrieve better than chunk + embed + cosine, why use it?
- **Beat full-context stuffing on cost** — if the tool costs more than sending the entire conversation every time, why use it?

A tool that can't do both is **not justified** as infrastructure.

### 3. Ops-first evaluation

Most benchmarks measure accuracy or throughput. We measure **what a platform engineer actually lives with**:
- Time from `git clone` to first working memory
- Dependency conflicts when installing alongside other tools
- Time to debug when the tool silently loses data
- Upgrade pain when version N → N+1 breaks everything
- Cost predictability as the memory corpus grows

### 4. Raw data is always published

Every benchmark run produces a JSON file with every question, every answer, every token count, every latency measurement. These raw files are published alongside the summary. If you disagree with a ranking, you can re-analyze the data yourself.

### 5. No tool is above criticism

Every tool on the roster has been through a smoke gate. Every tool has bugs. We document them honestly. A vendor relationship or sponsorship does not influence rankings. The only way a tool improves its score is by actually improving.

### 6. Living document, not a static snapshot

The almanac is updated monthly. Tools enter and exit the roster. Scores change as tools improve or degrade. The "founding edition" is a snapshot; the current edition is the truth.

## Design philosophy

### The seven dimensions

We score every tool on seven dimensions because no single number captures "good memory infrastructure":

| Dimension | Why it matters |
|-----------|---------------|
| **Retrieval accuracy** | Does it find the right memory when needed? |
| **Latency** | Does it respond fast enough for real-time agents? |
| **Token economics** | Does it cost what you expect as memory grows? |
| **Scale behavior** | What happens when you 10x the conversation history? |
| **Ops burden** | How much of your life does it consume? |
| **Developer experience** | Is it pleasant or painful to use? |
| **Data sovereignty** | Can you run it yourself? Audit it? Export data? |

### The `await_ingest()` barrier

This is the critical design element that separates this almanac from marketing benchmarks. Many memory tools (graph builders, vector databases with background indexing, async derivation queues) claim "instant" writes because the actual work happens in the background. The `await_ingest()` barrier forces the tool to finish all background work before retrieval is measured, so the **true latency** is captured.

### The canary

Every benchmark batch starts with a **no-memory baseline** (the "canary"). If the benchmark leaked answers anywhere, the canary would score above zero on answerable categories. The canary must score exactly **0.000** — this is a hard invariant. If it doesn't, the entire batch is invalid.

### Failure-mode taxonomy

Every incorrect answer is classified into a taxonomy. This reveals **how** a tool fails, not just **whether** it fails. The seven failure modes are:

| Failure mode | Meaning | Example |
|-------------|---------|---------|
| **missing_recall** | Retrieval returned nothing or irrelevant context | Model says "I don't know" because the memory tool failed to retrieve |
| **wrong_fact** | Model gave a specific incorrect answer | Retrieved context contained an outdated fact |
| **wrong_abstention** | Model abstained when it should have answered | Tool failed to retrieve context the model needed |
| **partial** | Model gave a partially correct answer | Retrieved only half the needed context |
| **hallucination** | Model invented information not in the source | Model ignored retrieved context and made something up |
| **cross_project_leak** | Retrieved data from a different project | Tool lacks proper isolation |
| **none** | Correct answer — no failure | |

## Who this is for

- **Agent developers** choosing which memory system to integrate
- **Platform engineers** evaluating memory infrastructure for production
- **CTOs/CIOs** making build-vs-buy decisions with actual data
- **Open-source maintainers** who want independent benchmarking of their project
- **Researchers** studying agent memory architectures

## What this is NOT

- Not a tutorial on how to use any memory tool
- Not a "best of" list based on GitHub stars or funding rounds
- Not a replacement for your own due diligence
- Not a static document that never changes

## The "Quest"

The "Platform Engineer's Quest for the Best" is the ongoing effort to test, measure, and rank every memory tool on the roster. It's a continuous process of:
1. **Discovery** — finding new tools via research, community, and submissions
2. **Triage** — deciding if a tool is serious enough to enter the roster
3. **Smoke gate** — running every tool through an identical 3-turn scenario to catch bugs
4. **Benchmark** — running LoCoMo, PlatformOps-Mem, and stress tests
5. **Publication** — publishing raw data + summary + per-tool deep-dives
6. **Iteration** — re-testing as tools update, as methodology improves, as new benchmarks emerge

## How to challenge a result

If you believe a ranking or score is wrong:
1. Check the **raw results JSON** — the data is public
2. Check the **adapter implementation** — the adapter code is public
3. Check the **judge prompts** — the prompts are frozen and public
4. File an issue with a specific claim and evidence
5. We'll re-run the test or update the methodology if warranted

## Governance

- **ArdurAI** maintains the almanac and runs the Quest
- **Methodology changes** require a public RFC and at least one edition cycle of notice
- **Tool additions/removals** are decided by the triage criteria (stars, last push, community activity, seriousness)
- **Benchmark results** are machine-generated; summaries are human-reviewed for fairness
- **Conflicts of interest** are disclosed (ArdurAI contributes to Honcho, which is on the roster); mitigation is identical harness for all

## License

Content: CC BY 4.0  
Harness code: MIT  
Raw data: CC BY 4.0
