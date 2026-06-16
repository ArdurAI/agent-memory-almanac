"""
Frozen MemoryAdapter contract.

This interface is the single point of control between the harness and every
memory tool on the roster. It was frozen before any tool ran.

Every adapter implementation must subclass MemoryAdapter and implement all
abstract methods. The harness enforces the contract via type checking and
runtime assertions.

Version: 2026-06-09
SHA-256: (computed at release)
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field
import time


@dataclass
class AdapterResult:
    """Standardized result from any adapter operation."""
    success: bool
    elapsed_sec: float
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class MemoryAdapter(ABC):
    """
    The frozen contract. Every tool on the roster speaks through this interface.

    Design constraints:
    - No mocks: the adapter must call the real tool, not a stub.
    - No caching across runs: wipe() must return a clean state.
    - Telemetry is automatic: the harness wraps every method with timing.
    """

    @abstractmethod
    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        """
        Store conversation turns through the tool's native write path.

        conversation_turns: list of dicts with keys:
            - role: "user" | "assistant" | "system"
            - content: str
            - timestamp: ISO-8601 string (optional, used for temporal tests)
            - metadata: dict (optional, tool-specific)

        The adapter must feed the turns to the tool exactly as the tool
        expects — no pre-processing that changes the semantic content.
        """
        pass

    @abstractmethod
    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        """
        Block until the tool has finished async ingestion.

        This is where tools with async write paths (Graphiti's graph extraction,
        Cognee's cognify, Honcho's deriver queue, Memobase's flush, Memvid's
        re-encode) get their cost measured instead of hidden.

        Returns the elapsed seconds. If the tool is synchronous, this should
        return immediately with elapsed_sec ≈ 0.

        Raises TimeoutError if ingestion does not complete within timeout_sec.
        """
        pass

    @abstractmethod
    def search(self, query: str, k: int = 5) -> AdapterResult:
        """
        Retrieve context excerpts for the query.

        Returns a list of text excerpts. The harness injects these excerpts
        into the answering model's prompt. The adapter must NOT include the
        answer itself — only the retrieved context.

        The adapter may transform the query (e.g., keyword extraction) but
        must not use the answer or gold label.
        """
        pass

    @abstractmethod
    def export(self) -> AdapterResult:
        """
        Dump the tool's internal state for inspection.

        Returns a dict representing the tool's memory state. This is used for
        debugging and for the stress suite's state-verification checks.
        """
        pass

    @abstractmethod
    def wipe(self) -> AdapterResult:
        """
        Reset the tool to a blank state.

        Must clear all stored data, caches, and in-process state. The harness
        calls this between every test scenario to prevent cross-contamination.
        """
        pass

    def setup(self) -> AdapterResult:
        """
        Optional one-time setup (install dependencies, start services).
        Default is a no-op. Override if the tool needs initialization.
        """
        return AdapterResult(success=True, elapsed_sec=0.0)

    def teardown(self) -> AdapterResult:
        """
        Optional cleanup (stop services, remove temp files).
        Default is a no-op. Override if the tool needs cleanup.
        """
        return AdapterResult(success=True, elapsed_sec=0.0)

    # --- harness-wrapped telemetry ---
    def _timed_call(self, method_name: str, fn, *args, **kwargs) -> tuple[Any, float]:
        t0 = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
            elapsed = time.perf_counter() - t0
            return result, elapsed
        except Exception as e:
            elapsed = time.perf_counter() - t0
            raise AdapterError(method_name, elapsed, str(e)) from e


class AdapterError(Exception):
    """Raised when an adapter operation fails."""
    def __init__(self, method: str, elapsed_sec: float, message: str):
        self.method = method
        self.elapsed_sec = elapsed_sec
        self.message = message
        super().__init__(f"[{method}] failed after {elapsed_sec:.3f}s: {message}")
