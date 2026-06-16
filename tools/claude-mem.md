# claude-mem

| | |
|---|---|
| Repo | [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) |
| Category | Tier B — session capture & reinjection |
| Stars | 81,466 |
| License | Apache-2.0 |
| First surveyed | 2026-06 |
| Architecture shape | **MCP server** — captures Claude Code sessions, AI-compresses, context-reinjects

## What it is

The adoption story of the year: 81k stars for a session-capture → AI-compression → context-reinjection layer for coding agents (Claude Code, Codex, Copilot, and others). It hooks into the agent's lifecycle and compresses conversation history into memory snippets that get reinjected on subsequent sessions.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~3 minutes via `npm install` and Claude Code hooks
- **Dependencies:** Node.js ecosystem; no Python dependency conflicts

### Smoke-gate findings
- **Deferred from standard adapter testing:** claude-mem is a Claude Code lifecycle-hook system with no queryable API. It cannot be evaluated through the standard `MemoryAdapter` contract (no `search()` endpoint — it reinjects context into the agent's prompt directly).
- **Evaluation plan:** It will be evaluated in its native environment (Claude Code sessions) rather than through the adapter harness. This means its results will be reported as a special case, not directly comparable head-to-head with standard adapter tools.
- **Latency:** Not measurable via the harness; the compression happens asynchronously between sessions

### Bugs & sharp edges found
- None in the smoke gate, but the evaluation model is fundamentally different from other tools. The lack of a queryable API means it cannot be tested for retrieval accuracy in the standard way.

## Benchmark status

| Benchmark | Sample | Status | Notes |
|-----------|--------|--------|-------|
| LoCoMo s300 | main | **deferred** | No queryable API; native-session evaluation planned |
| LoCoMo s300 | open | **deferred** | No queryable API |
| Stress suite | — | **deferred** | Cannot test through adapter contract |
| PlatformOps-Mem | — | **deferred** | Native-session evaluation planned |

## Claims under independent test

1. **Session compression preserves critical context.** Does the AI-compression step retain the facts that matter, or does it lose nuance? Native-session evaluation will test this.
2. **Coding-agent continuity beats general memory.** Specialized for coding workflows — does this specialization win against general-purpose memory tools on coding tasks?
3. **Hook-based integration is frictionless.** The install experience for Claude Code users is reportedly excellent; PlatformOps will test whether this holds for production infrastructure work.

## Verdict so far

**The adoption king with an evaluation gap.** 81k stars make it impossible to ignore, but the lack of a queryable API means standard benchmark comparability is limited. The Quest will evaluate it in its native habitat and report findings separately. Whether the hype translates to measurable retrieval quality is the open question.

