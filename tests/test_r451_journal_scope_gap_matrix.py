import unittest


class TestR451JournalScopeGapMatrix(unittest.TestCase):
    def test_scope_matrix_selects_jair_and_bounds_claims(self):
        from experiment.mmlu.r451_journal_scope_gap_matrix import run_matrix

        summary = run_matrix()

        self.assertEqual(summary["run_id"], "R451")
        self.assertEqual(summary["primary_target"], "JAIR")
        self.assertEqual(summary["secondary_target"], "KAIS")
        self.assertGreaterEqual(len(summary["scope_gap_matrix"]), 5)
        self.assertIn("agents_and_multi_agent_systems", summary["target_scope_terms"]["JAIR"])
        self.assertIn("knowledge_systems", summary["target_scope_terms"]["KAIS"])
        self.assertIn("no_broad_nonmath_improvement_claim", summary["claim_tightening_actions"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R452_five_run_goal_audit_and_compile_probe")


if __name__ == "__main__":
    unittest.main()
