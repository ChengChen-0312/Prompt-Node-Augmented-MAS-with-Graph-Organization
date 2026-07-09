import unittest


class TestR398NonmathContrastiveVerifierDesign(unittest.TestCase):
    def test_design_adds_general_nonmath_promptnodes_and_edges(self):
        from experiment.mmlu.r398_nonmath_contrastive_verifier_design import build_design_summary

        summary = build_design_summary()

        self.assertEqual(summary["run_id"], "R398")
        self.assertIn("PN_ContrastiveOptionVerifier", summary["promptnode_roles"])
        self.assertIn("PN_ConceptDefinitionAnchor", summary["promptnode_roles"])
        self.assertIn("PN_AbstentionRecoveryVerifier", summary["promptnode_roles"])
        self.assertIn("PE_RejectNearestDistractor", summary["promptedge_roles"])
        self.assertIn("PE_EvidenceSpecificityGate", summary["promptedge_roles"])
        self.assertTrue(summary["targeted_probe_authorized_next"])
        self.assertFalse(summary["api_execution_authorized_now"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R399_contrastive_verifier_targeted_preflight")


if __name__ == "__main__":
    unittest.main()
