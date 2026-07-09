import unittest


class TestR407NonmathPromptNodeCurriculumDesign(unittest.TestCase):
    def test_design_defines_general_nonmath_nodes_edges_and_training_gate(self):
        from experiment.mmlu.r407_nonmath_promptnode_curriculum_design import build_curriculum_design

        summary = build_curriculum_design()

        self.assertEqual(summary["run_id"], "R407")
        self.assertFalse(summary["math_patch_only"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])

        node_types = {node["type"] for node in summary["promptnodes"]}
        self.assertGreaterEqual(len(node_types), 6)
        self.assertIn("InstructionAmbiguityVerifierPN", node_types)
        self.assertIn("OptionSemanticConsistencyVerifierPN", node_types)
        self.assertIn("ConceptDefinitionAnchorPN", node_types)
        self.assertIn("ContradictionDetectorPN", node_types)
        self.assertIn("AdversarialVerifierPN", node_types)
        self.assertIn("ConsensusConflictResolverPN", node_types)
        self.assertIn("MemoryBridgePN", node_types)

        edge_types = {edge["type"] for edge in summary["promptedges"]}
        self.assertIn("OptionBindingPromptEdge", edge_types)
        self.assertIn("AdversarialChallengePromptEdge", edge_types)
        self.assertIn("ConflictResolutionPromptEdge", edge_types)
        self.assertTrue(all(edge["prompt_as_edge"] for edge in summary["promptedges"]))

        self.assertEqual(summary["training_plan"]["policy"], "two_stage_candidate_then_learned_forward_gate")
        self.assertIn("node_agreement_count", summary["training_plan"]["features"])
        self.assertIn("contradiction_count", summary["training_plan"]["features"])
        self.assertIn("hard_negative_wrong_forward_weight", summary["training_plan"])

        self.assertTrue(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R408_nonmath_curriculum_fresh_preflight")


if __name__ == "__main__":
    unittest.main()
