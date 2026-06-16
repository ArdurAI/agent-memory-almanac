"""
LangMem adapter for the Quest harness.

Implements the frozen MemoryAdapter contract for LangMem.
https://github.com/langchain-ai/langmem

LangMem is LangChain's first-party memory layer. It provides memory primitives
(conversation buffer, vector store memory, entity memory) that integrate with
LangChain's agent and chain abstractions.

SETUP REQUIRED:
1. Install LangMem: pip install langmem
   (If you already have LangChain, the marginal cost is near zero.)

Note: This is a scaffold. The actual LangMem API calls need to be filled in.
"""

import time
from typing import Optional

from harness.adapter import MemoryAdapter, AdapterResult

# LangMem is imported lazily
try:
    import langmem
    HAVE_LANGMEM = True
except ImportError:
    HAVE_LANGMEM = False


class LangmemAdapter(MemoryAdapter):
    """Quest adapter for LangMem (LangChain memory layer)."""

    def __init__(self, memory_type: str = "vector"):
        self.memory_type = memory_type
        self.memory = None
        if HAVE_LANGMEM:
            # TODO: Initialize LangMem with the chosen memory type
            # if memory_type == "vector":
            #     self.memory = langmem.VectorStoreMemory()
            # elif memory_type == "buffer":
            #     self.memory = langmem.ConversationBufferMemory()
            # elif memory_type == "entity":
            #     self.memory = langmem.EntityMemory()
            pass
        else:
            raise ImportError(
                "langmem is not installed. Run: pip install langmem\n"
                "LangMem is most valuable if you already use LangChain."
            )

    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        t0 = time.perf_counter()
        # TODO: Add turns to LangMem memory
        # for turn in conversation_turns:
        #     self.memory.add(turn)
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"note": "LangMem adapter scaffold — implement add"})

    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        # LangMem is synchronous
        return AdapterResult(success=True, elapsed_sec=0.0)

    def search(self, query: str, k: int = 5) -> AdapterResult:
        t0 = time.perf_counter()
        # TODO: Query LangMem memory
        # results = self.memory.search(query, top_k=k)
        excerpts = []
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"excerpts": excerpts,
                     "note": "LangMem adapter scaffold — implement search"})

    def export(self) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={
            "note": "LangMem export not yet implemented",
            "memory_type": self.memory_type,
        })

    def wipe(self) -> AdapterResult:
        # TODO: Clear memory state
        return AdapterResult(success=True, elapsed_sec=0.0,
            metadata={"note": "LangMem wipe not yet implemented"})
