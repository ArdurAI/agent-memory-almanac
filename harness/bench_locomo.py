"""
LoCoMo benchmark harness.

LoCoMo: 1,986 questions over 10 multi-session conversations.
The Quest uses a stratified 300-question sample (seed 42) for rapid iteration,
with full-1,986 runs for published numbers. The sample is disclosed on every row.

Categories:
1. multi-hop (43 questions) — requires connecting facts across sessions
2. temporal (48 questions) — requires reasoning about event ordering
3. open-domain (15 questions) — requires general knowledge + memory
4. single-hop (127 questions) — direct recall from a single session
5. adversarial (67 questions) — correct answer is to abstain

Pipeline: each tool really ingests all 10 conversations → really retrieves per
question → a frozen answering model sees ONLY the retrieved excerpts → graded
by deterministic rules first, frozen LLM judge for the ambiguous rest.
"""

from pathlib import Path
import json
import random
from typing import Optional

from harness.runner import BenchmarkRunner
from harness.telemetry import TelemetryCollector
from harness.judge import JudgePipeline


# Category names for reporting
CATEGORY_NAMES = {
    1: "multi-hop",
    2: "temporal",
    3: "open-domain",
    4: "single-hop",
    5: "adversarial",
}


class LoCoMoDataset:
    """Loads and samples the LoCoMo dataset."""

    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.full_data = None
        self.sample = None

    def load(self) -> list[dict]:
        """Load the full LoCoMo dataset."""
        # TODO: integrate actual LoCoMo data loader
        # For now, return a scaffold structure
        if self.full_data is None:
            self.full_data = self._load_from_disk()
        return self.full_data

    def _load_from_disk(self) -> list[dict]:
        """Load from the LoCoMo JSON format."""
        # The real LoCoMo data is a list of conversations with nested QA pairs.
        # This is a scaffold that expects the standard format.
        if not self.data_path.exists():
            return []
        with self.data_path.open() as f:
            data = json.load(f)
        # Flatten to question-level records
        records = []
        for conv in data:
            conv_id = conv.get("id", "unknown")
            for qa in conv.get("qa", []):
                records.append({
                    "question_id": qa.get("id", f"{conv_id}-{len(records)}"),
                    "conversation_id": conv_id,
                    "question": qa["question"],
                    "gold_answer": qa["answer"],
                    "category": qa.get("category", 1),
                    "turns": conv.get("turns", []),
                })
        return records

    def stratified_sample(self, n: int = 300, seed: int = 42) -> list[dict]:
        """Draw a stratified sample preserving category proportions."""
        data = self.load()
        if not data:
            return []

        rng = random.Random(seed)
        by_category = {}
        for item in data:
            cat = item["category"]
            by_category.setdefault(cat, []).append(item)

        # Proportional allocation
        total = len(data)
        sample = []
        for cat, items in sorted(by_category.items()):
            target = max(1, round(n * len(items) / total))
            selected = rng.sample(items, min(target, len(items)))
            sample.extend(selected)

        # If we're short, fill from the largest category
        while len(sample) < n:
            largest = max(by_category.values(), key=len)
            remaining = [i for i in largest if i not in sample]
            if remaining:
                sample.append(rng.choice(remaining))
            else:
                break

        rng.shuffle(sample)
        return sample[:n]


class LoCoMoBenchmark:
    """Runs the LoCoMo benchmark for a single tool."""

    def __init__(self, dataset: LoCoMoDataset, runner: BenchmarkRunner):
        self.dataset = dataset
        self.runner = runner

    def run(self, sample_id: str = "locomo-s300-seed42") -> dict:
        """Run the benchmark and return the summary."""
        # Parse sample identifier
        if sample_id.startswith("locomo-s300"):
            sample = self.dataset.stratified_sample(n=300, seed=42)
        elif sample_id == "locomo-full":
            sample = self.dataset.load()
        else:
            raise ValueError(f"Unknown sample: {sample_id}")

        # Flatten turns for ingestion
        scenario_data = []
        for item in sample:
            scenario_data.append({
                "question_id": item["question_id"],
                "conversation_id": item["conversation_id"],
                "question": item["question"],
                "gold_answer": item["gold_answer"],
                "category": item["category"],
                "turns": item["turns"],
            })

        return self.runner.run(scenario_data)
