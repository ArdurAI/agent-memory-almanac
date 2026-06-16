"""
Results formatter — generates markdown tables from benchmark run JSON.

Usage:
    python -m harness.format_results harness/results/<run-id>/run.json

Outputs a markdown summary suitable for pasting into the almanac.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def format_run(path: Path) -> str:
    """Format a single run.json into a markdown summary."""
    data = json.loads(path.read_text())

    lines = []
    lines.append(f"## {data['tool']} — {data['benchmark']} ({data['track']})")
    lines.append("")
    lines.append(f"- **Run ID:** `{data['run_id']}`")
    lines.append(f"- **Date:** {data.get('run_timestamp_iso', 'unknown')}")
    lines.append(f"- **Answer model:** {data.get('answer_model', 'unknown')}")
    lines.append("")

    # Scores table
    lines.append("### Scores")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Graded | {data['graded']} |")
    lines.append(f"| Deterministic | {data['deterministic']} |")
    lines.append(f"| LLM judged | {data['llm_judged']} |")
    lines.append(f"| **Overall accuracy** | **{data['overall_accuracy']}** |")
    lines.append(f"| **Answerable accuracy** | **{data['answerable_accuracy']}** |")
    lines.append(f"| **Abstention accuracy** | **{data['abstention_accuracy']}** |")
    lines.append("")

    # By category
    if 'by_category' in data:
        lines.append("### Per category")
        lines.append("")
        lines.append("| Category | Questions | Accuracy |")
        lines.append("|----------|-----------|----------|")
        for cat, stats in sorted(data['by_category'].items(), key=lambda x: int(x[0])):
            lines.append(f"| {cat} | {stats['n']} | {stats['accuracy']} |")
        lines.append("")

    # Failure modes
    if 'failure_modes' in data:
        lines.append("### Failure modes")
        lines.append("")
        lines.append("| Failure mode | Count |")
        lines.append("|-------------|-------|")
        for mode, count in sorted(data['failure_modes'].items(), key=lambda x: -x[1]):
            lines.append(f"| {mode} | {count} |")
        lines.append("")

    # Ingest time
    if 'adapter_ingest_time_sec' in data:
        lines.append(f"**Ingest time:** {data['adapter_ingest_time_sec']}s")
        lines.append("")

    return "\n".join(lines)


def format_leaderboard(results_dir: Path) -> str:
    """Format all run.json files in a directory into a leaderboard table."""
    runs = []
    for run_file in results_dir.rglob("run.json"):
        try:
            data = json.loads(run_file.read_text())
            runs.append(data)
        except Exception:
            continue

    if not runs:
        return "No results found."

    # Sort by answerable accuracy descending
    runs.sort(key=lambda r: r.get('answerable_accuracy', 0), reverse=True)

    lines = []
    lines.append("# Benchmark Leaderboard")
    lines.append("")
    lines.append(f"*Generated {datetime.now().isoformat()}*")
    lines.append("")
    lines.append("| Rank | Tool | Track | Answerable | Overall | Abstention | Graded |")
    lines.append("|------|------|-------|------------|---------|------------|--------|")
    for i, r in enumerate(runs, 1):
        lines.append(
            f"| {i} | {r['tool']} | {r['track']} | "
            f"{r.get('answerable_accuracy', '-')} | "
            f"{r.get('overall_accuracy', '-')} | "
            f"{r.get('abstention_accuracy', '-')} | "
            f"{r.get('graded', '-')} |"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m harness.format_results <run.json|results_dir>")
        print("")
        print("  Single run:  python -m harness.format_results harness/results/locomo-mem0-open-123/run.json")
        print("  Leaderboard: python -m harness.format_results harness/results")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: path not found: {path}")
        sys.exit(1)

    if path.is_dir():
        print(format_leaderboard(path))
    else:
        print(format_run(path))


if __name__ == "__main__":
    main()
