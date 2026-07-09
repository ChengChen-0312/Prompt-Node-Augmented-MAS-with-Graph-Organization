import unittest
from pathlib import Path


class TestR445ExternalAuditPayloadExport(unittest.TestCase):
    def test_exports_external_audit_payloads_without_transmitting(self):
        from experiment.mmlu.r445_external_audit_payload_export import run_export

        summary = run_export()

        self.assertEqual(summary["run_id"], "R445")
        self.assertEqual(len(summary["payloads_created"]), 3)
        for payload in summary["payloads_created"]:
            self.assertTrue(Path(payload["payload_md"]).exists())
            self.assertGreater(Path(payload["payload_md"]).stat().st_size, 1000)
        self.assertEqual(summary["external_reviews_executed"], [])
        self.assertFalse(summary["browser_submission_performed"])
        self.assertTrue(summary["requires_confirmation_before_transmission"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R446_local_tables_and_submission_gaps")


if __name__ == "__main__":
    unittest.main()
