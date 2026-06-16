"""
Plain-file baseline.

Appends every conversation turn to a single text file.
Search does naive keyword matching (case-insensitive substring).

Key finding from smoke-gate: timestamps are kept in metadata but NOT inlined
into the retrieved text, so temporal questions score 0.000. This is the
"timestamp visibility" control case.
"""

from pathlib import Path
import time
from harness.adapter import MemoryAdapter, AdapterResult


class PlainFileAdapter(MemoryAdapter):
    """Baseline: append to a single file, keyword search."""

    def __init__(self, file_path: Path = Path("memory.txt")):
        self.file_path = file_path
        self.turns = []

    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        t0 = time.perf_counter()
        self.turns.extend(conversation_turns)
        text = "\n".join(
            f"[{t.get('timestamp', 'unknown')}] {t['role']}: {t['content']}"
            for t in conversation_turns
        )
        with self.file_path.open("a") as f:
            f.write(text + "\n")
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed)

    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0)

    def search(self, query: str, k: int = 5) -> AdapterResult:
        t0 = time.perf_counter()
        query_words = query.lower().split()
        matches = []
        for turn in self.turns:
            content = turn.get("content", "").lower()
            score = sum(1 for w in query_words if w in content)
            if score > 0:
                matches.append((score, turn))

        matches.sort(key=lambda x: x[0], reverse=True)
        excerpts = [m[1]["content"] for m in matches[:k]]
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed, metadata={"excerpts": excerpts})

    def export(self) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={
            "turns": len(self.turns),
            "file": str(self.file_path)
        })

    def wipe(self) -> AdapterResult:
        self.turns = []
        if self.file_path.exists():
            self.file_path.unlink()
        return AdapterResult(success=True, elapsed_sec=0.0)
