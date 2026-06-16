"""
No-memory baseline.

The simplest possible control: every search returns an empty list.
This establishes the "blank-abstainer" reference line.

Expected behavior on LoCoMo: 0.000 answerable, 1.000 abstention, 0.223 overall.
Any tool scoring near this is doing nothing useful.
"""

from harness.adapter import MemoryAdapter, AdapterResult


class NoMemoryAdapter(MemoryAdapter):
    """Baseline that remembers nothing."""

    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0)

    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0)

    def search(self, query: str, k: int = 5) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={"excerpts": []})

    def export(self) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={"state": None})

    def wipe(self) -> AdapterResult:
        return AdapterResult(success=True, elapsed_sec=0.0)
