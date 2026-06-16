# Troubleshooting & Debugging

How to understand the Agent Memory Almanac codebase, debug issues, and resolve common problems.

## Table of Contents

1. [Understanding the Codebase](#understanding-the-codebase)
2. [Common Issues](#common-issues)
3. [Debugging the Data Pipeline](#debugging-the-data-pipeline)
4. [Debugging Benchmark Runs](#debugging-benchmark-runs)
5. [FAQ](#faq)
6. [Getting Help](#getting-help)

---

## Understanding the Codebase

### High-level flow

```
Research Agents → Research Output (Markdown) →
  Python Script → roster.json (Structured Data) →
    Manual Review → Edition Markdown →
      Git Commit → GitHub Publication
```

Benchmark results flow separately:
```
Harness Runner → Raw JSON (per question) →
  Analysis Script → Summary Tables →
    Per-tool Pages → Edition Update
```

### Key files and their roles

| File | Role | When to read it |
|------|------|-----------------|
| `README.md` | Project overview, quick reference | First thing you read |
| `INTENT.md` | Philosophy, why we do things this way | When you disagree with a decision |
| `IMPLEMENTATION.md` | How things are built, how to add tools | When you want to contribute |
| `TESTING.md` | Benchmark methodology summary | When you want to reproduce or challenge a result |
| `TROUBLESHOOTING.md` | This file | When something is broken |
| `methodology.md` | Complete frozen methodology spec | When you want the exact details |
| `architecture.md` | Stack architecture + latency charts | When you want to understand the big picture |
| `published-vs-reproduced.md` | Vendor claims vs. our results | When you want to verify a vendor claim |
| `editions/YYYY-MM.md` | Monthly snapshot of the landscape | When you want historical data |
| `data/roster.json` | Machine-readable catalog | When you want to query or analyze the data |
| `harness/adapter.py` | MemoryAdapter contract | When you want to build an adapter |
| `harness/runner.py` | Benchmark runner | When you want to run benchmarks |
| `harness/judge.py` | Grading pipeline | When you want to understand scoring |

### The data model

The almanac is fundamentally a **directed graph** of data:

```
Research findings → Tool metadata → Roster JSON → Edition Markdown → README
                                      ↓
                               Benchmark results → Per-tool pages
```

- **Research findings** are the raw output of the research swarm. They're saved in `research/` (not in the public repo).
- **Tool metadata** is extracted from research and stored in `data/roster.json`.
- **Roster JSON** is the single source of truth. Everything else derives from it.
- **Edition markdown** is human-written based on the roster and research.
- **README** is auto-generated from the roster and the latest edition.

### Understanding `data/roster.json`

This is the most important file in the repo. It is the single source of truth.

**Structure**:
```json
{
  "meta": { ... },
  "tools": [
    { "name": "...", "type": "...", "license": "...", "tier": "A|B|C", "notes": "..." }
  ]
}
```

**How to query it**:
```bash
# Find all Tier A tools
jq '.tools[] | select(.tier == "A") | .name' data/roster.json

# Count tools by type
jq '.tools | group_by(.type) | map({type: .[0].type, count: length})' data/roster.json

# Find all MIT-licensed tools
jq '.tools[] | select(.license == "MIT") | .name' data/roster.json
```

### The benchmark harness

The actual benchmark code lives in `harness/`. This is published alongside the almanac data.

**Key components**:
- `harness/adapter.py` — The `MemoryAdapter` abstract base class
- `harness/adapters/` — One adapter per tool
- `harness/runner.py` — The benchmark runner
- `harness/judge.py` — The grading pipeline (deterministic + LLM judge)
- `harness/requirements.txt` — Python dependencies

## Common Issues

### Issue: `roster.json` is invalid JSON

**Symptoms**:
- `jq` fails to parse it
- GitHub Actions fails on JSON validation
- Python `json.load()` raises `JSONDecodeError`

**Diagnosis**:
```bash
python3 -c "import json; json.load(open('data/roster.json'))"
```

**Resolution**:
1. Find the line with the error: `python3 -m json.tool data/roster.json`
2. Common causes: trailing commas, unescaped quotes, incorrect nesting
3. Fix the JSON and re-validate

### Issue: Edition markdown has broken links

**Symptoms**:
- Links to tools return 404
- Links to benchmarks don't exist yet
- Relative links work locally but break on GitHub

**Diagnosis**:
```bash
find . -name "*.md" -exec grep -oP '\[.*?\]\(.*?\)' {} + | grep -v "http" | grep -v "mailto"
```

**Resolution**:
1. For internal links, use relative paths: `../data/roster.json`
2. For external links, verify the URL is correct
3. For tools without a per-tool page yet, link to their homepage or GitHub repo

### Issue: The adapter fails

**Symptoms**:
- `harness.runner` crashes with an adapter error
- `add()` or `search()` raises an exception
- `await_ingest()` times out

**Diagnosis**:
1. Run the adapter in isolation: `python -c "from harness.adapters.my_tool import MyToolAdapter; a = MyToolAdapter(); a.add([...]); print(a.search('test'))"`
2. Check the tool's documentation for setup requirements
3. Check if environment variables are set (API keys, etc.)
4. Check if the tool version matches what the adapter expects

**Common fixes**:
- Missing API key → Set the environment variable in `harness/.env`
- Wrong tool version → Update the adapter or pin the version
- Dependency conflict → Use a virtual environment
- Async ingestion timeout → Increase `timeout_sec` in `await_ingest()` or fix the tool

### Issue: The canary fails

**Symptoms**:
- The no-memory baseline scores above zero on answerable categories
- The adversarial score is not 1.000

**Diagnosis**:
1. Check if the benchmark workload has leaked answers
2. Check if the grading pipeline has a bug
3. Check if the random seed was set correctly

**Resolution**:
1. If the workload leaked answers, redesign the workload
2. If the grader has a bug, fix the grader and rerun all tests
3. This is a critical failure — the entire batch is invalid

### Issue: Benchmark results are inconsistent

**Symptoms**:
- Same tool, same test, different results across runs
- Scores vary by more than the confidence interval

**Diagnosis**:
1. Check if the tool has non-deterministic behavior (temperature > 0, async timing)
2. Check if the hardware was different between runs
3. Check if the tool version changed between runs
4. Check if the answering model or judge model changed

**Resolution**:
1. Set temperature to 0 for all LLM calls in the adapter (if configurable)
2. Record hardware specs in the results metadata
3. Pin tool versions and record them
4. Use the exact same track (main or open) for comparison

### Issue: The harness runner fails to start

**Symptoms**:
- `python -m harness.runner` raises `ModuleNotFoundError`
- `ImportError` for `harness` module
- `.env` file not found

**Diagnosis**:
```bash
python -c "import harness.runner"
cat harness/.env
```

**Resolution**:
1. Install dependencies: `pip install -r harness/requirements.txt`
2. Ensure you're running from the repo root (not inside `harness/`)
3. Copy `harness/.env.example` to `harness/.env` and configure API keys
4. Ensure `data/locomo.json` exists (download from https://github.com/snap-research/locomo)

### Issue: GitHub push fails

**Symptoms**:
- `git push` returns 403 or 401
- The remote is not configured
- The branch is behind origin

**Diagnosis**:
```bash
git remote -v
git status
git log --oneline -5
```

**Resolution**:
1. Verify the remote URL is correct
2. Verify GitHub CLI auth: `gh auth status`
3. If behind origin, pull first: `git pull origin main`
4. If there are conflicts, resolve them manually

## Debugging the Data Pipeline

### Research output → roster.json

**Problem**: Research agents produce markdown, but the roster JSON is incomplete or wrong.

**Debug steps**:
1. Read the research output files in `research/` (local workspace, not in the repo)
2. Check if the Python extraction script correctly parsed the tool tables
3. Check if tools were dropped during triage (check the triage log)
4. Verify the JSON schema is correct

**Common bugs**:
- Tool names with special characters break JSON parsing → Escape them properly
- Tools with no tier get dropped → Default to Tier C if unsure
- Tools with no notes get empty strings → Add a minimal note

### roster.json → edition markdown

**Problem**: The edition doesn't reflect the roster.

**Debug steps**:
1. Compare the tool counts in the roster vs. the edition
2. Check if the edition was written before the roster was updated
3. Check if tools were manually edited in the edition but not in the roster

**Resolution**:
1. The edition should be derived from the roster, not the other way around
2. If the edition has manual additions, ensure they are also in the roster
3. The edition is a human-readable summary; the roster is the source of truth

## Debugging Benchmark Runs

### The adapter fails on a specific tool

**Debug steps**:
1. Run the adapter in isolation (without the harness runner)
2. Check the tool's logs for errors
3. Check if the tool's services are running (Docker containers, databases, etc.)
4. Check if the tool's API version matches the adapter's expectations

**Common fixes**:
- Missing Docker daemon → Start Docker
- Missing database → Initialize the database
- Missing API key → Set the environment variable
- Wrong tool version → Update the adapter or pin the version
- Dependency conflict → Use a virtual environment or container

### Results are inconsistent across runs

**Debug steps**:
1. Check if the tool has non-deterministic behavior (e.g., LLM-based extraction with temperature > 0)
2. Check if the answering model is consistent (same model, same temperature)
3. Check if the corpus is the same (same LoCoMo sample, same seed)
4. Check if hardware/resources are the same (same machine, same GPU)

**Resolution**:
1. Pin all random seeds
2. Set temperature to 0 for all LLM calls
3. Use the exact same sample identifier (e.g., `locomo-s300-seed42`)
4. Record hardware specs in the results metadata

### The judge pipeline disagrees with deterministic grader

**Symptoms**:
- The LLM judge says "correct" but the deterministic grader says "incorrect"
- The two passes disagree (confidence < 0.7)

**Diagnosis**:
1. Read the per-question record to see the exact question, answer, and judge reasoning
2. Check if the answer is ambiguous (partially correct, borderline)
3. Check if the judge prompt is being followed correctly

**Resolution**:
1. If the deterministic grader is correct, the judge may be wrong — document it
2. If the answer is ambiguous, the conservative fallback is "incorrect" — this is by design
3. If the judge consistently makes a class of errors, file an issue to update the judge prompt for the next methodology lock

## FAQ

### Q: Why is tool X not in the roster?

A: Either it doesn't meet triage criteria, it hasn't been discovered yet, or it was removed for inactivity. File an issue with evidence and we'll triage it. The tool must be an **agent memory tool** — not a general RAG framework or vector database.

### Q: Why did tool X's score change?

A: Either the tool was updated, the methodology was refined, or we found a bug in our previous test. All three are valid reasons. Check the edition notes for the rationale.

### Q: Can I run the benchmarks myself?

A: Yes. Clone the repo, install dependencies, configure API keys, download LoCoMo data, and run the harness. See `CONTRIBUTING.md` for detailed instructions.

### Q: How do I challenge a ranking?

A: File an issue with specific evidence. Check the raw results JSON, the adapter code, and the judge prompts. If you find a real problem, we'll re-run or update the methodology.

### Q: Can I add a tool to the roster?

A: Yes. See `CONTRIBUTING.md` for instructions. The tool must meet triage criteria and pass the smoke gate. It must be an agent memory tool.

### Q: How often are benchmarks re-run?

A: Standard: every quarter for each tool. Stress: annually. If a tool releases a major version, we may re-run early.

### Q: What's the difference between Tier A, B, and C?

A: Tier A = market leader or strongest technical merit. Tier B = solid option, specific use cases. Tier C = niche, early-stage, or specialized. Baselines are always Tier C.

### Q: Can vendors sponsor the almanac?

A: No. The almanac is independently funded. Sponsorship would compromise the core mission. Vendors can improve their scores by actually improving their tools.

### Q: What's the difference between main track and open track?

A: Main track uses commercial models via OpenRouter. Open track uses open-weight models via Ollama Cloud. They are **never compared head-to-head** because the answerers differ.

### Q: Why is the canary important?

A: The canary verifies that the benchmark doesn't leak answers. If the no-memory baseline scored above zero, the benchmark would be invalid. The canary must score exactly 0.000 on answerable categories.

### Q: What if a tool fails the smoke gate?

A: The tool is documented as having smoke-gate failures and is assigned to Tier C with a note about the blocker. If the vendor fixes the issues, the tool can be re-tested.

## Getting Help

### File an issue

GitHub issues are the primary support channel. Use the appropriate template:

- **Tool request**: "Add [Tool Name] to roster"
- **Data correction**: "[Tool Name] metadata is wrong: [what's wrong]"
- **Benchmark challenge**: "Challenge [Tool Name] ranking: [evidence]"
- **Bug report**: "[Bug description] in [file/process]"
- **Feature request**: "[Feature description] for [use case]"

### Discussion

GitHub Discussions are for:
- General questions about the almanac
- Sharing experiences with tools on the roster
- Proposing methodology changes
- Community announcements

### Email

For private or sensitive inquiries: Use the contact info in the ArdurAI org profile.

## License

Content: CC BY 4.0
