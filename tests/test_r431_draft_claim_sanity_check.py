import unittest


class TestR431DraftClaimSanityCheck(unittest.TestCase):
    def test_sanity_check_removes_forbidden_phrases_and_checks_goal(self):
        from experiment.mmlu.r431_draft_claim_sanity_check import run_sanity_check

        summary = run_sanity_check()

        self.assertEqual(summary["run_id"], "R431")
        self.assertTrue(summary["draft_sanity_pass"])
        self.assertEqual(summary["remaining_forbidden_hits"], [])
        self.assertIn("submission-ready", summary["replacements_applied"])
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R427", "R428", "R429", "R430", "R431"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R432_paper_main_tex_scaffold")


if __name__ == "__main__":
    unittest.main()
