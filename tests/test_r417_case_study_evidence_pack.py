import unittest


class TestR417CaseStudyEvidencePack(unittest.TestCase):
    def test_case_pack_extracts_fix_prune_and_gate_selection_cases(self):
        from experiment.mmlu.r417_case_study_evidence_pack import build_case_study_pack

        summary = build_case_study_pack()

        self.assertEqual(summary["run_id"], "R417")
        self.assertGreaterEqual(len(summary["case_studies"]), 3)
        cases = {case["case_id"]: case for case in summary["case_studies"]}
        self.assertIn("definition_challenge_fix", cases)
        self.assertIn("verifier_pruned_candidate_harm", cases)
        self.assertIn("gate_beats_candidate_pool", cases)
        self.assertEqual(cases["definition_challenge_fix"]["task_id"], "MMLU-nonstem-moral_disputes_test-14")
        self.assertEqual(cases["verifier_pruned_candidate_harm"]["task_id"], "MMLU-nonstem-logical_fallacies_test-12")
        self.assertIn("ConceptDefinitionAnchorPN", cases["definition_challenge_fix"]["graph_elements"])
        self.assertIn("ConflictResolutionPromptEdge", cases["verifier_pruned_candidate_harm"]["graph_elements"])

        self.assertEqual(summary["lifecycle_trace_status"], "partial_needs_explicit_runtime_logging")
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R418_lifecycle_trace_instrumentation_preflight")


if __name__ == "__main__":
    unittest.main()
