import unittest


class TestR408NonmathCurriculumFreshPreflight(unittest.TestCase):
    def test_preflight_builds_leakage_free_curriculum_manifest(self):
        from experiment.mmlu.r408_nonmath_curriculum_fresh_preflight import build_curriculum_preflight

        records, summary = build_curriculum_preflight()

        self.assertEqual(summary["run_id"], "R408")
        self.assertGreater(summary["tasks"], 0)
        self.assertEqual(summary["api_records"], summary["tasks"] * 2)
        self.assertEqual(summary["planned_arg_baseline_calls"], summary["tasks"])
        self.assertEqual(summary["planned_curriculum_candidate_calls"], summary["tasks"])
        self.assertTrue(summary["leakage_pass"])
        self.assertTrue(summary["api_execution_authorized_next"])

        candidate_rows = [row for row in records if row["control_variant"] == "nonmath_curriculum_candidate_api"]
        self.assertEqual(len(candidate_rows), summary["tasks"])
        first_prompt = "\n".join(message["content"] for message in candidate_rows[0]["model_visible_messages"])
        self.assertIn("InstructionAmbiguityVerifierPN", first_prompt)
        self.assertIn("ConceptDefinitionAnchorPN", first_prompt)
        self.assertIn("AdversarialVerifierPN", first_prompt)
        self.assertIn("ConsensusConflictResolverPN", first_prompt)
        self.assertIn("Return compact JSON", first_prompt)
        self.assertNotIn("true_answer", first_prompt.lower())
        self.assertNotIn("task_id", first_prompt.lower())

        self.assertIn("InstructionAmbiguityVerifierPN", summary["node_types"])
        self.assertIn("ConflictResolutionPromptEdge", summary["edge_types"])
        self.assertEqual(summary["next_required_run"], "R409_nonmath_curriculum_api_execution")


if __name__ == "__main__":
    unittest.main()
