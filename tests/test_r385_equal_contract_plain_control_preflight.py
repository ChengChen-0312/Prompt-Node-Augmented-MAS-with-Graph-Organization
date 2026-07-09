import unittest


class TestR385EqualContractPlainControlPreflight(unittest.TestCase):
    def test_preflight_builds_equal_contract_plain_control(self):
        from experiment.mmlu.r385_equal_contract_plain_control_preflight import build_equal_contract_preflight

        records, summary = build_equal_contract_preflight()

        self.assertEqual(summary["run_id"], "R385")
        self.assertEqual(summary["tasks"], 24)
        self.assertEqual(summary["api_records"], 24)
        self.assertEqual(summary["planned_equal_contract_plain_calls"], 24)
        self.assertTrue(summary["same_task_set_as_r379"])
        self.assertTrue(summary["leakage_pass"])
        self.assertTrue(summary["api_execution_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R386_equal_contract_plain_control_api_execution")
        self.assertEqual({row["control_variant"] for row in records}, {"equal_contract_plain_control_api"})


if __name__ == "__main__":
    unittest.main()
