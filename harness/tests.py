"""
Integration tests for the Quest harness.

Tests the full pipeline with baseline adapters to verify the harness works
correctly before any real tool runs.

No pytest dependency — run with: python -m harness.tests
"""

import json
from pathlib import Path
import tempfile
import math

from harness.adapter import MemoryAdapter, AdapterResult
from harness.telemetry import TelemetryCollector
from harness.judge import JudgePipeline, DeterministicGrader
from harness.runner import BenchmarkRunner
from harness.data_loader import LoCoMoLoader
from harness.adapters.no_memory import NoMemoryAdapter
from harness.adapters.plainfile import PlainFileAdapter
from harness.adapters.obsidian import ObsidianAdapter
from harness.adapters.naive_rag import NaiveRAGAdapter


def approx(a, b, abs_tol=0.0001):
    """Simple approximation check, no pytest needed."""
    return math.isclose(a, b, abs_tol=abs_tol)


class TestDeterministicGrader:
    """Test the deterministic grading rules."""

    def test_exact_match(self):
        g = DeterministicGrader.grade("Q", "42", "42", category=1)
        assert g is not None
        assert g.correct is True
        assert g.graded_by == "deterministic"

    def test_exact_match_case_insensitive(self):
        g = DeterministicGrader.grade("Q", "Paris", "paris", category=1)
        assert g is not None
        assert g.correct is True

    def test_abstention_is_missing_recall(self):
        g = DeterministicGrader.grade("Q", "42", "I don't know", category=1)
        assert g is not None
        assert g.correct is False
        assert g.failure_mode == "missing_recall"

    def test_adversarial_abstention_correct(self):
        g = DeterministicGrader.grade("Q", "42", "I don't know", category=5)
        assert g is not None
        assert g.correct is True
        assert g.failure_mode == "none"

    def test_adversarial_answer_wrong(self):
        g = DeterministicGrader.grade("Q", "42", "Actually it's 43", category=5)
        assert g is not None
        assert g.correct is False
        assert g.failure_mode == "wrong_abstention"

    def test_substring_match_short_answer(self):
        g = DeterministicGrader.grade("Q", "us-east-1", "The server is in us-east-1", category=1)
        assert g is not None
        assert g.correct is True

    def test_long_answer_no_substring(self):
        g = DeterministicGrader.grade("Q", "a very long ground truth answer that is not short", "a very long ground truth answer that is not short", category=1)
        assert g is not None
        assert g.correct is True


class TestBaselineAdapters:
    """Test baseline adapters implement the contract correctly."""

    def test_no_memory_returns_empty(self):
        a = NoMemoryAdapter()
        a.add([{"role": "user", "content": "hello"}])
        r = a.search("hello")
        assert r.metadata["excerpts"] == []

    def test_plainfile_stores_and_retrieves(self):
        with tempfile.TemporaryDirectory() as td:
            a = PlainFileAdapter(file_path=Path(td) / "memory.txt")
            a.add([{"role": "user", "content": "The server is in us-east-1"}])
            a.add([{"role": "user", "content": "The database is Postgres"}])
            r = a.search("server")
            assert len(r.metadata["excerpts"]) > 0
            assert "us-east-1" in r.metadata["excerpts"][0]

    def test_plainfile_wipe_clears(self):
        with tempfile.TemporaryDirectory() as td:
            a = PlainFileAdapter(file_path=Path(td) / "memory.txt")
            a.add([{"role": "user", "content": "hello"}])
            a.wipe()
            r = a.search("hello")
            assert r.metadata["excerpts"] == []

    def test_obsidian_stores_markdown(self):
        with tempfile.TemporaryDirectory() as td:
            a = ObsidianAdapter(vault_path=Path(td) / "vault")
            a.add([{"role": "user", "content": "hello", "timestamp": "2026-01-01T00:00:00Z"}])
            notes = list(a.vault_path.glob("*.md"))
            assert len(notes) == 1
            assert "2026-01-01T00:00:00Z" in notes[0].read_text()

    def test_naive_rag_retrieves(self):
        a = NaiveRAGAdapter()
        a.add([{"role": "user", "content": "The server is in us-east-1"}])
        a.add([{"role": "user", "content": "The database is Postgres"}])
        r = a.search("server location")
        assert len(r.metadata["excerpts"]) > 0


