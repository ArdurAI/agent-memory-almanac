"""
Obsidian-as-memory baseline.

Stores conversation turns as Markdown notes in an Obsidian-style vault.
Each turn becomes a note with frontmatter (timestamp, tags).
Search is naive keyword matching, but timestamps are INLINED into the note text
so the answering model can see them.

Key finding from smoke-gate: the only difference from plainfile is timestamp
inlining, yet Obsidian scores 0.375 on temporal vs. plainfile's 0.000.
This is the "timestamp visibility" finding.
"""

from pathlib import Path
import time
import json
from harness.adapter import MemoryAdapter, AdapterResult


class ObsidianAdapter(MemoryAdapter):
    """Baseline: Obsidian vault with timestamp-inlined notes."""

    def __init__(self, vault_path: Path = Path("vault")):
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
            "notes": len(list(self.vault_path.glob("*.md")))
        })

    def wipe(self) -> AdapterResult:
        self.turns = []
        for f in self.vault_path.glob("*.md"):
            f.unlink()
        return AdapterResult(success=True, elapsed_sec=0.0)
