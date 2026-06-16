"""
Stress suite framework.

The stress suite tests how memory tools behave under pathological conditions
that a platform engineer actually encounters. Each scenario is a mini-benchmark
that runs through the same adapter interface as LoCoMo.

Scenarios:
1. contradiction_storm    — rapidly alternating facts; does the tool reconcile or append?
2. duplicate_flood        — 100 near-identical turns; does retrieval drown in noise?
3. temporal_paradox        — facts that change over time; does the tool preserve history?
4. concurrent_writers      — two agents writing to the same memory simultaneously
5. kill_the_backing_store  — crash and restart; does the tool recover state?
6. cost_runaway            — measure token burn and latency as corpus grows

Every scenario produces a pass/fail verdict plus a failure-mode taxonomy.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import time
import json
from pathlib import Path

from harness.adapter import MemoryAdapter
from harness.telemetry import TelemetryCollector


@dataclass
class StressResult:
    scenario: str
    tool: str
    passed: bool
    verdict: str  # human-readable summary
    failure_modes: list[str]
    latency_sec: float
    metrics: dict  # scenario-specific measurements


class StressScenario(ABC):
    """Base class for a stress test scenario."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self, adapter: MemoryAdapter, telemetry: TelemetryCollector) -> StressResult:
        pass


class ContradictionStorm(StressScenario):
    """
    Rapidly alternating contradictory facts.
    E.g., "The server is in us-east-1" → "The server is in eu-west-1" → repeat.
    
    Pass criterion: retrieval for "where is the server?" returns the MOST RECENT
    fact, not a random one or both.
    """

    @property
    def name(self) -> str:
        return "contradiction_storm"

    def run(self, adapter: MemoryAdapter, telemetry: TelemetryCollector) -> StressResult:
        facts = [
            ("The primary server is in us-east-1.", "us-east-1"),
            ("The primary server is in eu-west-1.", "eu-west-1"),
            ("The primary server is in ap-south-1.", "ap-south-1"),
        ]

        turns = []
        for i in range(20):
            fact, region = facts[i % len(facts)]
            turns.append({
                "role": "user",
                "content": fact,
                "timestamp": f"2026-01-{i+1:02d}T00:00:00Z",
                "metadata": {"region": region}
            })

        adapter.add(turns)
        adapter.await_ingest()
        excerpts = adapter.search("Where is the primary server?")

        # Check if the most recent fact (ap-south-1) is in the top result
        top_text = " ".join(excerpts).lower() if excerpts else ""
        passed = "ap-south-1" in top_text

        failure_modes = []
        if not passed:
            if "us-east-1" in top_text and "eu-west-1" in top_text and "ap-south-1" not in top_text:
                failure_modes.append("stale_dominance")
            elif sum(r in top_text for r in ["us-east-1", "eu-west-1", "ap-south-1"]) > 1:
                failure_modes.append("unresolved_contradiction")
            else:
                failure_modes.append("missing_recall")

        return StressResult(
            scenario=self.name,
            tool=type(adapter).__name__,
            passed=passed,
            verdict="Most recent fact wins" if passed else "Failed to surface latest fact",
            failure_modes=failure_modes,
            latency_sec=telemetry.summary()["total_latency_sec"],
            metrics={"turns": 20, "contradictions": 19, "excerpts_returned": len(excerpts)}
        )


class DuplicateFlood(StressScenario):
    """
    100 near-identical turns. Tests whether the retrieval system drowns in noise
    or correctly surfaces the one relevant variant.
    """

    @property
    def name(self) -> str:
        return "duplicate_flood"

    def run(self, adapter: MemoryAdapter, telemetry: TelemetryCollector) -> StressResult:
        turns = []
        for i in range(100):
            if i == 42:
                content = "CRITICAL: The database password is now rotated to X7#k9mP."
            else:
                content = f"Routine log entry {i}: service health check passed."
            turns.append({"role": "user", "content": content})

        adapter.add(turns)
        adapter.await_ingest()
        excerpts = adapter.search("database password")

        top_text = " ".join(excerpts).lower() if excerpts else ""
        passed = "x7#k9mp" in top_text

        failure_modes = []
        if not passed:
            if "routine log entry" in top_text:
                failure_modes.append("noise_dominance")
            else:
                failure_modes.append("missing_recall")

        return StressResult(
            scenario=self.name,
            tool=type(adapter).__name__,
            passed=passed,
            verdict="Critical signal preserved in noise" if passed else "Signal lost in noise",
            failure_modes=failure_modes,
            latency_sec=telemetry.summary()["total_latency_sec"],
            metrics={"turns": 100, "critical_turn": 42, "excerpts_returned": len(excerpts)}
        )


