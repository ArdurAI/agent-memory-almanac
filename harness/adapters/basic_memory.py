"""
Basic Memory adapter for the Quest harness.

Implements the frozen MemoryAdapter contract for the Basic Memory MCP server.
https://github.com/basicmachines-co/basic-memory

Basic Memory stores everything as markdown on disk. We interact with it via
its file system interface.
"""

import time
from pathlib import Path
from typing import Optional

from harness.adapter import MemoryAdapter, AdapterResult


class BasicMemoryAdapter(MemoryAdapter):
    """Quest adapter for Basic Memory."""

    def __init__(self, vault_path: Path = Path("basic-memory-vault")):
        self.vault_path = vault_path
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.turns = []

    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        t0 = time.perf_counter()
        for turn in conversation_turns:
            self.turns.append(turn)
            timestamp = turn.get("timestamp", "unknown")
            content = turn.get("content", "")
            note = f"""---
timestamp: {timestamp}
role: {turn.get("role", "unknown")}
---

**{timestamp}** — {content}
"""
            note_path = self.vault_path / f"turn-{len(self.turns):04d}.md"
            note_path.write_text(note)
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed)

    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0)

    def search(self, query: str, k: int = 5) -> AdapterResult:
        t0 = time.perf_counter()
        query_words = query.lower().split()
        matches = []

        for note_path in sorted(self.vault_path.glob("*.md")):
            text = note_path.read_text().lower()
            score = sum(1 for w in query_words if w in text)
            if score > 0:
                matches.append((score, note_path.read_text()))

        matches.sort(key=lambda x: x[0], reverse=True)
        excerpts = [m[1] for m in matches[:k]]
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed, metadata={"excerpts": excerpts})

    def export(self) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={
            "turns": len(self.turns),
            "vault": str(self.vault_path),
            "notes": len(list(self.vault_path.glob("*.md"))),
        })

    def wipe(self) -> AdapterResult:
        self.turns = []
        for f in self.vault_path.glob("*.md"):
            f.unlink()
        return AdapterResult(success=True, elapsed_sec=0.0)
