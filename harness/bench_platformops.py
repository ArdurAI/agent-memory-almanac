"""
PlatformOps-Mem benchmark.

The differentiator of the Quest series. While LoCoMo tests general long-horizon
memory, PlatformOps-Mem tests memory on the actual work of a platform engineer:

1. infra-continuity     — troubleshooting a problem across multiple sessions
2. state-mutation       — remembering that infrastructure state has changed
3. runbook-recall       — retrieving the correct runbook for a given alert
4. cross-project-isolation — ensuring memories from project A don't leak into project B
5. incident-reconstruction — reconstructing the timeline of a past incident

Each scenario is a realistic multi-turn conversation with an embedded question
that tests whether the memory tool preserves operational context.
"""

from dataclasses import dataclass
from pathlib import Path
import json

from harness.adapter import MemoryAdapter
from harness.telemetry import TelemetryCollector
from harness.judge import JudgePipeline


@dataclass
class PlatformOpsResult:
    scenario: str
    tool: str
    correct: bool
    failure_mode: str
    reasoning: str
    latency_sec: float


# --- Scenario definitions ---

SCENARIOS = {
    "infra-continuity": {
        "description": "Troubleshooting a problem across multiple sessions",
        "turns": [
            {"role": "user", "content": "Session 1: The API is returning 500s. Checked logs — it's a DB connection pool exhaustion. Increased max_connections from 20 to 50."},
            {"role": "user", "content": "Session 2 (next day): API is still flaky. Checked — the connection pool fix from yesterday helped but there's a new issue: N+1 query in the /users endpoint. Added eager loading."},
            {"role": "user", "content": "Session 3 (next week): API is stable now. The root cause was two issues: connection pool exhaustion AND N+1 query. Both fixed."},
        ],
        "questions": [
            {
                "question": "What were the two root causes of the API 500s?",
                "gold_answer": "DB connection pool exhaustion and N+1 query in /users endpoint",
                "category": "multi-hop"
            },
            {
                "question": "What was the max_connections value increased to?",
                "gold_answer": "50",
                "category": "single-hop"
            }
        ]
    },
    "state-mutation": {
        "description": "Remembering that infrastructure state has changed",
        "turns": [
            {"role": "user", "content": "We are running Kubernetes 1.28 on the production cluster."},
            {"role": "user", "content": "Upgraded the production cluster to Kubernetes 1.29 today."},
            {"role": "user", "content": "The old ingress controller is deprecated. Switched to the new Gateway API."},
        ],
        "questions": [
            {
                "question": "What Kubernetes version is the production cluster running now?",
                "gold_answer": "1.29",
                "category": "temporal"
            },
            {
                "question": "What ingress technology are we using now?",
                "gold_answer": "Gateway API",
                "category": "temporal"
            }
        ]
    },
    "runbook-recall": {
        "description": "Retrieving the correct runbook for a given alert",
        "turns": [
            {"role": "user", "content": "Alert: HighMemoryUsage. Runbook: Scale the worker nodes. Check for memory leaks in the batch job."},
            {"role": "user", "content": "Alert: DiskFull. Runbook: Clean up old logs. Expand the EBS volume if needed."},
            {"role": "user", "content": "Alert: HighLatency. Runbook: Check the CDN. Verify the database query plan."},
        ],
        "questions": [
            {
                "question": "What is the runbook for DiskFull?",
                "gold_answer": "Clean up old logs. Expand the EBS volume if needed.",
                "category": "single-hop"
            },
            {
                "question": "Which alert requires checking the database query plan?",
                "gold_answer": "HighLatency",
                "category": "single-hop"
            }
        ]
    },
    "cross-project-isolation": {
        "description": "Ensuring memories from project A don't leak into project B",
        "turns": [
            {"role": "user", "content": "[Project: Alpha] The API key for Alpha is sk-alpha-123."},
            {"role": "user", "content": "[Project: Beta] The API key for Beta is sk-beta-456."},
            {"role": "user", "content": "[Project: Alpha] Deployed Alpha to us-east-1."},
            {"role": "user", "content": "[Project: Beta] Deployed Beta to eu-west-1."},
        ],
        "questions": [
            {
                "question": "[Project: Alpha] What is the API key?",
                "gold_answer": "sk-alpha-123",
                "category": "single-hop"
            },
            {
                "question": "[Project: Beta] What region is Beta deployed to?",
                "gold_answer": "eu-west-1",
                "category": "single-hop"
            },
            {
                "question": "[Project: Alpha] Does Alpha's memory contain Beta's API key?",
                "gold_answer": "No",
                "category": "adversarial"
            }
        ]
    },
    "incident-reconstruction": {
        "description": "Reconstructing the timeline of a past incident",
        "turns": [
            {"role": "user", "content": "2026-06-10 09:00: Alert fired — 99th percentile latency spiked to 2s."},
            {"role": "user", "content": "2026-06-10 09:15: Found the culprit: a missing database index on the events table."},
            {"role": "user", "content": "2026-06-10 09:30: Added index on events.created_at. Latency back to 200ms."},
            {"role": "user", "content": "2026-06-10 10:00: Post-mortem: the index was missed during the schema migration last week."},
        ],
        "questions": [
            {
                "question": "What was the root cause of the latency spike?",
                "gold_answer": "Missing database index on the events table",
                "category": "single-hop"
            },
            {
                "question": "What time was the index added?",
                "gold_answer": "09:30",
                "category": "temporal"
            },
            {
                "question": "When did the schema migration happen?",
                "gold_answer": "last week",
                "category": "temporal"
            }
        ]
    }
}


