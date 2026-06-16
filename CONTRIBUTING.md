# Contributing to the Agent Memory Almanac

Thank you for contributing. The Almanac is a community effort to independently evaluate agent memory tools. Every contribution is audited against the frozen methodology.

## Quick start: run a benchmark

```bash
# 1. Clone and install
git clone https://github.com/ArdurAI/agent-memory-almanac.git
cd agent-memory-almanac
pip install -r harness/requirements.txt

# 2. Configure providers
cp harness/.env.example harness/.env
# Edit harness/.env with your OpenRouter and/or Ollama Cloud keys

# 3. Download LoCoMo data
# Get the dataset from https://github.com/snap-research/locomo
# Place it at data/locomo.json

# 4. Run a baseline
python -m harness.runner \
  --benchmark locomo \
  --tool no-memory \
  --sample locomo-s300-seed42 \
  --track open

# 5. Run a real tool
python -m harness.runner \
  --benchmark locomo \
  --tool basic-memory \
  --sample locomo-s300-seed42 \
  --track open
```

## What you can contribute

### 1. Adapter for a new or missing tool

The most valuable contribution. Every tool on the roster needs an adapter implementing the frozen `MemoryAdapter` contract.

**Steps:**

1. Read `harness/adapter.py` to understand the contract
2. Create `harness/adapters/<tool_name>.py`
3. Implement all abstract methods: `add()`, `await_ingest()`, `search()`, `export()`, `wipe()`
4. Add your adapter to `_load_adapter()` in `harness/runner.py`
5. Test with the no-memory benchmark first to validate the harness, then with your tool
6. Submit a PR with:
   - The adapter code
   - A smoke-test run summary (install time, dependency notes, any bugs found)
   - Updated `tools/<tool_name>.md` with the smoke-gate findings

**Adapter rules:**
- No mocks: call the real tool
- No answer leakage: don't use the gold answer or question category in `search()`
- `wipe()` must return a clean state (no cross-contamination between runs)
- `await_ingest()` must measure real async lag, not return 0 if the tool has async ingestion

### 2. Benchmark run results

If you have API quota and want to run a queued tool:

1. Check the [published-vs-reproduced table](published-vs-reproduced.md) for what's queued
2. Run the benchmark via the harness
3. The harness emits `run.json` + `per_question.jsonl` + `telemetry.json`
4. Submit a PR adding the raw JSON files to `data/benchmarks/` and updating the results page

**Before you run:**
- Verify the methodology is still frozen (check `methodology.md` for the lock date)
- Use the exact sample identifier from the table (e.g., `locomo-s300-seed42`)
- Do not modify the harness code mid-run — report bugs instead

### 3. Bug reports from smoke-gate or benchmark runs

Found a bug in a tool? Document it:

1. Reproduce it with the harness (or with a minimal script if the harness can't reach it)
2. File an issue with:
   - Tool name and version
   - Steps to reproduce
   - Expected vs. actual behavior
   - Severity assessment (High/Medium/Low)
3. We validate it independently and add it to the tool's entry and the bug registry

### 4. New entrants for the roster

Know a tool that should be on the roster?

1. Verify it's open-source and actively maintained (last push < 6 months)
2. File an issue with the repo URL, star count, and why it belongs on the roster
3. The triage criteria:
   - Must be an agent memory tool (not a general RAG framework)
   - Must have a working installation path
   - Must not be a pure wrapper around another roster tool

### 5. Documentation and methodology improvements

- Fix errors in tool entries or editions
- Improve the harness README or methodology docs
- Add diagrams or visualizations

## Code style

- Python: PEP 8, type hints encouraged
- Markdown: 100-character line width, semantic line breaks
- JSON: 2-space indent, no trailing commas
- Commit messages: imperative mood, body explains what and why

## Review process

1. Every PR is reviewed against the frozen methodology
2. Adapter PRs get a smoke-test run by a maintainer before merge
3. Benchmark result PRs are validated for methodology compliance (no harness changes mid-run)
4. Disclosure: if you contribute to a roster tool, declare it in the PR (same as Honcho disclosure)

## License

By contributing, you agree that your contributions are licensed under the same license as the project:
- Code: MIT (or as specified in the file)
- Content: CC BY 4.0

## Questions?

- Read `methodology.md` for the full testing specification
- Read `harness/README.md` for harness architecture
- Open an issue for anything not covered here
