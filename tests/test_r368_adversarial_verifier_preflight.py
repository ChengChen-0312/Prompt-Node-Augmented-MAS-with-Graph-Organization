import unittest


class TestR368AdversarialVerifierPreflight(unittest.TestCase):
    def test_preflight_targets_wrong_forward_and_missed_fixes_without_label_leakage(self):
        from experiment.mmlu.r368_adversarial_verifier_preflight import build_adversarial_preflight

        records, summary = build_adversarial_preflight()

        self.assertEqual(summary["run_id"], "R368")
        self.assertEqual(summary["target_task_count"], 11)
        self.assertEqual(summary["records"], 11)
        self.assertEqual(summary["variant_counts"]["adversarial_candidate_verifier_api"], 1)
        self.assertEqual(summary["variant_counts"]["domain_specialized_candidate_api"], 10)
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["uses_true_answers_in_prompt"])
        self.assertTrue(summary["api_probe_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R369_adversarial_verifier_api_probe")
        self.assertTrue(all("true_answer" not in "\n".join(m["content"] for m in row["model_visible_messages"]) for row in records))


if __name__ == "__main__":
    unittest.main()
