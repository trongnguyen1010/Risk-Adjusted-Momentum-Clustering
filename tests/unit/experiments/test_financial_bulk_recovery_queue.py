import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('bulk_queue', Path(__file__).resolve().parents[3] / 'scripts/financial_bulk_recovery_queue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BulkRecoveryQueueTests(unittest.TestCase):
    def test_overlap_is_not_double_counted_and_displacement_is_not_hidden(self):
        self.assertEqual(module.primary_reason(['ACCOUNTING_OR_FINANCE_QA_HELD', 'DISPLACEMENT_REVIEW_REQUIRED'], None), 'DISPLACEMENT_REVIEW_REQUIRED')

    def test_old_missing_cfo_diagnosis_cannot_hide_new_gate_result(self):
        self.assertEqual(module.primary_reason(['MISSING_INPUTS'], 'HELD_UNCHANGED_ACCOUNTING_DISPLACEMENT_OR_CORE_GATES'), 'CFO_ALREADY_FOUND_OTHER_GATES_HELD')
        self.assertEqual(module.primary_reason(['MISSING_INPUTS'], 'INVALID_OR_FAILED_COMPONENT_OBSERVATION'), 'MISSING_INPUTS')

    def test_partition_ambiguity_is_preserved_even_with_qa_failure(self):
        self.assertEqual(module.primary_reason(['MULTIPLE_PROVIDER_PARTITIONS_NO_SOURCE_PRIORITY', 'ACCOUNTING_OR_FINANCE_QA_HELD'], None), 'MULTIPLE_PROVIDER_PARTITIONS_NO_SOURCE_PRIORITY')

    def test_cost_ranking_never_accepts_or_removes_candidate_dependencies(self):
        item = dict(registry_id='A', gaps=[dict(primary_blocker='ACCOUNTING_OR_FINANCE_QA_HELD', failed_checks=['OTHER_PROFIT'])])
        duplicate = dict(registry_id='B', gaps=item['gaps'] * 2)
        self.assertLess(module.rank(item), module.rank(duplicate))
        self.assertEqual(len(duplicate['gaps']), 2)
