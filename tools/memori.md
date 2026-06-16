# Memori

| | |
|---|---|
| Repo | [MemoriLabs/Memori](https://github.com/MemoriLabs/Memori) |
| Category | Tier A — SQL-native memory |
| Stars | 15,231 |
| License | Apache-2.0 (nonstandard filename) |
| First surveyed | 2026-06 |
| Architecture shape | **Fact extractor** — SQL-native agent memory on SQLite/Postgres/MySQL

## What it is

SQL-native agent memory on SQLite/Postgres/MySQL — the bet is that boring, queryable storage beats exotic stores on ops burden. Every memory is a row in a SQL table. You can query it with SQL, back it up with standard tools, and migrate it with standard procedures.

## Smoke-gate experience

### Install & setup
- **Time to first memory:** ~4 minutes (SQLite is zero-config; Postgres requires setup)
- **Dependencies:** Moderate — SQLAlchemy, database driver
- **Isolation:** Recommended for Postgres mode; SQLite mode is self-contained.

### Smoke-gate findings
- **Write-path latency:** ~1.8s for 3 turns (SQL insert + fact extraction)
- **Async ingestion:** Synchronous — SQL writes are blocking
- **Queryability:** SQL-native means you can query memories with arbitrary SQL. This is a powerful debugging and audit feature.
- **Backup/restore:** Standard database tools work out of the box.

### Bugs & sharp edges found
- **🔴 Cloud tether:** Memori's documented recording API **POSTs to its cloud service** even when configured with a local database. The local path requires an **undocumented internal route**. This means "self-hosted" Memori is leaking data to the cloud by default.
- **License file nonstandard:** GitHub reports `NOASSERTION` because the license file is under a nonstandard filename. The text is Apache-2.0, but automated license detection fails.

## Benchmark status

| Benchmark | Sample | Status | Answerable | Overall |
|-----------|--------|--------|------------|---------|
| LoCoMo s300 | main | queued | — | — |
| LoCoMo s300 | open | queued | — | — |
| Stress suite | — | queued | — | — |
| PlatformOps-Mem | — | queued | — | — |

## Claims under independent test

1. **SQL-native storage beats exotic stores on ops burden.** The ops-burden bet is exactly the Quest's differentiator dimension. Backup, restore, portability, and queryability should be Memori's home turf.
2. **Standard database tooling is enough for agent memory.** If SQLite/Postgres is sufficient, Memori proves that agent memory doesn't need vector stores, graph databases, or specialized backends.
3. **Fact extraction quality is competitive.** The SQL storage is only as good as the facts stored in it. The benchmark will measure whether Memori's extraction matches Mem0's.

## Verdict so far

**The ops-burden champion with a cloud-tether bug.** SQL-native storage is the right ops abstraction — backups, migrations, and queries just work. The cloud-tether bug is serious: a tool marketed as self-hosted shouldn't POST to its cloud service by default. The undocumented local route is a discoverability problem. If the cloud tether is fixed and the fact extraction quality is competitive, Memori could be the most practical Tier A tool for ops-conscious teams.

