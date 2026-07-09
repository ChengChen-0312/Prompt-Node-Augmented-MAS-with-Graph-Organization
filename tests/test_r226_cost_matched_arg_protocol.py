import unittest

from experiment.mmlu.r226_cost_matched_arg_protocol import (
    build_cost_matched_manifest,
    estimate_allowed_requeries,
)


class TestR226CostMatchedARGProtocol(unittest.TestCase):
    def test_estimate_allowed_requeries_caps_by_task_count_and_budget(self):
        self.assertEqual(
            estimate_allowed_requeries(cost_cap=0.45, arg_cost_per_task=0.03, max_tasks=4),
            4,
        )
        self.assertEqual(
            estimate_allowed_requeries(cost_cap=0.05, arg_cost_per_task=0.03, max_tasks=4),
            1,
        )

    def test_build_manifest_marks_cost_matched_arg_requery_tasks(self):
        tasks = ["t1", "t2", "t3"]
        manifest = build_cost_matched_manifest(
            task_ids=tasks,
            cost_cap=0.45,
            arg_cost_per_task=0.03,
            max_tasks=2,
            source="unit",
        )

        self.assertEqual(len(manifest["tasks"]), 2)
        self.assertEqual(manifest["tasks"][0]["baseline_variant"], "cost_matched_arg_requery")
        self.assertFalse(manifest["tasks"][0]["api_executed"])
        self.assertEqual(manifest["estimated_total_cost"], 0.06)


if __name__ == "__main__":
    unittest.main()
