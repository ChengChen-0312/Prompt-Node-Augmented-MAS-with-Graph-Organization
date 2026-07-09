import unittest


class TestR404IntegrityAuditPreflight(unittest.TestCase):
    def test_preflight_collects_audit_artifacts_without_claiming_pass(self):
        from experiment.mmlu.r404_integrity_audit_preflight import build_audit_preflight

        summary = build_audit_preflight()

        self.assertEqual(summary["run_id"], "R404")
        self.assertGreater(summary["artifact_counts"]["evaluation_scripts"], 0)
        self.assertGreater(summary["artifact_counts"]["result_files"], 0)
        self.assertGreater(summary["artifact_counts"]["paper_claims"], 0)
        self.assertTrue(summary["external_review_required"])
        self.assertFalse(summary["integrity_audit_complete"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R405_experiment_integrity_local_precheck")


if __name__ == "__main__":
    unittest.main()
