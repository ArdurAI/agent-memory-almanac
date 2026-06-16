#!/usr/bin/env bash
# Quest Benchmark Runner — convenience script
# Usage: ./run-benchmark.sh <tool> <benchmark> [track] [sample]

set -euo pipefail

TOOL="${1:-}"
BENCH="${2:-locomo}"
TRACK="${3:-open}"
SAMPLE="${4:-locomo-s300-seed42}"

if [ -z "$TOOL" ]; then
    echo "Usage: $0 <tool> [benchmark] [track] [sample]"
    echo ""
    echo "Examples:"
    echo "  $0 no-memory                    # Run no-memory canary (open track)"
    echo "  $0 basic-memory locomo open     # Run Basic Memory on LoCoMo open track"
    echo "  $0 mem0 locomo main             # Run Mem0 on LoCoMo main track (Claude)"
    echo "  $0 plainfile locomo open locomo-full  # Run full LoCoMo dataset"
    echo ""
    echo "Available tools:"
    echo "  Baselines: no-memory, plainfile, obsidian, naive-rag"
    echo "  Real: basic-memory, openmemory, mem0"
    echo ""
    echo "Tracks: open (cheap, fast) | main (Claude, higher cost)"
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="$REPO_ROOT/harness/results"
DATA_PATH="$REPO_ROOT/data/locomo.json"

mkdir -p "$RESULTS_DIR"

echo "======================================"
echo "Quest Benchmark Runner"
echo "Tool:      $TOOL"
echo "Benchmark: $BENCH"
echo "Track:     $TRACK"
echo "Sample:    $SAMPLE"
echo "Results:   $RESULTS_DIR"
echo "======================================"
echo ""

python3 -m harness.runner \
    --benchmark "$BENCH" \
    --tool "$TOOL" \
    --track "$TRACK" \
    --sample "$SAMPLE" \
    --results-dir "$RESULTS_DIR" \
    --data-path "$DATA_PATH"
