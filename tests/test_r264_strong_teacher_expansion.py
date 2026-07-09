import unittest

from experiment.aqua.r264_strong_teacher_expansion import (
    build_strong_teacher_records,
    build_target_task_rows,
    parse_strong_teacher_response,
    scan_prompt_leakage,
    summarize_teacher_expansion,
)


class TestR264StrongTeacherExpansion(unittest.TestCase):
    def sample_rows(self):
        return [
            {
                "task_id": "task_59",
                "question": "Question one Choices: A)1 B)2 C)3 D)4 E)5",
                "true_answer": "C",
                "predicted_answer": "D",
                "baseline_prediction": "B",
                "is_solved": False,
            },
            {
                "task_id": "task_139",
                "question": "Question two Choices: A)1 B)2 C)3 D)4 E)5",
                "true_answer": "E",
                "predicted_answer": "D",
                "baseline_prediction": "D",
                "is_solved": False,
            },
            {
                "task_id": "task_1",
                "question": "Already solved Choices: A)1 B)2 C)3 D)4 E)5",
                "true_answer": "A",
                "predicted_answer": "A",
                "baseline_prediction": "A",
                "is_solved": True,
            },
        ]

    def test_records_target_r065_errors_and_keep_gold_eval_only(self):
        targets = build_target_task_rows(self.sample_rows(), ["task_59", "task_139"])
        records = build_strong_teacher_records(targets, model="gpt-4o-2024-08-06")

        self.assertGreater(len(records), 2)
        self.assertEqual({row["task_id"] for row in records}, {"task_59", "task_139"})
        for row in records:
            self.assertIn("true_answer", row["evaluation_only"])
            visible_text = "\n".join(m["content"] for m in row["model_visible_messages"])
            self.assertNotIn("task_59", visible_text)
            self.assertNotIn("task_139", visible_text)
            self.assertNotIn("true_answer", visible_text)
            self.assertFalse(row["gold_answer_used_in_prompt"])
            self.assertTrue(scan_prompt_leakage(row)["leakage_pass"])

    def test_parser_accepts_json_fences_and_text_fallback(self):
        parsed_json = parse_strong_teacher_response(
            '```json\n{"selected_label":"C","confidence":0.82,"abstain":false}\n```'
        )
        parsed_text = parse_strong_teacher_response("After checking the options, Answer: E")
        parsed_loose_json = parse_strong_teacher_response(
            '{"selected_label": "D", "confidence": 0.9, "abstain": false, "evidence_checks": "loose"}'
        )
        parsed_truncated_json = parse_strong_teacher_response(
            '{"selected_label": "D", "confidence": 0.9, "abstain": false, "evidence_checks": "unterminated'
        )

        self.assertEqual(parsed_json["selected_label"], "C")
        self.assertAlmostEqual(parsed_json["confidence"], 0.82)
        self.assertFalse(parsed_json["abstain"])
        self.assertEqual(parsed_text["selected_label"], "E")
        self.assertFalse(parsed_text["abstain"])
        self.assertEqual(parsed_loose_json["selected_label"], "D")
        self.assertFalse(parsed_loose_json["abstain"])
        self.assertEqual(parsed_truncated_json["selected_label"], "D")
        self.assertFalse(parsed_truncated_json["abstain"])

    def test_summary_reports_oracle_and_non_oracle_teacher_ceiling(self):
        targets = build_target_task_rows(self.sample_rows(), ["task_59", "task_139"])
        records = build_strong_teacher_records(targets, model="gpt-4o-2024-08-06")[:4]
        outputs = []
        for row in records:
            response = '{"selected_label":"C","confidence":0.9,"abstain":false}'
            if row["task_id"] == "task_139":
                response = '{"selected_label":"E","confidence":0.9,"abstain":false}'
            out = dict(row)
            out["raw_response"] = response
            out["parsed_response"] = parse_strong_teacher_response(response)
            out["api_executed"] = True
            out["api_error"] = ""
            outputs.append(out)

        summary = summarize_teacher_expansion(outputs, r065_correct=31, total_tasks=34)

        self.assertEqual(summary["oracle_fixed_task_ids"], ["task_139", "task_59"])
        self.assertEqual(summary["oracle_teacher_accuracy"], "33/34")
        self.assertEqual(summary["non_oracle_teacher_accuracy"], "33/34")


if __name__ == "__main__":
    unittest.main()
