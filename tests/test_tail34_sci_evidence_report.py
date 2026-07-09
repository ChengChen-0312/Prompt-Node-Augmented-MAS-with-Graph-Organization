import unittest


class Tail34SciEvidenceReportTests(unittest.TestCase):
    def test_summarize_method_splits_audit_and_cost(self):
        from experiment.aqua.tail34_sci_evidence_report import summarize_method

        baseline = [
            {"task_id": "clean_fix", "true_answer": "B", "predicted_answer": "A"},
            {"task_id": "clean_keep", "true_answer": "C", "predicted_answer": "C"},
            {"task_id": "noisy_harm", "true_answer": "D", "predicted_answer": "D"},
        ]
        method = [
            {
                "task_id": "clean_fix",
                "true_answer": "B",
                "predicted_answer": "B",
                "generated_graph": {"roles": ["Math Solver", "PromptNode:Verifier"]},
            },
            {"task_id": "clean_keep", "true_answer": "C", "predicted_answer": "C"},
            {"task_id": "noisy_harm", "true_answer": "D", "predicted_answer": "A"},
        ]
        audit = {
            "clean_fix": {"clean_label": "clean"},
            "clean_keep": {"clean_label": "clean"},
            "noisy_harm": {"clean_label": "noisy"},
        }

        summary = summarize_method(
            "Synthetic PN",
            method,
            baseline,
            audit,
            cost=0.6,
            prompt_tokens=30,
            completion_tokens=15,
        )

        self.assertEqual(summary["overall"], "2/3")
        self.assertEqual(summary["clean"], "2/2")
        self.assertEqual(summary["noisy_or_ambiguous"], "0/1")
        self.assertEqual(summary["fix_harm"], "1/1")
        self.assertEqual(summary["clean_fix_harm"], "1/0")
        self.assertEqual(summary["noisy_fix_harm"], "0/1")
        self.assertEqual(summary["switches"], 2)
        self.assertEqual(summary["promptnode_graph_hits"], "1/3")
        self.assertAlmostEqual(summary["cost_per_correct"], 0.3)

    def test_full_system_cost_uses_baseline_plus_four_views(self):
        from experiment.aqua.tail34_sci_evidence_report import build_full_system_cost

        summaries = {
            "ARG baseline": {"cost": 0.9, "prompt_tokens": 10, "completion_tokens": 5},
            "PN router": {"cost": 1.0, "prompt_tokens": 11, "completion_tokens": 6},
            "PN candidate": {"cost": 1.1, "prompt_tokens": 12, "completion_tokens": 7},
            "PN conservative": {"cost": 1.2, "prompt_tokens": 13, "completion_tokens": 8},
            "PN calibrated": {"cost": 1.3, "prompt_tokens": 14, "completion_tokens": 9},
        }

        full = build_full_system_cost(summaries)

        self.assertAlmostEqual(full["cost"], 5.5)
        self.assertEqual(full["prompt_tokens"], 60)
        self.assertEqual(full["completion_tokens"], 35)
        self.assertEqual(full["execution_scope"], "baseline + router + candidate + conservative + calibrated")

    def test_real_tail34_objective_boundary(self):
        from experiment.aqua.tail34_sci_evidence_report import build_tail34_report_payload

        payload = build_tail34_report_payload("experiment/aqua")
        objective = payload["method_summaries"]["Objective-guided selector"]

        self.assertEqual(objective["overall"], "31/34")
        self.assertEqual(objective["fix_harm"], "3/0")
        self.assertEqual(objective["clean"], "28/28")
        self.assertEqual(objective["clean_fix_harm"], "1/0")
        self.assertEqual(objective["promptnode_graph_hits"], "0/34")
        self.assertEqual(objective["switch_task_ids"], ["task_114", "task_59", "task_108", "task_250"])
        self.assertAlmostEqual(objective["cost"], 5.050805, places=6)
        self.assertEqual(payload["evidence_boundary"]["update2_compliance"], "partial")


if __name__ == "__main__":
    unittest.main()