class PlatformOpsBenchmark:
    """Runs the PlatformOps-Mem benchmark for a single tool."""

    def __init__(self, adapter: MemoryAdapter, judge: JudgePipeline):
        self.adapter = adapter
        self.judge = judge

    def run_scenario(self, scenario_name: str) -> list[PlatformOpsResult]:
        if scenario_name not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = SCENARIOS[scenario_name]
        
        # Wipe and ingest
        self.adapter.wipe()
        self.adapter.add(scenario["turns"])
        self.adapter.await_ingest()
        
        results = []
        for q in scenario["questions"]:
            excerpts = self.adapter.search(q["question"])
            
            # For adversarial questions, we check if the tool leaks cross-project data
            if q["category"] == "adversarial" and "contain" in q["question"]:
                # Special check: does the search return the other project's data?
                all_text = " ".join(excerpts).lower()
                leaked = "sk-beta-456" in all_text if "Alpha" in q["question"] else "sk-alpha-123" in all_text
                correct = not leaked
                failure_mode = "cross_project_leak" if leaked else "none"
                results.append(PlatformOpsResult(
                    scenario=scenario_name,
                    tool=type(self.adapter).__name__,
                    correct=correct,
                    failure_mode=failure_mode,
                    reasoning="No cross-project leak detected" if correct else "Cross-project data leaked into search results",
                    latency_sec=0.0
                ))
            else:
                # Standard grading via judge pipeline
                model_answer = " ".join(excerpts)  # simplistic: the answer IS the retrieved text
                grade = self.judge.grade(q["question"], q["gold_answer"], model_answer, 1)
                results.append(PlatformOpsResult(
                    scenario=scenario_name,
                    tool=type(self.adapter).__name__,
                    correct=grade.correct,
                    failure_mode=grade.failure_mode,
                    reasoning=grade.reason,
                    latency_sec=0.0
                ))
        
        return results

    def run_all(self) -> dict:
        """Run all scenarios and return aggregated results."""
        all_results = []
        for scenario_name in SCENARIOS:
            all_results.extend(self.run_scenario(scenario_name))
        
        total = len(all_results)
        correct = sum(1 for r in all_results if r.correct)
        by_scenario = {}
        for r in all_results:
            by_scenario.setdefault(r.scenario, {"total": 0, "correct": 0})
            by_scenario[r.scenario]["total"] += 1
            if r.correct:
                by_scenario[r.scenario]["correct"] += 1
        
        failure_modes = {}
        for r in all_results:
            if r.failure_mode != "none":
                failure_modes[r.failure_mode] = failure_modes.get(r.failure_mode, 0) + 1
        
        return {
            "total_questions": total,
            "correct": correct,
            "accuracy": round(correct / total, 4) if total > 0 else 0.0,
            "by_scenario": {k: {"accuracy": round(v["correct"] / v["total"], 4), "total": v["total"]} for k, v in by_scenario.items()},
            "failure_modes": failure_modes,
            "detailed_results": [
                {
                    "scenario": r.scenario,
                    "correct": r.correct,
                    "failure_mode": r.failure_mode,
                    "reasoning": r.reasoning
                } for r in all_results
            ]
        }
