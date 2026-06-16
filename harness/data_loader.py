"""
LoCoMo dataset loader.

Handles the standard LoCoMo JSON format and produces the flat question-level
records the harness expects.

Expected input format (from snap-research/locomo):
{
  "conversations": [
    {
      "id": "conv_001",
      "turns": [
        {"role": "user", "content": "...", "timestamp": "..."},
        {"role": "assistant", "content": "...", "timestamp": "..."}
      ],
      "qa": [
        {
          "id": "q_001",
          "question": "What did X say about Y?",
          "answer": "Z",
          "category": 1
        }
      ]
    }
  ]
}
"""

import json
import random
from pathlib import Path
from typing import Optional


class LoCoMoLoader:
    """Loads and samples the LoCoMo dataset."""

    def __init__(self, data_path: Path):
        self.data_path = data_path
        self._data: Optional[list[dict]] = None

    def load(self) -> list[dict]:
        """Load the full LoCoMo dataset into flat question records."""
        if self._data is not None:
            return self._data

        if not self.data_path.exists():
            raise FileNotFoundError(
                f"LoCoMo data not found at {self.data_path}. "
                f"Download from https://github.com/snap-research/locomo"
            )

        with self.data_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        records = []
        # Handle both top-level "conversations" key and raw list
        conversations = raw.get("conversations", raw) if isinstance(raw, dict) else raw

        for conv in conversations:
            conv_id = conv.get("id", "unknown")
            turns = conv.get("turns", [])
            for qa in conv.get("qa", []):
                records.append({
                    "question_id": qa.get("id", f"{conv_id}-{len(records)}"),
                    "conversation_id": conv_id,
                    "question": qa["question"],
                    "gold_answer": qa["answer"],
                    "category": qa.get("category", 1),
                    "turns": turns,
                })

        self._data = records
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

        total = len(data)
        sample = []
        for cat, items in sorted(by_category.items()):
            target = max(1, round(n * len(items) / total))
            selected = rng.sample(items, min(target, len(items)))
            sample.extend(selected)

        # Fill if short
        while len(sample) < n:
            largest = max(by_category.values(), key=len)
            remaining = [i for i in largest if i not in sample]
            if remaining:
                sample.append(rng.choice(remaining))
            else:
                break

        rng.shuffle(sample)
        return sample[:n]

    def stats(self) -> dict:
        """Return dataset statistics."""
        data = self.load()
        by_category = {}
        for item in data:
            cat = item["category"]
            by_category.setdefault(cat, 0)
            by_category[cat] += 1

        return {
            "total_questions": len(data),
            "by_category": {str(k): v for k, v in sorted(by_category.items())},
        }
