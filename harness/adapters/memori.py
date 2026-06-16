"""
Memori adapter for the Quest harness.

Implements the frozen MemoryAdapter contract for Memori.
https://github.com/MemoriLabs/Memori

Memori is SQL-native agent memory on SQLite/Postgres/MySQL. It uses fact
extraction and stores memories as rows in SQL tables.

SETUP REQUIRED:
1. Install Memori: pip install memori
2. Configure the database (SQLite for zero-config, or Postgres/MySQL)

Note: This is a scaffold. The actual Memori API calls need to be filled in.
WARNING: Memori's documented recording API POSTs to its cloud service even
when configured with a local database. The local path requires an undocumented
internal route.
"""

import time
from typing import Optional

from harness.adapter import MemoryAdapter, AdapterResult

# Memori is imported lazily
try:
    import memori
    HAVE_MEMORI = True
except ImportError:
    HAVE_MEMORI = False


class MemoriAdapter(MemoryAdapter):
    """Quest adapter for Memori (SQL-native memory)."""

    def __init__(self, db_url: str = "sqlite:///memori.db"):
        self.db_url = db_url
        self.client = None
        if HAVE_MEMORI:
            # TODO: Initialize Memori client
            # self.client = memori.Client(db_url=db_url)
            pass
        else:
            raise ImportError(
                "memori is not installed. Run: pip install memori\n"
                "WARNING: Check for cloud-tether bug — documented API may POST to cloud."
            )

    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        t0 = time.perf_counter()
        # TODO: Insert turns into SQL database with fact extraction
        # for turn in conversation_turns:
        #     self.client.record(turn)
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"note": "Memori adapter scaffold — implement SQL record"})

    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        # Memori is synchronous (SQL writes are blocking)
        return AdapterResult(success=True, elapsed_sec=0.0)

    def search(self, query: str, k: int = 5) -> AdapterResult:
        t0 = time.perf_counter()
        # TODO: Query SQL database with fact-based search
        # results = self.client.search(query, top_k=k)
        excerpts = []
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"excerpts": excerpts,
                     "note": "Memori adapter scaffold — implement SQL search"})

    def export(self) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={
            "note": "Memori export not yet implemented",
            "db_url": self.db_url,
        })

    def wipe(self) -> AdapterResult:
        # TODO: Clear SQL tables
        return AdapterResult(success=True, elapsed_sec=0.0,
            metadata={"note": "Memori wipe not yet implemented"})
