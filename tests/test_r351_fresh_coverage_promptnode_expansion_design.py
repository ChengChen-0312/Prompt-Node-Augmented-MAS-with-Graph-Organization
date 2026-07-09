import unittest


class TestR351FreshCoveragePromptnodeExpansionDesign(unittest.TestCase):
    def test_design_expands_coverage_with_general_stem_and_nonstem_promptnodes(self):
        from experiment.mmlu.r351_fresh_coverage_promptnode_expansion_design import build_coverage_expansion_design

        summary = build_coverage_expansion_design()
        node_ids = {node["id"] for node in summary["expanded_promptnodes"]}

        self.assertEqual(summary["run_id"], "R351")
        self.assertTrue(summary["r349_reclassified_as_coverage_dev_set"])
        self.assertFalse(summary["uses_r349_for_main_claim"])
        self.assertIn("PN_NumericWordProblemSolver", node_ids)
        self.assertIn("PN_PhysicsFormulaEvaluator", node_ids)
        self.assertIn("PN_ChemistryConceptAndStoichiometryTool", node_ids)
        self.assertIn("PN_PassageEntailmentVerifier", node_ids)
        self.assertIn("PN_DefinitionFallacyVerifier", node_ids)
        self.assertIn("PN_ClozeSemanticConsistencyVerifier", node_ids)
        self.assertIn("reject_if_no_machine_or_textual_evidence", summary["promptedge_contracts"])
        self.assertGreaterEqual(summary["target_min_forwarded_candidates_next"], 8)
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R352_fresh_coverage_promptnode_expansion_preflight")


if __name__ == "__main__":
    unittest.main()
