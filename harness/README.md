# Quest Benchmark Harness

The frozen harness behind the *Agent Memory Almanac*.

Every tool on the roster runs through the same adapter interface, the same telemetry, the same judge, and the same answering model. Methodology was frozen before any tool ran; raw results JSON is published with every ranking.

## Architecture

```
harness/
  adapter.py           # Frozen MemoryAdapter contract — add(), await_ingest(), search()
  telemetry.py         # Per-call latency, token usage, cost tracking
  judge.py             # Deterministic grader + frozen LLM judge pipeline
  runner.py            # Orchestrator: setup → run → grade → emit results
  bench_locomo.py      # LoCoMo benchmark implementation
  stress_suite.py      # Stress test framework (contradictions, floods, chaos)
  bench_platformops.py # PlatformOps-Mem benchmark (infra continuity, etc.)
  adapters/            # Per-tool adapter implementations
  stress/              # Stress scenario definitions
  platformops/         # PlatformOps scenario definitions
  results/             # Run output (JSON + per-question records)
```

## The frozen contract

```python
from harness.adapter import MemoryAdapter

class MyToolAdapter(MemoryAdapter):
    def add(self, conversation_turns: list[dict]) -> None:
        """Store conversation turns through the tool's native write path."""
        pass

    def await_ingest(self, timeout_sec: float = 60.0) -> float:
        """Block until async ingestion is complete. Returns elapsed seconds."""
        pass

    def search(self, query: str, k: int = 5) -> list[str]:
        """Retrieve context excerpts for the query."""
        pass

    def export(self) -> dict:
        """Dump the tool's internal state for inspection."""
        pass

    def wipe(self) -> None:
        """Reset to blank state for the next test."""
        pass
```

## Running a benchmark

```bash
# 1. Install harness dependencies
pip install -r harness/requirements.txt

# 2. Configure providers (OpenRouter for main track, Ollama Cloud for open track)
cp harness/.env.example harness/.env
# Edit harness/.env with your keys

# 3. Run LoCoMo s300 for a tool
python -m harness.runner \
  --benchmark locomo \
  --tool basic-memory \
  --sample locomo-s300-seed42 \
  --track open \
  --results-dir harness/results

# 4. Run the stress suite
python -m harness.runner \
  --benchmark stress \
  --tool mem0 \
  --suite contradiction_storm

# 5. Run PlatformOps-Mem
python -m harness.runner \
  --benchmark platformops \
  --tool honcho \
  --scenario infra-continuity
```

## Results format

Every run emits:
- `run.json` — top-level metadata, scores, failure-mode taxonomy
- `per_question.jsonl` — one line per question with excerpts, verbatim answer, grade
- `telemetry.json` — per-call latency, token counts, cost
- `adapter_state.json` — post-run export (if the adapter supports it)

## Methodology freeze

The following were fixed before any tool ran and are SHA-256-stamped in every result:
- Adapter interface (this file)
- Judge model and prompts (`judge.py`)
- Answering model (per track)
- LoCoMo sampling policy (seed 42, stratified 300-question sample)
- Control variables (same tool-internal LLM wherever configurable)
- Failure-mode taxonomy (`judge.py`)
