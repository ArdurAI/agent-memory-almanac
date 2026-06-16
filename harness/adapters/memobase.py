"""
Memobase adapter for the Quest harness.

Implements the frozen MemoryAdapter contract for Memobase.
https://github.com/memodb-io/memobase

Memobase maintains a structured, evolving user profile with a hard cap of
exactly 3 LLM calls per run (extraction, update, retrieval).

SETUP REQUIRED:
1. Install Memobase server: see https://github.com/memodb-io/memobase
2. Start the server
3. Configure the API endpoint

Note: This is a scaffold. The actual Memobase API calls need to be filled in.
Freshness watch: last push 2026-01-11 (~5 months ago as of June 2026).
"""

import time
from typing import Optional

from harness.adapter import MemoryAdapter, AdapterResult

# Memobase is imported lazily
try:
    import memobase
    HAVE_MEMOBASE = True
except ImportError:
    HAVE_MEMOBASE = False


class MemobaseAdapter(MemoryAdapter):
    """Quest adapter for Memobase (evolving user profile)."""

    def __init__(self, api_url: str = "http://localhost:8000",
                 user_id: str = "quest-user"):
        self.api_url = api_url
        self.user_id = user_id
        self.client = None
        if HAVE_MEMOBASE:
            # TODO: Initialize Memobase client
            # self.client = memobase.Client(base_url=api_url)
            pass
        else:
            raise ImportError(
                "memobase is not installed. See https://github.com/memodb-io/memobase\n"
                "Freshness watch: last push 2026-01-11."
            )

    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        t0 = time.perf_counter()
        # TODO: Send turns to Memobase (counts as 1 LLM call: extraction)
        # for turn in conversation_turns:
        #     self.client.add_message(user_id=self.user_id, message=turn)
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"note": "Memobase adapter scaffold — implement add_message"})

    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        # Memobase has a flush-based async pipeline
        t0 = time.perf_counter()
        # TODO: Wait for the profile update flush to complete
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"note": "Memobase flush — measure async lag"})

    def search(self, query: str, k: int = 5) -> AdapterResult:
        t0 = time.perf_counter()
        # TODO: Query the evolving user profile (counts as 1 LLM call: retrieval)
        # results = self.client.query(user_id=self.user_id, query=query, top_k=k)
        excerpts = []
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"excerpts": excerpts,
                     "note": "Memobase adapter scaffold — implement profile query"})

    def export(self) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={
            "note": "Memobase export not yet implemented",
            "user_id": self.user_id,
        })

    def wipe(self) -> AdapterResult:
        # TODO: Clear user profile
        return AdapterResult(success=True, elapsed_sec=0.0,
            metadata={"note": "Memobase wipe not yet implemented"})
