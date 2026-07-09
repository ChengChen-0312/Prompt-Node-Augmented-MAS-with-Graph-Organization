import unittest


class TestR367AdversarialCandidateVerifierDesign(unittest.TestCase):
    def test_design_adds_adversarial_edge_and_domain_verifiers_without_relaxing_gate(self):
        from experiment.mmlu.r367_adversarial_candidate_verifier_design import build_adversarial_verifier_design

        summary = build_adversarial_verifier_design()
        node_ids = {node["id"] for node in summary["new_promptnodes"]}

        self.assertEqual(summary["run_id"], "R367")
        self.assertIn("PN_AdversarialCandidateVerifier", node_ids)
        self.assertIn("PN_ChemPhysicsVerifier", node_ids)
        self.assertIn("PN_PassageHistoryEntailmentVerifier", node_ids)
        self.assertIn("challenge_candidate_before_forward", summary["new_promptedges"])
        self.assertIn("block_forward_on_independent_contradiction", summary["new_promptedges"])
        self.assertEqual(summary["target_wrong_forward_task_ids"], ["MMLU-college_mathematics_test-15"])
        self.assertEqual(summary["target_missed_fix_count"], 10)
        self.assertFalse(summary["relax_gate_threshold"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R368_adversarial_verifier_preflight")


if __name__ == "__main__":
    unittest.main()
