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
from pathlib import Path
from datetime import datetime, timezone

from harness.telemetry import TelemetryCollector
from harness.judge import JudgePipeline
from harness.adapter import MemoryAdapter
from harness.answer import answer_question
from harness.data_loader import LoCoMoLoader
from harness.transport import TransportFactory


class BenchmarkRunner:
    """Orchestrates a single benchmark run from start to finish."""

    def __init__(self, benchmark: str, tool: str, track: str, results_dir: Path,
                 adapter: MemoryAdapter, judge: JudgePipeline, answer_model: str,
                 dry_run: bool = False):
        self.benchmark = benchmark
        self.tool = tool
        self.track = track
        self.results_dir = results_dir
        self.adapter = adapter
        self.judge = judge
        self.answer_model = answer_model
        self.dry_run = dry_run
        self.run_timestamp = int(time.time())
        self.run_id = f"{benchmark}-{tool}-{track}-{self.run_timestamp}"
        self.telemetry = TelemetryCollector(self.run_id)

        self.run_dir = results_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=False)

    def run(self, scenario_data: list[dict]) -> dict:
        """Run the full LoCoMo-style benchmark pipeline."""
        self.adapter.setup()

        # Ingestion
        for conv in self._group_by_conversation(scenario_data):
            self.adapter.add(conv["turns"])
        ingest_result = self.adapter.await_ingest()

        # Retrieval + Answering + Grading
        per_question_records = []
        for item in scenario_data:
            search_result = self.adapter.search(item["question"])
            excerpts = search_result.metadata.get("excerpts", []) if search_result else []
            model_answer = self._answer(item["question"], excerpts)
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

        # Export + Wipe
        adapter_state_result = self.adapter.export()
        adapter_state = adapter_state_result.metadata if adapter_state_result else {}
        self.adapter.wipe()

        # Aggregate + Save
        run_summary = self._aggregate(per_question_records)
        run_summary["run_id"] = self.run_id
        run_summary["benchmark"] = self.benchmark
        run_summary["tool"] = self.tool
        run_summary["track"] = self.track
        run_summary["run_timestamp"] = self.run_timestamp
        run_summary["run_timestamp_iso"] = datetime.now(timezone.utc).isoformat()
        run_summary["adapter_ingest_time_sec"] = ingest_result.elapsed_sec if ingest_result else 0.0
        run_summary["answer_model"] = self.answer_model

        (self.run_dir / "run.json").write_text(json.dumps(run_summary, indent=2))
        with (self.run_dir / "per_question.jsonl").open("w") as f:
            for rec in per_question_records:
                f.write(json.dumps(rec) + "\n")
        self.telemetry.save(self.run_dir / "telemetry.json")
        (self.run_dir / "adapter_state.json").write_text(json.dumps(adapter_state, indent=2))

        return run_summary

    def run_stress(self, scenarios: list[str]) -> dict:
        """Run the stress suite for a single tool."""
        from harness.stress_suite import run_stress_suite

        self.adapter.setup()
        results = run_stress_suite(self.adapter, scenarios=scenarios)
        self.adapter.wipe()

        summary = {
            "run_id": self.run_id,
            "benchmark": self.benchmark,
            "tool": self.tool,
            "track": self.track,
            "run_timestamp": self.run_timestamp,
            "run_timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "scenarios": [r.scenario for r in results],
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
            "total": len(results),
            "detailed_results": [
                {
                    "scenario": r.scenario,
                    "passed": r.passed,
                    "verdict": r.verdict,
                    "failure_modes": r.failure_modes,
                    "latency_sec": r.latency_sec,
                    "metrics": r.metrics,
                }
                for r in results
            ],
        }

        (self.run_dir / "run.json").write_text(json.dumps(summary, indent=2))
        self.telemetry.save(self.run_dir / "telemetry.json")
        return summary

    def run_platformops(self) -> dict:
        """Run the PlatformOps-Mem benchmark for a single tool."""
        from harness.bench_platformops import PlatformOpsBenchmark

        benchmark = PlatformOpsBenchmark(self.adapter, self.judge)
        all_results = benchmark.run_all()

        summary = {
            "run_id": self.run_id,
            "benchmark": self.benchmark,
            "tool": self.tool,
            "track": self.track,
            "run_timestamp": self.run_timestamp,
            "run_timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "answer_model": self.answer_model,
            "total_questions": all_results["total_questions"],
            "correct": all_results["correct"],
            "accuracy": all_results["accuracy"],
            "by_scenario": all_results["by_scenario"],
            "failure_modes": all_results["failure_modes"],
            "detailed_results": all_results["detailed_results"],
        }

        (self.run_dir / "run.json").write_text(json.dumps(summary, indent=2))
        self.telemetry.save(self.run_dir / "telemetry.json")
        return summary

    def _group_by_conversation(self, scenario_data: list[dict]) -> list[dict]:
        from collections import defaultdict
        convs = defaultdict(lambda: {"conversation_id": "", "turns": []})
        for item in scenario_data:
            cid = item.get("conversation_id", "default")
            convs[cid]["conversation_id"] = cid
            if not convs[cid]["turns"]:
                convs[cid]["turns"] = item.get("turns", [])
        return list(convs.values())

    def _answer(self, question: str, excerpts: list[str]) -> str:
        if self.dry_run:
            if excerpts:
                return excerpts[0]
            return "I don't know"
        return answer_question(
            question=question, excerpts=excerpts,
            model=self.answer_model, track=self.track,
            telemetry=self.telemetry,
        )

    def _aggregate(self, records: list[dict]) -> dict:
        total = len(records)
        correct = sum(1 for r in records if r["grade"]["correct"])
        deterministic = sum(1 for r in records if r["grade"]["graded_by"] == "deterministic")
        llm_judged = sum(1 for r in records if "llm_judge" in r["grade"]["graded_by"])

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

        failure_modes = {}
        for r in records:
            fm = r["grade"]["failure_mode"]
            failure_modes[fm] = failure_modes.get(fm, 0) + 1

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
    parser.add_argument("--data-path", default="data/locomo.json", type=Path, help="Path to LoCoMo dataset")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without calling LLM APIs — returns first excerpt as answer")
    parser.add_argument("--stress-scenarios", default="all",
                        help="Comma-separated stress scenarios (for --benchmark stress)")
    args = parser.parse_args()

    answer_model = (
        "anthropic/claude-sonnet-4.6" if args.track == "main"
        else "deepseek-v4-pro"
    )
    judge_model = (
        "anthropic/claude-opus-4.8" if args.track == "main"
        else "qwen3.5:397b"
    )

    adapter = _load_adapter(args.tool)
    judge = JudgePipeline(judge_model, args.track)

    runner = BenchmarkRunner(
        benchmark=args.benchmark, tool=args.tool, track=args.track,
        results_dir=args.results_dir, adapter=adapter, judge=judge,
        answer_model=answer_model, dry_run=args.dry_run,
    )

    print(f"Running {args.benchmark} / {args.tool} / {args.track}")
    print(f"Answer model: {answer_model}")
    print(f"Judge model: {judge_model}")
    if args.dry_run:
        print("Mode: DRY RUN (no API calls)")
    print(f"Results dir: {runner.run_dir}")
    print()

    if args.benchmark == "locomo":
        loader = LoCoMoLoader(args.data_path)
        if args.sample == "locomo-s300-seed42":
            scenario_data = loader.stratified_sample(n=300, seed=42)
        elif args.sample == "locomo-full":
            scenario_data = loader.load()
        else:
            raise ValueError(f"Unknown sample: {args.sample}")
        print(f"Questions: {len(scenario_data)}")
        summary = runner.run(scenario_data)
        print(f"\nOverall: {summary['overall_accuracy']}")
        print(f"Answerable: {summary['answerable_accuracy']}")
        print(f"Abstention: {summary['abstention_accuracy']}")

    elif args.benchmark == "stress":
        if args.stress_scenarios == "all":
            scenarios = None
        else:
            scenarios = [s.strip() for s in args.stress_scenarios.split(",")]
        summary = runner.run_stress(scenarios)
        print(f"\nPassed: {summary['passed']} / {summary['total']}")
        for r in summary["detailed_results"]:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"  [{status}] {r['scenario']}: {r['verdict']}")

    elif args.benchmark == "platformops":
        summary = runner.run_platformops()
        print(f"\nAccuracy: {summary['accuracy']}")
        for scenario, stats in summary["by_scenario"].items():
            print(f"  {scenario}: {stats['accuracy']} ({stats['total']} questions)")

    print(f"\nResults: {runner.run_dir}")


