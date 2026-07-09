import unittest


class TestR369AdversarialVerifierApiProbe(unittest.TestCase):
    def test_api_probe_plan_is_bounded_and_leakage_checked(self):
        from experiment.mmlu.r369_adversarial_verifier_api_probe import build_api_probe_plan

        summary = build_api_probe_plan()

        self.assertEqual(summary["run_id"], "R369")
        self.assertEqual(summary["records"], 11)
        self.assertEqual(summary["api_calls_planned"], 11)
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["api_executed"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R369_execute_with_api_or_R370_analyze_if_executed")


if __name__ == "__main__":
    unittest.main()
