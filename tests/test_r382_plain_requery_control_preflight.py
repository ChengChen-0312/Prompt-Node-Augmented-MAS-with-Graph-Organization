import unittest


class TestR382PlainRequeryControlPreflight(unittest.TestCase):
    def test_preflight_builds_plain_requery_control_on_r379_tasks(self):
        from experiment.mmlu.r382_plain_requery_control_preflight import build_plain_requery_preflight

        records, summary = build_plain_requery_preflight()

        self.assertEqual(summary["run_id"], "R382")
        self.assertEqual(summary["tasks"], 24)
        self.assertEqual(summary["api_records"], 24)
        self.assertEqual(summary["planned_plain_requery_calls"], 24)
        self.assertTrue(summary["same_task_set_as_r379"])
        self.assertTrue(summary["leakage_pass"])
        self.assertTrue(summary["api_execution_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R383_plain_requery_control_api_execution")
        self.assertEqual({row["control_variant"] for row in records}, {"plain_requery_control_api"})


if __name__ == "__main__":
    unittest.main()
