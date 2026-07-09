import unittest


class TestR347ToolBackedPromptnodeProspectiveReplay24(unittest.TestCase):
    def test_replay24_improves_arg_without_harming_correct_baseline_items(self):
        from experiment.mmlu.r347_tool_backed_promptnode_prospective_replay24 import build_replay24

        records, summary = build_replay24()

        self.assertEqual(summary["run_id"], "R347")
        self.assertEqual(summary["records"], 24)
        self.assertEqual(summary["arg_correct"], 20)
        self.assertEqual(summary["tool_promptnode_correct"], 24)
        self.assertEqual(summary["tool_promptnode_delta_correct"], 4)
        self.assertEqual(summary["forwarded_candidate_count"], 4)
        self.assertEqual(summary["fixes"], 4)
        self.assertEqual(summary["harms"], 0)
        self.assertEqual(summary["accuracy"], 1.0)
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertTrue(summary["claim_permissions"]["replay_mechanism_evidence_allowed"])
        self.assertTrue(all(row["final_prediction"] == row["true_answer"] for row in records))
        self.assertEqual(summary["next_required_run"], "R348_fresh_tool_promptnode_eval_design")


if __name__ == "__main__":
    unittest.main()