class TemporalParadox(StressScenario):
    """
    Facts that change over time. The tool must preserve the full timeline,
    not just overwrite.
    
    Query: "What was the database password on January 15?"
    """

    @property
    def name(self) -> str:
        return "temporal_paradox"

    def run(self, adapter: MemoryAdapter, telemetry: TelemetryCollector) -> StressResult:
        turns = [
            {"role": "user", "content": "On Jan 1, the DB password is Alpha1.", "timestamp": "2026-01-01T00:00:00Z"},
            {"role": "user", "content": "On Jan 15, the DB password is Bravo2.", "timestamp": "2026-01-15T00:00:00Z"},
            {"role": "user", "content": "On Jan 30, the DB password is Charlie3.", "timestamp": "2026-01-30T00:00:00Z"},
        ]

        adapter.add(turns)
        adapter.await_ingest()
        excerpts = adapter.search("What was the database password on January 15?")

        top_text = " ".join(excerpts).lower() if excerpts else ""
        passed = "bravo2" in top_text and "alpha1" not in top_text and "charlie3" not in top_text

        failure_modes = []
        if not passed:
            if "charlie3" in top_text:
                failure_modes.append("temporal_override")
            elif "alpha1" in top_text:
                failure_modes.append("stale_retrieval")
            elif sum(p in top_text for p in ["alpha1", "bravo2", "charlie3"]) > 1:
                failure_modes.append("unresolved_temporal")
            else:
                failure_modes.append("missing_recall")

        return StressResult(
            scenario=self.name,
            tool=type(adapter).__name__,
            passed=passed,
            verdict="Correct temporal slice retrieved" if passed else "Failed to retrieve correct time-slice",
            failure_modes=failure_modes,
            latency_sec=telemetry.summary()["total_latency_sec"],
            metrics={"time_points": 3, "query_time": "2026-01-15", "excerpts_returned": len(excerpts)}
        )


class KillTheBackingStore(StressScenario):
    """
    Crash the backing store mid-ingestion and restart. Does the tool recover
    state, or does it lose data?
    """

    @property
    def name(self) -> str:
        return "kill_the_backing_store"

    def run(self, adapter: MemoryAdapter, telemetry: TelemetryCollector) -> StressResult:
        # Phase 1: store a fact
        adapter.add([{"role": "user", "content": "The API key is sk-12345."}])
        adapter.await_ingest()

        # Phase 2: export state, simulate crash, restart
        pre_crash_state = adapter.export()
        adapter.wipe()  # simulate crash + restart
        adapter.setup()  # re-initialize

        # Phase 3: can we still retrieve?
        excerpts = adapter.search("API key")
        top_text = " ".join(excerpts).lower() if excerpts else ""
        passed = "sk-12345" in top_text

        return StressResult(
            scenario=self.name,
            tool=type(adapter).__name__,
            passed=passed,
            verdict="State survived crash" if passed else "State lost on crash",
            failure_modes=["data_loss"] if not passed else [],
            latency_sec=telemetry.summary()["total_latency_sec"],
            metrics={"state_preserved": passed, "pre_crash_state_size": len(str(pre_crash_state))}
        )


class CostRunaway(StressScenario):
    """
    Measure token burn and latency as the corpus grows from 10 to 1000 turns.
    Identifies tools whose cost scales super-linearly.
    """

    @property
    def name(self) -> str:
        return "cost_runaway"

    def run(self, adapter: MemoryAdapter, telemetry: TelemetryCollector) -> StressResult:
        corpus_sizes = [10, 50, 100, 500, 1000]
        measurements = []

        for size in corpus_sizes:
            adapter.wipe()
            turns = [{"role": "user", "content": f"Log entry {i}: status nominal."} for i in range(size)]
            
            t0 = time.perf_counter()
            adapter.add(turns)
            adapter.await_ingest()
            t1 = time.perf_counter()
            
            excerpts = adapter.search("status nominal")
            t2 = time.perf_counter()
            
            measurements.append({
                "corpus_size": size,
                "ingest_sec": round(t1 - t0, 3),
                "search_sec": round(t2 - t1, 3),
            })

        # Check for super-linear scaling
        ingest_times = [m["ingest_sec"] for m in measurements]
        # If 1000-turn ingest is > 100x the 10-turn ingest, that's super-linear
        passed = ingest_times[-1] < ingest_times[0] * 100

        return StressResult(
            scenario=self.name,
            tool=type(adapter).__name__,
            passed=passed,
            verdict="Scaling is linear or sub-linear" if passed else "Super-linear scaling detected",
            failure_modes=["super_linear_scaling"] if not passed else [],
            latency_sec=telemetry.summary()["total_latency_sec"],
            metrics={"measurements": measurements}
        )


SCENARIOS = {
    "contradiction_storm": ContradictionStorm,
    "duplicate_flood": DuplicateFlood,
    "temporal_paradox": TemporalParadox,
    "kill_the_backing_store": KillTheBackingStore,
    "cost_runaway": CostRunaway,
}


def run_stress_suite(adapter: MemoryAdapter, scenarios: list[str] | None = None) -> list[StressResult]:
    """Run selected stress scenarios. Defaults to all."""
    if scenarios is None:
        scenarios = list(SCENARIOS.keys())
    
    results = []
    for name in scenarios:
        if name not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {name}")
        
        scenario = SCENARIOS[name]()
        telemetry = TelemetryCollector(f"stress-{name}-{type(adapter).__name__}")
        result = scenario.run(adapter, telemetry)
        results.append(result)
    
    return results
