import unittest

from experiment.mmlu.r247_lifecycle_annotations import (
    annotate_decision_lifecycle,
    annotate_source_lifecycle,
    summarize_lifecycle_annotations,
)


class TestR247LifecycleAnnotations(unittest.TestCase):
    def test_fix_switch_updates_and_forwards(self):
        annotation = annotate_decision_lifecycle(
            {
                "task_id": "fix",
                "split_role": "frozen_eval",
                "switch": True,
                "fix": True,
                "harm": False,
                "clean_label": "clean",
            }
        )

        self.assertIn("update", annotation["lifecycle_actions"])
        self.assertIn("forward", annotation["edge_actions"])
        self.assertIn("upgrade", annotation["lifecycle_actions"])

    def test_clean_abstain_prunes_objective_evidence(self):
        annotation = annotate_decision_lifecycle(
            {
                "task_id": "protect",
                "switch": False,
                "baseline_correct": True,
                "selected_correct": True,
                "clean_label": "clean",
            }
        )

        self.assertIn("prune", annotation["lifecycle_actions"])
        self.assertIn("read", annotation["edge_actions"])

    def test_no_fix_requests_merge(self):
        annotation = annotate_decision_lifecycle(
            {
                "task_id": "nofix",
                "switch": True,
                "baseline_correct": False,
                "selected_correct": False,
            }
        )

        self.assertIn("merge", annotation["lifecycle_actions"])

    def test_dense_negative_source_requests_compress(self):
        annotation = annotate_source_lifecycle(
            {
                "run_id": "dense",
                "positive_accuracy_source": False,
                "promptnode_record_rate": 1.0,
                "records_with_promptnode_roles": 34,
            }
        )

        self.assertIn("compress", annotation["lifecycle_actions"])

    def test_summary_counts_actions(self):
        annotations = [
            {"lifecycle_actions": ["update", "upgrade"], "edge_actions": ["forward"]},
            {"lifecycle_actions": ["prune"], "edge_actions": ["read"]},
        ]

        summary = summarize_lifecycle_annotations(annotations)

        self.assertEqual(summary["lifecycle_action_counts"]["update"], 1)
        self.assertEqual(summary["lifecycle_action_counts"]["prune"], 1)
        self.assertEqual(summary["edge_action_counts"]["forward"], 1)


if __name__ == "__main__":
    unittest.main()
