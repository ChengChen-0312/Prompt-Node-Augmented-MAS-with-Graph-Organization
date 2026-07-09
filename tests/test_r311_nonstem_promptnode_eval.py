import unittest


class TestR311NonstemPromptNodeEval(unittest.TestCase):
    def test_low_confidence_switch_keeps_arg(self):
        from experiment.mmlu.r311_nonstem_promptnode_eval import apply_guarded_response

        record = {
            "api_required": True,
            "evaluation_only": {"true_answer": "C", "arg_prediction": "A"},
        }

        row = apply_guarded_response(
            record,
            '{"action":"SWITCH","final_label":"C","confidence":"medium"}',
            api_executed=True,
        )

        self.assertEqual(row["predicted_answer"], "A")
        self.assertEqual(row["fallback_reason"], "guarded_keep_arg")
        self.assertFalse(row["fix"])

    def test_high_confidence_switch_can_fix_arg(self):
        from experiment.mmlu.r311_nonstem_promptnode_eval import apply_guarded_response

        record = {
            "api_required": True,
            "evaluation_only": {"true_answer": "C", "arg_prediction": "A"},
        }

        row = apply_guarded_response(
            record,
            '{"action":"SWITCH","final_label":"C","confidence":"high"}',
            api_executed=True,
        )

        self.assertEqual(row["predicted_answer"], "C")
        self.assertTrue(row["fix"])

    def test_manifest_pairs_arg_and_promptnode_records(self):
        from experiment.mmlu.r311_nonstem_promptnode_eval import build_manifest_records

        arg_rows = [
            {
                "task_id": "t1",
                "subject": "philosophy",
                "question": "Q\nOption A: a\nOption B: b\nOption C: c\nOption D: d",
                "true_answer": "B",
                "predicted_answer": "A",
            }
        ]
        split_rows = [{"task_id": "t1", "candidate": {"candidate_type": "instruction_ambiguity_verifier"}}]

        records = build_manifest_records(arg_rows, split_rows)

        self.assertEqual(len(records), 2)
        self.assertEqual({row["control_variant"] for row in records}, {"arg_baseline_fixed", "proposed_nonstem_promptnode_promptedge"})
        self.assertFalse(records[0]["api_required"])
        self.assertTrue(records[1]["api_required"])
        self.assertTrue(records[1]["leakage_pass"])


if __name__ == "__main__":
    unittest.main()
