"""
Memvid adapter for the Quest harness.

Implements the frozen MemoryAdapter contract for Memvid.
https://github.com/memvid/memvid

Memvid encodes memory using video-codec compression. It has NO incremental
writes — the entire corpus must be re-encoded on every update. This is an
archive format, not a real-time memory system.

SETUP REQUIRED:
1. Install Memvid: pip install memvid
   Note: Memvid has a stale numpy<2 pin. You may need to use an older Python
   version or patch the dependency.

Note: This is a scaffold. The actual Memvid API calls need to be filled in.
"""

import time
from typing import Optional

from harness.adapter import MemoryAdapter, AdapterResult

# Memvid is imported lazily
try:
    import memvid
    HAVE_MEMVID = True
except ImportError:
    HAVE_MEMVID = False


class MemvidAdapter(MemoryAdapter):
    """Quest adapter for Memvid (codec-compressed memory)."""

    def __init__(self, output_path: str = "memvid.archive"):
        self.output_path = output_path
        self.turns = []
        if not HAVE_MEMVID:
            raise ImportError(
                "memvid is not installed. Run: pip install memvid\n"
                "WARNING: memvid has a stale numpy<2 pin that may break on Python 3.12+."
            )

    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        t0 = time.perf_counter()
        # Collect turns for the next full re-encode
        self.turns.extend(conversation_turns)
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"note": "Memvid collects turns; full re-encode happens on search"})

    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        # Memvid is synchronous — no async lag
        return AdapterResult(success=True, elapsed_sec=0.0)

    def search(self, query: str, k: int = 5) -> AdapterResult:
        t0 = time.perf_counter()
        # TODO: Full re-encode the corpus, then search the encoded archive
        # archive = memvid.encode(self.turns)
        # results = archive.search(query, top_k=k)
        excerpts = []
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"excerpts": excerpts,
                     "note": "Memvid adapter scaffold — full re-encode + search"})

    def export(self) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={
            "note": "Memvid export not yet implemented",
            "turns": len(self.turns),
        })

    def wipe(self) -> AdapterResult:
        self.turns = []
        return AdapterResult(success=True, elapsed_sec=0.0)
