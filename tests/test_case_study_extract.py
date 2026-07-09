import unittest


class PromptNodeCaseStudyExtractTests(unittest.TestCase):
    def test_build_case_studies_keeps_only_clean_multi_contract_fixes(self):
        from experiment.aqua.case_study_extract import build_case_studies

        records = [
            {
                "task_id": "task_fix",
                "question": "Synthetic question? Choices: A)bad B)good C)other",
                "true_answer": "B",
                "baseline_prediction": "A",
                "ensemble_prediction": "B",
                "predicted_answer": "B",
                "selected_source": "multi_contract_union",
                "selector_features": {
                    "method_features": {
                        "router": {
                            "router_option": "B",
                            "router_binding_status": "EXACT_MATCH",
                            "direct_majority": "B",
                            "direct_majority_count": 2,
                            "router_matches_direct_majority": True,
                        },
                        "candidate": {
                            "router_option": "C",
                            "router_binding_status": "EXACT_MATCH",
                            "direct_majority": "A",
                            "direct_majority_count": 1,
                            "router_matches_direct_majority": False,
                        },
                    },
                    "direct_consensus_counts": {"B": 2},
                    "strong_option_counts": {"B": 2, "C": 1},
                    "method_keys": ["router", "candidate"],
                },
                "slice_prefix": "synthetic",
            },
            {
                "task_id": "task_noisy",
                "true_answer": "C",
                "baseline_prediction": "A",
                "predicted_answer": "C",
                "selected_source": "multi_contract_union",
                "selector_features": {},
            },
            {
                "task_id": "task_fallback",
                "true_answer": "D",
                "baseline_prediction": None,
                "predicted_answer": "D",
                "selected_source": "ensemble_invalid",
                "selector_features": {},
            },
        ]

        studies = build_case_studies(records, {"task_fix": "clean", "task_noisy": "noisy"})

        self.assertEqual(len(studies), 1)
        self.assertEqual(studies[0]["task_id"], "task_fix")
        self.assertEqual(studies[0]["case_type"], "clean_fix")
        self.assertEqual(studies[0]["rule_evidence"], "direct-consensus B=2; strong B=2, C=1")
        self.assertIn("router:B/EXACT_MATCH/direct=2/match=yes", studies[0]["method_contracts"])
        self.assertIn("candidate:C/EXACT_MATCH/direct=1/match=no", studies[0]["method_contracts"])

    def test_render_markdown_states_claim_boundary_and_table(self):
        from experiment.aqua.case_study_extract import render_markdown

        markdown = render_markdown(
            [
                {
                    "task_id": "task_fix",
                    "slice_prefix": "aqua_100",
                    "audit_label": "clean",
                    "true_answer": "B",
                    "baseline_prediction": "A",
                    "ensemble_prediction": "B",
                    "selected_prediction": "B",
                    "selected_source": "multi_contract_union",
                    "rule_evidence": "direct-consensus B=2",
                    "method_contracts": "router:B/EXACT_MATCH/direct=2/match=yes",
                    "question_short": "Synthetic question?",
                }
            ],
            title="Synthetic Case Studies",
        )

        self.assertIn("exploratory first200", markdown)
        self.assertIn("| Task | Slice | Audit | Gold | ARG | Ensemble | Selected | Evidence |", markdown)
        self.assertIn("task_fix", markdown)
        self.assertIn("direct-consensus B=2", markdown)

    def test_real_r035_first200_extracts_expected_clean_switches(self):
        from experiment.aqua.case_study_extract import (
            build_case_studies,
            load_audit_labels,
            load_jsonl_records,
        )

        records = load_jsonl_records(
            "experiment/aqua/aqua_first200_multi_contract_union_only_selector_results.jsonl"
        )
        audit_labels = load_audit_labels(
            [
                "experiment/aqua/aqua_100_option_binding_audit.jsonl",
                "experiment/aqua/aqua_next100_option_binding_audit.jsonl",
            ]
        )

        studies = build_case_studies(records, audit_labels)
        task_ids = {study["task_id"] for study in studies}

        self.assertEqual(task_ids, {"task_122", "task_197", "task_67"})
        self.assertTrue(all(study["audit_label"] == "clean" for study in studies))
        self.assertTrue(all(study["selected_source"] == "multi_contract_union" for study in studies))


if __name__ == "__main__":
    unittest.main()
