import unittest


class TestR412FreshDefinitionChallengeGatePreflight(unittest.TestCase):
    def test_preflight_builds_fresh_definition_challenge_manifest(self):
        from experiment.mmlu.r412_fresh_definition_challenge_gate_preflight import build_definition_challenge_preflight

        records, summary = build_definition_challenge_preflight()

        self.assertEqual(summary["run_id"], "R412")
        self.assertEqual(summary["subjects"], 3)
        self.assertGreater(summary["tasks"], 0)
        self.assertEqual(summary["api_records"], summary["tasks"] * 2)
        self.assertTrue(summary["leakage_pass"])
        self.assertTrue(summary["api_execution_authorized_next"])

        candidate_rows = [row for row in records if row["control_variant"] == "definition_challenge_candidate_api"]
        self.assertEqual(len(candidate_rows), summary["tasks"])
        prompt = "\n".join(message["content"] for message in candidate_rows[0]["model_visible_messages"])
        self.assertIn("DefinitionChallengeGate", prompt)
        self.assertIn("ConceptDefinitionAnchorPN", prompt)
        self.assertIn("AdversarialVerifierPN", prompt)
        self.assertIn("Return raw JSON object only", prompt)
        self.assertNotIn("true_answer", prompt.lower())
        self.assertNotIn("task_id", prompt.lower())

        self.assertEqual(summary["next_required_run"], "R413_definition_challenge_gate_api_execution")


if __name__ == "__main__":
    unittest.main()
