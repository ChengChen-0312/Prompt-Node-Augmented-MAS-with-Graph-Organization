import unittest

from experiment.mmlu.r222_control_manifest_leakage_scan import scan_control_rows


class TestR222ControlManifestLeakageScan(unittest.TestCase):
    def _row(self):
        return {
            "control_variant": "abstain_only_router",
            "model_visible_input": {"baseline_prediction": "A"},
            "router_final_schema": {
                "model_visible_fields": ["policy_input.baseline_prediction"],
                "forbidden_model_visible_fields": ["task_id", "is_correct", "true_answer"],
                "gold_answer_used": False,
            },
        }

    def test_clean_rows_pass_scan(self):
        summary = scan_control_rows([self._row(), self._row()])

        self.assertEqual(summary["records"], 2)
        self.assertTrue(summary["leakage_pass"])
        self.assertEqual(summary["leakage_violations"], 0)

    def test_model_visible_input_forbidden_key_fails_scan(self):
        row = self._row()
        row["model_visible_input"]["task_id"] = "task_1"

        summary = scan_control_rows([row])

        self.assertFalse(summary["leakage_pass"])
        self.assertEqual(summary["leakage_violations"], 1)
        self.assertEqual(summary["violations"][0]["reason"], "model_visible_input_forbidden_fields")

    def test_schema_visible_forbidden_field_fails_scan(self):
        row = self._row()
        row["router_final_schema"]["model_visible_fields"].append("task_id")

        summary = scan_control_rows([row])

        self.assertFalse(summary["leakage_pass"])
        self.assertEqual(summary["violations"][0]["reason"], "schema_visible_forbidden_fields")


if __name__ == "__main__":
    unittest.main()
