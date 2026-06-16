import sys; sys.path.insert(0, '/Users/gnutakki16/Documents/kimi/workspace/agent-memory-almanac')
import harness.tests as t

grader = t.TestDeterministicGrader()
grader.test_exact_match()
grader.test_exact_match_case_insensitive()
grader.test_abstention_is_missing_recall()
grader.test_adversarial_abstention_correct()
grader.test_adversarial_answer_wrong()
grader.test_substring_match_short_answer()
print('  Deterministic grader: 6 tests passed')

telem = t.TestTelemetry()
telem.test_telemetry_summary()
print('  Telemetry: summary test passed')

loader = t.TestLoCoMoLoader()
loader.test_load_and_sample()
print('  LoCoMo loader: load + sample test passed')

print('All tests passed.')
