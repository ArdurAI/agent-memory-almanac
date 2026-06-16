"""
Main orchestrator: setup → run → grade → emit results.

Usage:
    python -m harness.runner \
        --benchmark locomo|stress|platformops \
        --tool <tool-name> \
        --results-dir harness/results

Every run produces a timestamped result directory with:
- run.json (metadata, scores, failure-mode taxonomy)
- per_question.jsonl (excerpts, verbatim answer, grade per question)
- telemetry.json (raw per-call telemetry)
- adapter_state.json (post-run memory dump)
"""

import argparse
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from harness.telemetry import TelemetryCollector
from harness.judge import JudgePipeline
from harness.adapter import MemoryAdapter


class BenchmarkRunner:
    """Orchestrates a single benchmark run from start to finish."""

    def __init__(self, benchmark: str, tool: str, track: str, results_dir: Path,
                 adapter: MemoryAdapter, judge: JudgePipeline):
        self.benchmark = benchmark
        self.tool = tool
        self.track = track
        self.results_dir = results_dir
        self.adapter = adapter
        self.judge = judge
        self.run_timestamp = int(time.time())
        self.run_id = f"{benchmark}-{tool}-{track}-{self.run_timestamp}"
        self.telemetry = TelemetryCollector(self.run_id)

        # Create result directory
        self.run_dir = results_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=False)

    def run(self, scenario_data: list[dict]) -> dict:
        """
        Run the full benchmark pipeline.

        scenario_data: list of question dicts, each with:
            - question_id
            - question
            - gold_answer
            - category (1-5 for LoCoMo)
            - conversation_turns (for ingestion)
        """
        # --- Phase 1: Setup ---
        self.adapter.setup()

        # --- Phase 2: Ingestion ---
        # Group turns by conversation and feed to adapter
        for conv in self._group_by_conversation(scenario_data):
            self.adapter.add(conv["turns"])

        # Wait for async ingestion
        ingest_result = self.adapter.await_ingest()

        # --- Phase 3: Retrieval + Answering ---
        per_question_records = []
        for item in scenario_data:
            # Retrieve context
            excerpts = self.adapter.search(item["question"])

            # Answer (placeholder — real implementation calls the answering model)
            model_answer = self._answer(item["question"], excerpts)

            # Grade
            grade = self.judge.grade(
                question=item["question"],
                gold_answer=item["gold_answer"],
                model_answer=model_answer,
                category=item.get("category", 1)
            )

            per_question_records.append({
                "question_id": item["question_id"],
                "question": item["question"],
                "gold_answer": item["gold_answer"],
                "model_answer": model_answer,
                "excerpts": excerpts,
                "category": item.get("category", 1),
                "grade": {
                    "correct": grade.correct,
                    "confidence": grade.confidence,
                    "failure_mode": grade.failure_mode,
                    "reason": grade.reason,
                    "graded_by": grade.graded_by,
                    "pass_number": grade.pass_number,
                }
            })

        # --- Phase 4: Export + Wipe ---
        adapter_state = self.adapter.export()
        self.adapter.wipe()

        # --- Phase 5: Aggregate + Save ---
        run_summary = self._aggregate(per_question_records)
        run_summary["run_id"] = self.run_id
        run_summary["benchmark"] = self.benchmark
        run_summary["tool"] = self.tool
        run_summary["track"] = self.track
        run_summary["run_timestamp"] = self.run_timestamp
        run_summary["run_timestamp_iso"] = datetime.now(timezone.utc).isoformat()
        run_summary["adapter_ingest_time_sec"] = ingest_result.elapsed_sec if ingest_result else 0.0

        # Save files
        (self.run_dir / "run.json").write_text(json.dumps(run_summary, indent=2))
        with (self.run_dir / "per_question.jsonl").open("w") as f:
            for rec in per_question_records:
                f.write(json.dumps(rec) + "\n")
        self.telemetry.save(self.run_dir / "telemetry.json")
        (self.run_dir / "adapter_state.json").write_text(json.dumps(adapter_state, indent=2))

        return run_summary

    def _group_by_conversation(self, scenario_data: list[dict]) -> list[dict]:
        """Group scenario data by conversation ID for batch ingestion."""
        from collections import defaultdict
        convs = defaultdict(list)
        for item in scenario_data:
            cid = item.get("conversation_id", "default")
            convs[cid].append(item)
        return [{"conversation_id": cid, "turns": items} for cid, items in convs.items()]

    def _answer(self, question: str, excerpts: list[str]) -> str:
        """Placeholder: calls the answering model. Implement in submodules."""
        # TODO: wire to actual answering model via transport
        return "I don't know"

    def _aggregate(self, records: list[dict]) -> dict:
        """Aggregate per-question grades into run-level scores."""
        total = len(records)
        correct = sum(1 for r in records if r["grade"]["correct"])
        deterministic = sum(1 for r in records if r["grade"]["graded_by"] == "deterministic")
        llm_judged = sum(1 for r in records if "llm_judge" in r["grade"]["graded_by"])

        # By category
        by_category = {}
        for r in records:
            cat = r["category"]
            by_category.setdefault(cat, {"n": 0, "correct": 0})
            by_category[cat]["n"] += 1
            if r["grade"]["correct"]:
                by_category[cat]["correct"] += 1

        by_category_out = {}
        for cat, stats in by_category.items():
            by_category_out[str(cat)] = {
                "n": stats["n"],
                "accuracy": round(stats["correct"] / stats["n"], 4) if stats["n"] > 0 else 0.0
            }

        # Failure modes
        failure_modes = {}
        for r in records:
            fm = r["grade"]["failure_mode"]
            failure_modes[fm] = failure_modes.get(fm, 0) + 1

        # Answerable (categories 1-4) vs abstention (category 5)
        answerable_n = sum(1 for r in records if r["category"] != 5)
        answerable_correct = sum(1 for r in records if r["category"] != 5 and r["grade"]["correct"])
        abstention_n = sum(1 for r in records if r["category"] == 5)
        abstention_correct = sum(1 for r in records if r["category"] == 5 and r["grade"]["correct"])

        return {
            "graded": total,
            "deterministic": deterministic,
            "llm_judged": llm_judged,
            "overall_accuracy": round(correct / total, 4) if total > 0 else 0.0,
            "answerable_accuracy": round(answerable_correct / answerable_n, 4) if answerable_n > 0 else 0.0,
            "abstention_accuracy": round(abstention_correct / abstention_n, 4) if abstention_n > 0 else 0.0,
            "by_category": by_category_out,
            "failure_modes": failure_modes,
        }


def main():
    parser = argparse.ArgumentParser(description="Quest Benchmark Runner")
    parser.add_argument("--benchmark", required=True, choices=["locomo", "stress", "platformops"])
    parser.add_argument("--tool", required=True, help="Tool name from the roster")
    parser.add_argument("--track", default="main", choices=["main", "open"])
    parser.add_argument("--results-dir", default="harness/results", type=Path)
    parser.add_argument("--sample", default="locomo-s300-seed42", help="Sample identifier")
    args = parser.parse_args()

    # TODO: load adapter by tool name, load benchmark data, instantiate judge
    print(f"Runner scaffold ready for {args.benchmark} / {args.tool} / {args.track}")
    print(f"Results will go to: {args.results_dir}")


if __name__ == "__main__":
    main()
