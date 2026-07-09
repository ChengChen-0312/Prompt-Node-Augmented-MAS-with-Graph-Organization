import unittest


class AquaOptionBindingAuditTests(unittest.TestCase):
    def test_build_audit_prompt_contains_required_fields(self):
        from experiment.aqua.audit_option_binding import build_audit_prompt

        processed = {
            "task": "Question text Choices: A)1 B)2 C)3 D)4 E)5",
            "answer": "B",
            "step": "Official rationale. Answer B",
        }
        raw = {
            "question": "Question text",
            "options": ["A)1", "B)2", "C)3", "D)4", "E)5"],
            "correct": "B",
            "rationale": "Official rationale. Answer B",
        }
        messages = build_audit_prompt(
            processed,
            raw,
            "task_1",
            result_records={"baseline": {"predicted_answer": "C", "raw_response": "wrong"}},
        )
        text = "\n".join(message["content"] for message in messages)

        self.assertIn("task_1", text)
        self.assertIn("gold label", text.lower())
        self.assertIn("gold option text: B)2", text)
        self.assertIn("Official rationale", text)
        self.assertIn("baseline", text)
        self.assertIn("clean|noisy|ambiguous", text)
        self.assertIn("verify every arithmetic equation", text)

    def test_parse_audit_response_accepts_fenced_json(self):
        from experiment.aqua.audit_option_binding import parse_audit_response

        parsed = parse_audit_response(
            """
            reasoning text
            ```json
            {
              "clean_label": "noisy",
              "gold_binding_status": "contradictory",
              "target_preserved": false,
              "option_mismatch": true,
              "rationale_issue": "arithmetic_error",
              "faithful_answer": "NONE",
              "confidence": "high",
              "brief_reason": "Gold rationale contradicts its arithmetic."
            }
            ```
            """
        )

        self.assertEqual(parsed["clean_label"], "noisy")
        self.assertEqual(parsed["gold_binding_status"], "contradictory")
        self.assertFalse(parsed["target_preserved"])
        self.assertTrue(parsed["option_mismatch"])

    def test_make_record_and_summary(self):
        from experiment.aqua.audit_option_binding import make_audit_record, summarize_audits

        processed = {"task": "Q Choices: A)1", "answer": "A", "step": "rationale"}
        raw = {"question": "Q", "options": ["A)1"], "correct": "A", "rationale": "rationale"}
        audit = {
            "clean_label": "clean",
            "gold_binding_status": "exact",
            "target_preserved": True,
            "option_mismatch": False,
            "rationale_issue": "none",
            "faithful_answer": "A",
            "confidence": "high",
            "brief_reason": "ok",
        }
        record = make_audit_record(
            "task_1",
            processed,
            raw,
            audit,
            result_records={"baseline": {"predicted_answer": "A", "is_solved": True}},
        )
        summary = summarize_audits([record, {**record, "clean_label": "noisy"}])

        self.assertEqual(record["task_id"], "task_1")
        self.assertEqual(record["gold_answer"], "A")
        self.assertEqual(record["results"]["baseline"]["predicted_answer"], "A")
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["clean_label_counts"]["clean"], 1)
        self.assertEqual(summary["clean_label_counts"]["noisy"], 1)

    def test_make_record_overrides_obvious_linear_equation_error(self):
        from experiment.aqua.audit_option_binding import make_audit_record

        processed = {
            "task": "Q Choices: A)6 B)8 C)10 D)12 E)14",
            "answer": "C",
            "step": "(10)(12) = (8)(x)\n120 = 8x\n10 = x\nAnswer C",
        }
        raw = {
            "question": "Q",
            "options": ["A)6", "B)8", "C)10", "D)12", "E)14"],
            "correct": "C",
            "rationale": "(10)(12) = (8)(x)\n120 = 8x\n10 = x\nAnswer C",
        }
        audit = {
            "clean_label": "clean",
            "gold_binding_status": "exact",
            "target_preserved": True,
            "option_mismatch": False,
            "rationale_issue": "none",
            "faithful_answer": "C",
            "confidence": "high",
            "brief_reason": "LLM missed arithmetic.",
        }

        record = make_audit_record("task_152", processed, raw, audit)

        self.assertEqual(record["clean_label"], "noisy")
        self.assertEqual(record["rationale_issue"], "arithmetic_error")
        self.assertEqual(record["gold_binding_status"], "contradictory")
        self.assertTrue(record["deterministic_override"])

    def test_linear_equation_override_does_not_cross_example_lines(self):
        from experiment.aqua.audit_option_binding import make_audit_record

        rationale = (
            "x = 126, y = 315 - (9/7)126 = 153\n"
            "x = 133, y = 315 - (9/7)133 = 144\n"
            "Answer A"
        )
        processed = {"task": "Q Choices: A)15", "answer": "A", "step": rationale}
        raw = {"question": "Q", "options": ["A)15"], "correct": "A", "rationale": rationale}
        audit = {
            "clean_label": "clean",
            "gold_binding_status": "exact",
            "target_preserved": True,
            "option_mismatch": False,
            "rationale_issue": "none",
            "faithful_answer": "A",
            "confidence": "high",
            "brief_reason": "ok",
        }

        record = make_audit_record("task_21", processed, raw, audit)

        self.assertEqual(record["clean_label"], "clean")
        self.assertFalse(record["deterministic_override"])


if __name__ == "__main__":
    unittest.main()