def _load_adapter(tool_name: str) -> MemoryAdapter:
    adapters = {
        "no-memory": "harness.adapters.no_memory",
        "plainfile": "harness.adapters.plainfile",
        "obsidian": "harness.adapters.obsidian",
        "naive-rag": "harness.adapters.naive_rag",
        "basic-memory": "harness.adapters.basic_memory",
        "openmemory": "harness.adapters.openmemory",
        "mem0": "harness.adapters.mem0",
        "graphiti": "harness.adapters.graphiti",
        "cognee": "harness.adapters.cognee",
        "honcho": "harness.adapters.honcho",
        "hindsight": "harness.adapters.hindsight",
        "memvid": "harness.adapters.memvid",
        "memos": "harness.adapters.memos",
        "memori": "harness.adapters.memori",
        "memobase": "harness.adapters.memobase",
        "langmem": "harness.adapters.langmem",
    }
    if tool_name not in adapters:
        raise ValueError(f"Unknown tool: {tool_name}. Known tools: {list(adapters.keys())}")
    import importlib
    module = importlib.import_module(adapters[tool_name])
    class_name = "".join(part.capitalize() for part in tool_name.replace("-", "_").split("_")) + "Adapter"
    return getattr(module, class_name)()


if __name__ == "__main__":
    main()
