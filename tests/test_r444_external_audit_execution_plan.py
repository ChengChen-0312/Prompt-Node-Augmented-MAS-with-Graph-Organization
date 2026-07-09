import unittest


class TestR444ExternalAuditExecutionPlan(unittest.TestCase):
    def test_execution_plan_orders_external_audits_without_marking_executed(self):
        from experiment.mmlu.r444_external_audit_execution_plan import run_plan

        summary = run_plan()

        self.assertEqual(summary["run_id"], "R444")
        self.assertEqual(
            summary["execution_order"],
            ["experiment_integrity_audit", "paper_claim_audit", "citation_context_audit"],
        )
        self.assertTrue(summary["external_audit_execution_ready"])
        self.assertEqual(summary["external_reviews_executed"], [])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R445_external_audit_execution_or_manual_import")


if __name__ == "__main__":
    unittest.main()
