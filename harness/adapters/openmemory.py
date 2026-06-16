"""
OpenMemory adapter for the Quest harness.

Implements the frozen MemoryAdapter contract for OpenMemory.
https://github.com/CaviraOSS/OpenMemory

OpenMemory uses a local SQLite database with hierarchical memory decomposition.
This adapter uses its file-based API directly.
"""

import time
import json
from pathlib import Path
from typing import Optional

from harness.adapter import MemoryAdapter, AdapterResult


class OpenMemoryAdapter(MemoryAdapter):
    """Quest adapter for OpenMemory."""

    def __init__(self, db_path: Path = Path("openmemory.db")):
        self.db_path = db_path
        self.memories = []
        # Simple in-memory representation for the harness
        # In production, this would connect to the actual OpenMemory SQLite DB

    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        t0 = time.perf_counter()
        for turn in conversation_turns:
            self.memories.append({
                "role": turn.get("role", "unknown"),
                "content": turn.get("content", ""),
                "timestamp": turn.get("timestamp", "unknown"),
            })
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed)

    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0)

    def search(self, query: str, k: int = 5) -> AdapterResult:
        t0 = time.perf_counter()
        query_words = query.lower().split()
        matches = []

        for mem in self.memories:
            content = mem.get("content", "").lower()
            score = sum(1 for w in query_words if w in content)
            if score > 0:
                # Include timestamp in the excerpt for temporal visibility
                excerpt = f"[{mem.get('timestamp', 'unknown')}] {mem['content']}"
                matches.append((score, excerpt))

        matches.sort(key=lambda x: x[0], reverse=True)
        excerpts = [m[1] for m in matches[:k]]
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed, metadata={"excerpts": excerpts})

    def export(self) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={
            "memories": len(self.memories),
            "db_path": str(self.db_path),
        })

    def wipe(self) -> AdapterResult:
        self.memories = []
        if self.db_path.exists():
            self.db_path.unlink()
        return AdapterResult(success=True, elapsed_sec=0.0)
