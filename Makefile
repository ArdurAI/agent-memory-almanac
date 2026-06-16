# Agent Memory Almanac — Makefile

.PHONY: help test imports run-canary run-canary-dry run-plainfile run-plainfile-dry run-basic run-mem0 lint clean

PYTHON ?= python3
REPO_ROOT := $(shell pwd)

help: ## Show this help
	@echo "Quest Benchmark Harness — available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

test: ## Run integration tests (no API calls needed)
	@echo "Running harness tests..."
	@mkdir -p $(REPO_ROOT)/tmp
	@echo "import sys; sys.path.insert(0, '$(REPO_ROOT)')" > $(REPO_ROOT)/tmp/test_runner.py
	@echo "import harness.tests as t" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "grader = t.TestDeterministicGrader()" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "grader.test_exact_match()" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "grader.test_exact_match_case_insensitive()" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "grader.test_abstention_is_missing_recall()" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "grader.test_adversarial_abstention_correct()" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "grader.test_adversarial_answer_wrong()" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "grader.test_substring_match_short_answer()" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "print('  Deterministic grader: 6 tests passed')" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "telem = t.TestTelemetry()" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "telem.test_telemetry_summary()" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "print('  Telemetry: summary test passed')" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "loader = t.TestLoCoMoLoader()" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "loader.test_load_and_sample()" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "print('  LoCoMo loader: load + sample test passed')" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "" >> $(REPO_ROOT)/tmp/test_runner.py
	@echo "print('All tests passed.')" >> $(REPO_ROOT)/tmp/test_runner.py
	@cd $(REPO_ROOT) && $(PYTHON) tmp/test_runner.py

imports: ## Verify all harness modules import cleanly
	@echo "Checking imports..."
	@mkdir -p $(REPO_ROOT)/tmp
	@echo "import sys; sys.path.insert(0, '$(REPO_ROOT)')" > $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapter, harness.telemetry, harness.judge, harness.runner" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.transport, harness.answer, harness.data_loader" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.stress_suite, harness.bench_platformops, harness.bench_locomo" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.no_memory, harness.adapters.plainfile" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.obsidian, harness.adapters.naive_rag" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.basic_memory, harness.adapters.openmemory" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.mem0" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.graphiti" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.cognee" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.honcho" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.hindsight" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.memvid" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.memos" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.memori" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.memobase" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "import harness.adapters.langmem" >> $(REPO_ROOT)/tmp/import_test.py
	@echo "print('All imports OK')" >> $(REPO_ROOT)/tmp/import_test.py
	@cd $(REPO_ROOT) && $(PYTHON) tmp/import_test.py

run-canary-dry: ## Run the no-memory canary in dry-run mode (no API calls)
	@echo "Running no-memory canary (dry-run)..."
	cd $(REPO_ROOT) && $(PYTHON) -m harness.runner \
		--benchmark locomo --tool no-memory --track open \
		--sample locomo-s300-seed42 --dry-run

run-plainfile-dry: ## Run the plainfile baseline in dry-run mode (no API calls)
	@echo "Running plainfile baseline (dry-run)..."
	cd $(REPO_ROOT) && $(PYTHON) -m harness.runner \
		--benchmark locomo --tool plainfile --track open \
		--sample locomo-s300-seed42 --dry-run

run-canary: ## Run the no-memory canary (requires API key for answering model)
	@echo "Running no-memory canary..."
	chmod +x $(REPO_ROOT)/run-benchmark.sh
	$(REPO_ROOT)/run-benchmark.sh no-memory locomo open locomo-s300-seed42

run-plainfile: ## Run the plainfile baseline (open track, requires API key)
	@echo "Running plainfile baseline..."
	chmod +x $(REPO_ROOT)/run-benchmark.sh
	$(REPO_ROOT)/run-benchmark.sh plainfile locomo open locomo-s300-seed42

run-basic: ## Run Basic Memory on open track (requires API key)
	@echo "Running Basic Memory..."
	chmod +x $(REPO_ROOT)/run-benchmark.sh
	$(REPO_ROOT)/run-benchmark.sh basic-memory locomo open locomo-s300-seed42

run-mem0: ## Run Mem0 on open track (requires API key)
	@echo "Running Mem0..."
	chmod +x $(REPO_ROOT)/run-benchmark.sh
	$(REPO_ROOT)/run-benchmark.sh mem0 locomo open locomo-s300-seed42

lint: ## Check Python syntax
	@echo "Checking syntax..."
	cd $(REPO_ROOT) && $(PYTHON) -m py_compile harness/*.py harness/adapters/*.py

clean: ## Remove generated results
	@echo "Cleaning results..."
	rm -rf $(REPO_ROOT)/harness/results
	rm -rf $(REPO_ROOT)/tmp