class TestRunnerPipeline:
    """Test the full runner pipeline with synthetic data."""

    def test_no_memory_canary(self):
        with tempfile.TemporaryDirectory() as td:
            results_dir = Path(td)
            adapter = NoMemoryAdapter()
            judge = JudgePipeline("dummy-model", "open")
            runner = BenchmarkRunner(
                benchmark="locomo",
                tool="no-memory",
                track="open",
                results_dir=results_dir,
                adapter=adapter,
                judge=judge,
                answer_model="dummy-model",
            )
            # Override answer to always abstain (simulating no retrieval)
            runner._answer = lambda q, e: "I don't know"

            scenario_data = [
                {
                    "question_id": "q1",
                    "conversation_id": "c1",
                    "question": "What is the answer?",
                    "gold_answer": "42",
                    "category": 1,
                    "turns": [{"role": "user", "content": "The answer is 42"}],
                },
                {
                    "question_id": "q2",
                    "conversation_id": "c1",
                    "question": "What is the secret?",
                    "gold_answer": "secret",
                    "category": 5,
                    "turns": [],
                },
            ]

            summary = runner.run(scenario_data)
            assert summary["answerable_accuracy"] == 0.0
            assert summary["abstention_accuracy"] == 1.0
            assert approx(summary["overall_accuracy"], 0.5, abs_tol=0.01)
            assert "failure_modes" in summary

            # Verify files were created
            assert (runner.run_dir / "run.json").exists()
            assert (runner.run_dir / "per_question.jsonl").exists()
            assert (runner.run_dir / "telemetry.json").exists()

    def test_plainfile_answers(self):
        with tempfile.TemporaryDirectory() as td:
            results_dir = Path(td)
            adapter = PlainFileAdapter(file_path=Path(td) / "memory.txt")
            judge = JudgePipeline("dummy-model", "open")
            runner = BenchmarkRunner(
                benchmark="locomo",
                tool="plainfile",
                track="open",
                results_dir=results_dir,
                adapter=adapter,
                judge=judge,
                answer_model="dummy-model",
            )
            # Override answer to return the first excerpt (simple simulation)
            runner._answer = lambda q, e: e[0] if e else "I don't know"

            scenario_data = [
                {
                    "question_id": "q1",
                    "conversation_id": "c1",
                    "question": "What is the answer?",
                    "gold_answer": "42",
                    "category": 1,
                    "turns": [{"role": "user", "content": "The answer is 42"}],
                },
            ]

            summary = runner.run(scenario_data)
            assert summary["graded"] == 1
            assert "failure_modes" in summary


class TestTelemetry:
    """Test telemetry collection."""

    def test_telemetry_summary(self):
        t = TelemetryCollector("test-run")
        t.record("add", "tool1", start=0.0, end=1.0, tokens_prompt=100, tokens_completion=50, model="test")
        t.record("search", "tool1", start=1.0, end=1.5, tokens_prompt=20, tokens_completion=10, model="test")
        s = t.summary()
        assert s["total_calls"] == 2
        assert s["total_latency_sec"] == 1.5
        assert s["total_tokens"] == 180
        assert "by_method" in s

    def test_telemetry_cost(self):
        t = TelemetryCollector("test-run")
        t.record("answer", None, start=0.0, end=2.0, tokens_prompt=1000, tokens_completion=500, model="anthropic/claude-sonnet-4.6")
        s = t.summary()
        # 1000 * 3.00 + 500 * 15.00 = 3000 + 7500 = 10500 / 1M = 0.0105
        assert approx(s["total_cost_usd"], 0.0105, abs_tol=0.0001)


class TestLoCoMoLoader:
    """Test LoCoMo data loading."""

    def test_load_and_sample(self):
        with tempfile.TemporaryDirectory() as td:
            data_path = Path(td) / "locomo.json"
            data = {
                "conversations": [
                    {
                        "id": "c1",
                        "turns": [{"role": "user", "content": "hello"}],
                        "qa": [
                            {"id": "q1", "question": "Q1", "answer": "A1", "category": 1},
                            {"id": "q2", "question": "Q2", "answer": "A2", "category": 1},
                            {"id": "q3", "question": "Q3", "answer": "A3", "category": 2},
                        ]
                    },
                    {
                        "id": "c2",
                        "turns": [{"role": "user", "content": "world"}],
                        "qa": [
                            {"id": "q4", "question": "Q4", "answer": "A4", "category": 1},
                            {"id": "q5", "question": "Q5", "answer": "A5", "category": 5},
                        ]
                    }
                ]
            }
            data_path.write_text(json.dumps(data))

            loader = LoCoMoLoader(data_path)
            full = loader.load()
            assert len(full) == 5

            sample = loader.stratified_sample(n=2, seed=42)
            assert len(sample) == 2
            # All sampled items should be from the original data
            all_ids = {q["question_id"] for q in full}
            for s in sample:
                assert s["question_id"] in all_ids

            stats = loader.stats()
            assert stats["total_questions"] == 5
