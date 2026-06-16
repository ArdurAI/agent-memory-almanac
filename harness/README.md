# Quest Benchmark Harness

The frozen harness behind the *Agent Memory Almanac*.

## Quick start

```bash
pip install -r harness/requirements.txt
cp harness/.env.example harness/.env
# Edit harness/.env with your API keys

# Run the no-memory canary (no API calls needed)
python -m harness.runner \
  --benchmark locomo \
  --tool no-memory \
  --sample locomo-s300-seed42 \
  --track open
```

## Architecture

```
harness/
  adapter.py           # Frozen MemoryAdapter contract
  telemetry.py         # Per-call latency, token usage, cost tracking
  judge.py             # Deterministic grader + frozen LLM judge pipeline
  runner.py            # Orchestrator: setup → run → grade → emit results
  transport.py         # OpenRouter + Ollama Cloud API clients
  answer.py            # Answering model integration
  data_loader.py       # LoCoMo dataset loader
  bench_locomo.py      # LoCoMo benchmark implementation
  stress_suite.py      # Stress test framework
  bench_platformops.py # PlatformOps-Mem benchmark
  adapters/            # Per-tool adapter implementations
    __init__.py
    no_memory.py       # Baseline: remembers nothing
    plainfile.py       # Baseline: single text file
    obsidian.py        # Baseline: markdown vault with timestamps
    naive_rag.py       # Baseline: chunk + embed + cosine
    basic_memory.py    # Basic Memory adapter
    openmemory.py      # OpenMemory adapter
    mem0.py            # Mem0 adapter
  tests.py             # Integration tests
```

## The frozen contract

Every adapter implements:

```python
class MemoryAdapter(ABC):
    def add(self, conversation_turns: list[dict]) -> AdapterResult
    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult
    def search(self, query: str, k: int = 5) -> AdapterResult
    def export(self) -> AdapterResult
    def wipe(self) -> AdapterResult
```

## Running a benchmark

```bash
# LoCoMo s300 — open track (cheaper, faster)
python -m harness.runner \
  --benchmark locomo \
  --tool basic-memory \
  --sample locomo-s300-seed42 \
  --track open \
  --data-path data/locomo.json

# LoCoMo s300 — main track (Claude models, higher cost)
python -m harness.runner \
  --benchmark locomo \
  --tool mem0 \
  --sample locomo-s300-seed42 \
  --track main \
  --data-path data/locomo.json

# Full LoCoMo dataset (1,986 questions)
python -m harness.runner \
  --benchmark locomo \
  --tool naive-rag \
  --sample locomo-full \
  --track open
```

## Results format

Every run produces a timestamped directory under `harness/results/`:

- `run.json` — metadata, scores, failure-mode taxonomy
- `per_question.jsonl` — one line per question with excerpts, verbatim answer, grade
- `telemetry.json` — raw per-call telemetry with latency, tokens, cost
- `adapter_state.json` — post-run memory dump

## Writing a new adapter

1. Create `harness/adapters/<tool_name>.py`
2. Subclass `MemoryAdapter` from `harness.adapter`
3. Implement all abstract methods
4. Register in `harness/runner.py:_load_adapter()`
5. Test with `python -m harness.runner --tool <tool_name> --benchmark locomo --track open`

See existing adapters for examples. The contract is frozen — no changes without a methodology revision.

## Testing the harness

```bash
cd agent-memory-almanac
python -m pytest harness/tests.py -v
```

## Methodology

Full specification in [`methodology.md`](../methodology.md). Key principles:

- Frozen before any tool runs
- Raw results JSON published with every ranking
- Identical harness for every tool
- Seven scored dimensions (accuracy, latency, token economics, scale, ops burden, DX, data sovereignty)
