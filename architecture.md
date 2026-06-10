# Architecture atlas

How the agent-memory landscape is shaped, and how the Quest tests it.
(Diagrams render natively on GitHub.)

## The four architectural shapes

Every tool on the roster, whatever its marketing, resolves to one of four
write-path designs — plus the MCP layer that cuts across them:

```mermaid
flowchart TD
    T[conversation turns] --> EX & GR & PR & OS

    subgraph EX[1 · Fact extractors]
        direction TB
        ex1[LLM extracts salient facts] --> ex2[reconcile: ADD / UPDATE / DELETE / NOOP] --> ex3[(vector store)]
    end
    subgraph GR[2 · Graph builders]
        direction TB
        gr1[LLM extracts entities + relations] --> gr2[temporal edges<br/>valid_at / invalid_at] --> gr3[(graph db)]
    end
    subgraph PR[3 · Profile / user-modelers]
        direction TB
        pr1[LLM updates a structured profile] --> pr2[(profile + event log)]
    end
    subgraph OS[4 · OS-style managers]
        direction TB
        os1[agent loop manages its own memory] --> os2[core blocks ↔ archival store] --> os3[(paged storage)]
    end

    EX -.-> M[Mem0 · Memori]
    GR -.-> G[Graphiti · Cognee · Hindsight]
    PR -.-> P[Memobase · Honcho]
    OS -.-> O[Letta · MemOS]

    style EX fill:#fbe9e2,stroke:#c1502e
    style GR fill:#fbe9e2,stroke:#c1502e
    style PR fill:#fbe9e2,stroke:#c1502e
    style OS fill:#fbe9e2,stroke:#c1502e
```

**Tier B (MCP servers)** — Basic Memory, OpenMemory, mcp-knowledge-graph,
claude-mem — skip the in-tool LLM entirely: *the calling agent* is the
extractor, and the server provides storage + search. Cheap and
client-agnostic, but quality depends on whoever is calling. Memvid is its own
category: an **archive format** (encode corpus → video + index; no
incremental writes).

## How the Quest tests a tool

Same harness for all twenty; the judge was frozen before any tool ran:

```mermaid
flowchart LR
    subgraph Adapter[frozen MemoryAdapter contract]
        direction LR
        A["add()<br/>store turns"] --> B["await_ingest()<br/>async barrier — lag measured"]
        B --> C["search()<br/>injectable context"]
    end
    C --> D[answering model<br/>same for every tool]
    D --> E{deterministic<br/>grader}
    E -->|exact-match types| V[verdict]
    E -->|free-form| J[LLM judge · frozen prompts<br/>+ failure-mode taxonomy]
    J -->|confidence < 0.7| J2[second independent pass]
    J --> V
    J2 --> V
    V --> L[(raw results JSON<br/>published)]

    T[telemetry: latency · tokens · $ per call] -.-> A & B & C

    style Adapter fill:#e8eef2,stroke:#2e6f95
```

The `await_ingest()` barrier is where async-ingestion designs (Graphiti's
graph extraction, Cognee's cognify, Honcho's deriver queue, Memobase's flush,
Memvid's full re-encode) get their cost measured instead of hidden.

## Current readings

![Smoke-gate latency by tool](assets/smoke-latency-2026-06.png)

![The landscape — adoption vs activity](assets/landscape-2026-06.png)
