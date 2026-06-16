"""
Telemetry: per-call latency, token usage, and cost tracking.

Every adapter call is instrumented automatically. The harness collects:
- latency (wall-clock and CPU time)
- token counts (prompt + completion, where available)
- cost (computed from model pricing tables)

Raw telemetry is published with every run for independent audit.
"""

from dataclasses import dataclass, field
from typing import Optional
import time
import json
from pathlib import Path


@dataclass
class CallTelemetry:
    """Telemetry for a single adapter or model call."""
    call_id: str
    method: str  # "add", "await_ingest", "search", "answer", "judge"
    tool: str | None  # None for model calls
    start_time: float
    end_time: float
    tokens_prompt: int = 0
    tokens_completion: int = 0
    tokens_total: int = 0
    cost_usd: float = 0.0
    model: str | None = None  # for model calls
    status: str = "ok"  # "ok", "error", "timeout"
    error_message: str | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def latency_sec(self) -> float:
        return self.end_time - self.start_time


# Pricing tables (USD per 1M tokens) — frozen at methodology lock date.
# These are the prices used for all cost calculations in the almanac.
PRICING = {
    "anthropic/claude-sonnet-4.6": {"prompt": 3.00, "completion": 15.00},
    "anthropic/claude-opus-4.8": {"prompt": 15.00, "completion": 75.00},
    "deepseek-v4-pro": {"prompt": 0.50, "completion": 2.00},  # via Ollama Cloud
    "qwen3.5:397b": {"prompt": 0.00, "completion": 0.00},  # local / open
}


class TelemetryCollector:
    """Collects and aggregates telemetry across a full benchmark run."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.calls: list[CallTelemetry] = []
        self._call_counter = 0

    def _next_id(self) -> str:
        self._call_counter += 1
        return f"{self.run_id}-{self._call_counter:04d}"

    def record(self, method: str, tool: str | None, start: float, end: float,
               tokens_prompt: int = 0, tokens_completion: int = 0,
               model: str | None = None, status: str = "ok",
               error_message: str | None = None, metadata: dict | None = None) -> CallTelemetry:
        call = CallTelemetry(
            call_id=self._next_id(),
            method=method,
            tool=tool,
            start_time=start,
            end_time=end,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            tokens_total=tokens_prompt + tokens_completion,
            cost_usd=self._compute_cost(model, tokens_prompt, tokens_completion),
            model=model,
            status=status,
            error_message=error_message,
            metadata=metadata or {}
        )
        self.calls.append(call)
        return call

    def _compute_cost(self, model: str | None, prompt_tokens: int, completion_tokens: int) -> float:
        if model is None or model not in PRICING:
            return 0.0
        p = PRICING[model]
        cost = (prompt_tokens * p["prompt"] + completion_tokens * p["completion"]) / 1_000_000
        return round(cost, 6)

    def summary(self) -> dict:
        """Aggregate telemetry into a run-level summary."""
        total_latency = sum(c.latency_sec for c in self.calls)
        total_tokens = sum(c.tokens_total for c in self.calls)
        total_cost = sum(c.cost_usd for c in self.calls)

        by_method = {}
        for c in self.calls:
            by_method.setdefault(c.method, {"calls": 0, "latency_sec": 0.0, "tokens": 0, "cost_usd": 0.0})
            by_method[c.method]["calls"] += 1
            by_method[c.method]["latency_sec"] += c.latency_sec
            by_method[c.method]["tokens"] += c.tokens_total
            by_method[c.method]["cost_usd"] += c.cost_usd

        return {
            "run_id": self.run_id,
            "total_calls": len(self.calls),
            "total_latency_sec": round(total_latency, 3),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "by_method": by_method,
        }

    def save(self, path: Path) -> None:
        """Write raw telemetry to JSON."""
        data = {
            "run_id": self.run_id,
            "calls": [self._call_to_dict(c) for c in self.calls],
            "summary": self.summary()
        }
        path.write_text(json.dumps(data, indent=2))

    def _call_to_dict(self, c: CallTelemetry) -> dict:
        return {
            "call_id": c.call_id,
            "method": c.method,
            "tool": c.tool,
            "latency_sec": round(c.latency_sec, 4),
            "tokens_prompt": c.tokens_prompt,
            "tokens_completion": c.tokens_completion,
            "tokens_total": c.tokens_total,
            "cost_usd": c.cost_usd,
            "model": c.model,
            "status": c.status,
            "error_message": c.error_message,
            "metadata": c.metadata,
        }


class TelemetryContext:
    """Context manager for instrumenting a single call."""
    def __init__(self, collector: TelemetryCollector, method: str, tool: str | None,
                 model: str | None = None):
        self.collector = collector
        self.method = method
        self.tool = tool
        self.model = model
        self.start = 0.0
        self.call = None

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = time.perf_counter()
        status = "error" if exc_type else "ok"
        self.call = self.collector.record(
            method=self.method,
            tool=self.tool,
            start=self.start,
            end=end,
            model=self.model,
            status=status,
            error_message=str(exc_val) if exc_val else None
        )
        return False  # don't suppress exceptions

    def set_tokens(self, prompt: int, completion: int) -> None:
        """Set token counts after the call completes (for model calls)."""
        if self.call:
            self.call.tokens_prompt = prompt
            self.call.tokens_completion = completion
            self.call.tokens_total = prompt + completion
            self.call.cost_usd = self.collector._compute_cost(self.model, prompt, completion)
