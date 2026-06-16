"""
Mem0 adapter for the Quest harness.

Implements the frozen MemoryAdapter contract for the Mem0 memory library.
https://github.com/mem0ai/mem0
"""

import time
from pathlib import Path
from typing import Optional

from harness.adapter import MemoryAdapter, AdapterResult

# Mem0 is imported lazily to avoid hard dependency
try:
    from mem0 import MemoryClient
    HAVE_MEM0 = True
except ImportError:
    HAVE_MEM0 = False


class Mem0Adapter(MemoryAdapter):
    """Quest adapter for Mem0."""

    def __init__(self, api_key: Optional[str] = None, user_id: str = "quest-user"):
        self.user_id = user_id
        self.client = None
        if HAVE_MEM0:
            self.client = MemoryClient(api_key=api_key)
        else:
            raise ImportError(
                "mem0 is not installed. Run: pip install mem0ai"
            )

    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        t0 = time.perf_counter()
        messages = [
            {"role": t["role"], "content": t["content"]}
            for t in conversation_turns
        ]
        self.client.add(messages, user_id=self.user_id)
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed)

    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        # Mem0 ingestion is synchronous; no async lag to measure
        return AdapterResult(success=True, elapsed_sec=0.0)

    def search(self, query: str, k: int = 5) -> AdapterResult:
        t0 = time.perf_counter()
        results = self.client.search(query, user_id=self.user_id, limit=k)
        excerpts = [r.get("memory", "") for r in results]
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed, metadata={"excerpts": excerpts})

    def export(self) -> AdapterResult:
        # Mem0 does not have a direct export API; return memory count
        all_memories = self.client.get_all(user_id=self.user_id)
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={
            "memory_count": len(all_memories),
            "user_id": self.user_id,
        })

    def wipe(self) -> AdapterResult:
        # Mem0 does not have a direct wipe API; delete all memories for user
        all_memories = self.client.get_all(user_id=self.user_id)
        for mem in all_memories:
            mem_id = mem.get("id")
            if mem_id:
                self.client.delete(memory_id=mem_id, user_id=self.user_id)
        return AdapterResult(success=True, elapsed_sec=0.0)
