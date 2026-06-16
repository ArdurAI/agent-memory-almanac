# Implementation Guide

How the Agent Memory Almanac is built, how to add a tool, how to update an edition, and how the data pipeline works.

## Table of Contents

1. [Repository Structure](#repository-structure)
2. [The Data Pipeline](#the-data-pipeline)
3. [Adding a New Memory Tool](#adding-a-new-memory-tool)
4. [Updating an Edition](#updating-an-edition)
5. [The Roster JSON Schema](#the-roster-json-schema)
6. [Directory Conventions](#directory-conventions)
7. [Building the Adapter](#building-the-adapter)
8. [Automation](#automation)

---

## Repository Structure

```
agent-memory-almanac/
├── README.md                          # Project overview + roster at a glance
├── INTENT.md                          # Philosophy, design principles, governance
├── IMPLEMENTATION.md                  # This file
├── TESTING.md                         # Benchmark methodology, harness details
├── TROUBLESHOOTING.md                 # Common issues, debugging, FAQ
├── CONTRIBUTING.md                      # How to contribute
├── architecture.md                    # Stack architecture + latency charts
├── methodology.md                     # Full testing methodology spec
├── published-vs-reproduced.md         # Vendor claims vs. independent results
├── SETUP.md                           # How to push to GitHub
├── .gitignore
│
├── editions/                          # Monthly editions
│   └── 2026-06.md                   # Founding edition
│
├── benchmarks/                        # Benchmark results (rolling)
│   └── (populated as results land)
│
├── data/
│   ├── roster.json                  # Machine-readable catalog
│   └── benchmarks/                  # Raw benchmark results
│
├── tools/                             # Per-tool deep-dive pages
│   └── (populated as deep-dives are written)
│
├── harness/                           # Benchmark harness code
│   ├── adapter.py                   # MemoryAdapter contract
│   ├── judge.py                     # Grading pipeline
│   ├── runner.py                    # Benchmark runner
│   ├── requirements.txt             # Dependencies
│   ├── .env.example                 # Environment template
│   └── adapters/                    # Per-tool adapters
│       └── (populated as adapters are written)
│
└── assets/                            # Charts, diagrams, screenshots
    └── (populated by editions)
```

## The Data Pipeline

The almanac data flows through four stages:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Discovery      │────▶│  Triage         │────▶│  Research       │────▶│  Publication    │
│  (find tools)   │     │  (decide entry) │     │  (deep dive)    │     │  (write edition) │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Stage 1: Discovery

Tools are discovered through:
- **Monthly research swarm**: Parallel agents search for new memory tools
- **Community submissions**: Issues, PRs, email, social media
- **Vendor announcements**: Funding rounds, product launches, major releases
- **GitHub trending**: New repos with significant star growth
- **Conference talks**: Papers, demos, blog posts from major events

### Stage 2: Triage

A tool enters the roster if it meets ALL of these criteria:
1. **Seriousness**: Not a toy/demo. Must have a real use case, real users, or real funding.
2. **Activity**: Last push or release within 6 months. Exceptions for "stable/mature" tools.
3. **Documentation**: Must have a README, docs, or at least a landing page explaining what it does.
4. **Accessibility**: Must be accessible to test (open source, free tier, or evaluation license available).
5. **Scope**: Must be an agent memory tool (not a general RAG framework or vector database).

A tool is **excluded** if:
- It's a fork with no meaningful divergence from the parent
- It's a wrapper around another tool with no added value
- It has no users, no community, and no evidence of real-world use
- It requires an enterprise-only license with no evaluation path

### Stage 3: Research

For each new tool, we collect:
- Name, type, license, language, GitHub URL, stars
- Last push date, release cadence
- Key features and differentiators (graph vs. vector vs. hybrid vs. file-based)
- Known bugs and sharp edges (from smoke gate)
- Community health (issues, PRs, maintainer responsiveness)

This data is stored in `data/roster.json` and summarized in the edition.

### Stage 4: Publication

The edition is a markdown file that includes:
- Landscape at a glance table
- Tiered roster with notes
- Per-tool deep-dive summaries
- Benchmark results and trends
- New tools added and tools removed
- Quest diary (what was tested this month)

## Adding a New Memory Tool

### Step 1: Verify the tool meets triage criteria

Check: seriousness, activity, documentation, accessibility, scope. The tool must be an **agent memory tool** — not a general RAG framework or vector database.

### Step 2: Build the adapter

Every tool on the roster needs an adapter implementing the `MemoryAdapter` contract:

```python
class MemoryAdapter(ABC):
    def add(self, conversation_turns: list[dict]) -> None
    def await_ingest(self, timeout_sec: float = 60.0) -> float
    def search(self, query: str, k: int = 5) -> list[str]
    def export(self) -> dict
    def wipe(self) -> None
```

**Adapter rules:**
- No mocks: the adapter must call the real tool, not a stub
- No caching across runs: `wipe()` must return a clean state
- No answer leakage: the adapter must not use the gold answer or question category
- `await_ingest()` must measure real async lag, not return 0 if the tool has async ingestion

**Steps:**
1. Read `harness/adapter.py` to understand the contract
2. Create `harness/adapters/<tool_name>.py`
3. Implement all abstract methods
4. Add your adapter to `_load_adapter()` in `harness/runner.py`
5. Test with the no-memory benchmark first to validate the harness, then with your tool

### Step 3: Run the smoke gate

Before the tool is officially "in," it must pass the smoke gate:

```
Turn 1: Store a piece of data (conversation turns)
Turn 2: Search/retrieve that data
Turn 3: Update the data and verify the change
```

**Pass criteria**:
- No crashes, no silent failures, no data loss
- Results must be deterministic (same input → same output)
- Tool must handle the basic case without workarounds
- `await_ingest()` must return a realistic latency, not 0

**What the smoke gate surfaced** (from the founding edition):
- Privacy bugs: Redis cache serving deleted data until TTL expires
- Cross-project contamination: Tool writing to a global shared store
- Dependency drift: Direct conflicts between tools on the same dependency
- Cloud tethers: "Self-hosted" tool still calling cloud APIs
- Write-path spread: Sub-millisecond to ~35 seconds for 3 turns

### Step 4: Add to the roster JSON

Edit `data/roster.json` and add the tool:

```json
{
  "name": "ToolName",
  "type": "framework|mcp-server|baseline",
  "license": "License",
  "tier": "A|B|C",
  "notes": "One-line description and key differentiators"
}
```

**Tier assignment rules**:
- **Tier A**: Market leader, widest adoption, or strongest technical merit. Must be actively maintained and have real production usage.
- **Tier B**: Solid option, actively maintained, but not the market leader. Good for specific use cases.
- **Tier C**: Niche, early-stage, or specialized. Worth knowing about but not a default choice.
- **Baselines**: The control group (naive RAG, full-context stuffing, no memory, etc.) — always Tier C by definition.

### Step 5: Update the edition

Add the tool to `editions/YYYY-MM.md`. If the tool is Tier A, update the README roster-at-a-glance.

### Step 6: Write the per-tool page

Create `tools/<tool_name>.md` with:
- Setup experience (time, dependencies, friction)
- Smoke gate results (bugs found, if any)
- Benchmark results (when available)
- Comparison with peers
- Known issues and limitations

## Updating an Edition

### Monthly update checklist

```
□ Check for new tools (discovery phase)
□ Triage new tools (add to roster or reject)
□ Update metadata for existing tools (stars, last push, releases)
□ Flag tools for removal (dead/abandoned)
□ Run smoke gate for new tools
□ Run benchmark updates for re-tested tools
□ Draft the edition markdown
□ Update README roster-at-a-glance
□ Commit and push
```

### Edition markdown template

```markdown
# Edition YYYY-MM — [Title]

*Research conducted YYYY-MM-DD. [Context about this month].*

## The landscape at a glance

| Tier | Tool Count | New This Month | Notable Changes |
|------|-----------|----------------|-----------------|

## Tier A — [Theme]

[Tool names with notes]

## Tier B — [Theme]

[Tool names with notes]

## Tier C — [Theme]

[Tool names with notes]

## Quest diary — [Month] [Year]

- [what was done]

## Coming next month

[what's planned]

## License
Content is licensed CC BY 4.0.
```

## The Roster JSON Schema

```json
{
  "meta": {
    "name": "Agent Memory Almanac Roster",
    "version": "YYYY-MM",
    "generated_at": "ISO-8601 timestamp",
    "total_tools": number,
    "research_method": "description"
  },
  "tools": [
    {
      "name": "Tool Name",
      "type": "framework|mcp-server|baseline",
      "license": "License",
      "tier": "A|B|C",
      "notes": "Description"
    }
  ]
}
```

**Field definitions**:
- `name`: The tool's common name. Use the name the tool calls itself.
- `type`: `framework` (agent memory framework), `mcp-server` (MCP memory server), or `baseline` (control group)
- `license`: The primary license. Use SPDX identifiers where possible.
- `tier`: A, B, or C (see tier rules above)
- `notes`: One-line description with key differentiators. Keep under 100 chars.

## Directory Conventions

### `editions/`
- One file per month: `YYYY-MM.md`
- Never delete old editions. The history is part of the record.
- New editions are appended; old editions are never rewritten.

### `data/`
- `roster.json` is the single source of truth for the tool catalog.
- `benchmarks/` contains raw results JSON files.
- It is machine-generated from the research process.
- It should be valid JSON at all times.

### `benchmarks/`
- One file per benchmark run: `<tool>-<suite>-<date>.md`
- Raw JSON files alongside the markdown: `<tool>-<suite>-<date>.json`
- Raw data is never deleted. It is the audit trail.

### `tools/`
- One file per tool: `<name>.md`
- Contains deep-dive analysis: setup experience, benchmark results, bug notes, comparison with peers
- Populated as deep-dives are written (not all tools have a page immediately)

### `harness/`
- The benchmark harness code.
- `adapter.py` defines the `MemoryAdapter` contract.
- `adapters/` contains one adapter per tool.
- The harness is open-source and published alongside the almanac.

### `assets/`
- Images, charts, diagrams referenced by editions and benchmarks
- Named descriptively: `landscape-2026-06.png`, `latency-p50-2026-06.png`

## Building the Adapter

The adapter is the bridge between the tool's API and the harness's fixed `MemoryAdapter` interface.

### Adapter rules

1. The adapter must be **pure** — it should not modify the tool's behavior, only interface with it.
2. The adapter must be **documented** — every step should be explainable in plain English.
3. The adapter must be **reproducible** — running it twice on the same machine should produce the same setup.
4. The adapter must be **isolated** — it should not depend on other tools' adapters.
5. The adapter code is **published** in the `harness/adapters/` directory.

### Example adapter (pseudocode)

```python
class BasicMemoryAdapter(MemoryAdapter):
    def __init__(self):
        self.client = BasicMemory()
    
    def add(self, conversation_turns: list[dict]) -> None:
        for turn in conversation_turns:
            self.client.add_turn(turn["role"], turn["content"])
    
    def await_ingest(self, timeout_sec: float = 60.0) -> float:
        # BasicMemory is synchronous, so this is a no-op
        return 0.0
    
    def search(self, query: str, k: int = 5) -> list[str]:
        return self.client.search(query, top_k=k)
    
    def export(self) -> dict:
        return self.client.export()
    
    def wipe(self) -> None:
        self.client.wipe()
```

### Async ingestion adapters

For tools with async ingestion (e.g., graph extraction, background indexing, derivation queues), the `await_ingest()` method is critical:

```python
class GraphitiAdapter(MemoryAdapter):
    def add(self, conversation_turns: list[dict]) -> None:
        for turn in conversation_turns:
            self.client.add_turn(turn["role"], turn["content"])
    
    def await_ingest(self, timeout_sec: float = 60.0) -> float:
        start = time.monotonic()
        # Wait for graph extraction to complete
        while self.client.is_processing():
            if time.monotonic() - start > timeout_sec:
                raise TimeoutError("Graph extraction did not complete")
            time.sleep(0.1)
        return time.monotonic() - start
    
    def search(self, query: str, k: int = 5) -> list[str]:
        return self.client.search(query, top_k=k)
    
    def export(self) -> dict:
        return self.client.export()
    
    def wipe(self) -> None:
        self.client.wipe()
```

## Automation

### Monthly update cron

The monthly update is run by a scheduled job:
- **Trigger**: `cron` expression (configured in the Kimi Work scheduler)
- **Action**: Runs a research agent to discover new tools, update metadata, and draft the next edition
- **Output**: Commits to the repo with the updated roster and new edition

### GitHub Actions (optional)

For automatic metadata refresh (GitHub stars, last push dates), a GitHub Actions workflow can be configured. See `SETUP.md` for the template.

## License

Content: CC BY 4.0  
Code: MIT
