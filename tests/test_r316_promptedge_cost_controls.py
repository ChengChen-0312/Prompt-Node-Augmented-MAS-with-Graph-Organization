import unittest


class TestR316PromptedgeCostControls(unittest.TestCase):
    def test_manifest_contains_plain_requery_and_node_only_controls(self):
        from experiment.mmlu.r316_promptedge_cost_controls import build_manifest_records

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

        rows = build_manifest_records(arg_rows, split_rows)
        variants = {row["control_variant"] for row in rows}

        self.assertEqual(len(rows), 3)
        self.assertEqual(variants, {"arg_baseline_fixed", "plain_requery", "node_only_no_promptedge_text"})
        self.assertFalse([row for row in rows if row["control_variant"] == "arg_baseline_fixed"][0]["api_required"])
        self.assertTrue(all(row["leakage_pass"] for row in rows))
        self.assertNotIn("PromptEdges:", [row for row in rows if row["control_variant"] == "node_only_no_promptedge_text"][0]["model_visible_messages"][1]["content"])

    def test_apply_plain_requery_response_scores_fix(self):
        from experiment.mmlu.r316_promptedge_cost_controls import apply_control_response

        record = {
            "control_variant": "plain_requery",
            "api_required": True,
            "evaluation_only": {"true_answer": "C", "arg_prediction": "A"},
        }

        row = apply_control_response(record, '{"selected_label":"C"}', api_executed=True)

        self.assertEqual(row["predicted_answer"], "C")
        self.assertTrue(row["fix"])

    def test_node_only_still_requires_high_confidence_switch(self):
        from experiment.mmlu.r316_promptedge_cost_controls import apply_control_response

        record = {
            "control_variant": "node_only_no_promptedge_text",
            "api_required": True,
            "evaluation_only": {"true_answer": "C", "arg_prediction": "A"},
        }

        row = apply_control_response(record, '{"action":"SWITCH","final_label":"C","confidence":"medium"}', api_executed=True)

        self.assertEqual(row["predicted_answer"], "A")
        self.assertFalse(row["fix"])


if __name__ == "__main__":
    unittest.main()
