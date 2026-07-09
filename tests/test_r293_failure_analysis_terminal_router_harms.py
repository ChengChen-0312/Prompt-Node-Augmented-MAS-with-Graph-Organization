import unittest


class TestR293FailureAnalysisTerminalRouterHarms(unittest.TestCase):
    def test_analyze_harms_detects_specialist_role_loss(self):
        from experiment.mmlu.r293_failure_analysis_terminal_router_harms import analyze_harms

        baseline = [
            {"task_id": "t", "is_correct": True, "roles": ["Mathematician", "Critic"]},
        ]
        promptnode = [
            {
                "task_id": "t",
                "is_correct": False,
                "roles": ["Historian", "PN_Memory", "PN_Verifier", "PN_Router"],
            }
        ]

        summary = analyze_harms(baseline_rows=baseline, promptnode_rows=promptnode)

        self.assertEqual(summary["harms"], 1)
        self.assertEqual(summary["harms_with_specialist_role_loss"], 1)
        self.assertFalse(summary["transfer_claim_supported"])


if __name__ == "__main__":
    unittest.main()
