import unittest


class TestR468SubmissionReadinessMatrix(unittest.TestCase):
    def test_matrix_separates_local_ready_items_from_submission_blockers(self):
        from experiment.mmlu.r468_submission_readiness_matrix import run_matrix

        summary = run_matrix()

        self.assertEqual(summary["run_id"], "R468")
        self.assertEqual(summary["readiness_matrix"]["local_manuscript_artifacts"]["status"], "ready_local")
        self.assertEqual(summary["readiness_matrix"]["external_audits"]["status"], "blocked")
        self.assertEqual(summary["readiness_matrix"]["pdf_compile"]["status"], "blocked")
        self.assertEqual(summary["readiness_matrix"]["official_jcr_verification"]["status"], "blocked")
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R469_local_smoke_after_jcr_readiness")


if __name__ == "__main__":
    unittest.main()
