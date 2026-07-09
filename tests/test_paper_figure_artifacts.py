import unittest


class PaperFigureArtifactsTests(unittest.TestCase):
    def test_build_main_result_rows_separates_mechanism_full_and_objective_candidates(self):
        from experiment.aqua.paper_figure_artifacts import build_main_result_rows

        ablation_summary = {
            "rows": [
                {
                    "variant": "ARG baseline",
                    "overall": "165/200",
                    "clean": "152/167",
                    "noisy_or_ambiguous": "13/33",
                    "delta_vs_baseline": 0,
                    "fix_harm": "0/0",
                    "clean_fix_harm": "0/0",
                    "switches": 0,
                },
                {
                    "variant": "R035 multi-contract only",
                    "overall": "168/200",
                    "clean": "155/167",
                    "noisy_or_ambiguous": "13/33",
                    "delta_vs_baseline": 3,
                    "fix_harm": "3/0",
                    "clean_fix_harm": "3/0",
                    "switches": 3,
                },
                {
                    "variant": "R035 multi-contract + invalid fallback",
                    "overall": "174/200",
                    "clean": "156/167",
                    "noisy_or_ambiguous": "18/33",
                    "delta_vs_baseline": 9,
                    "fix_harm": "9/0",
                    "clean_fix_harm": "4/0",
                    "switches": 14,
                },
            ]
        }
        ungated = {
            "posthoc_audit_summary": {
                "overall": "172/200",
                "clean": "155/167",
                "noisy_or_ambiguous": "17/33",
                "delta_vs_baseline": 7,
                "fix_harm": "9/2",
                "clean_fix_harm": "4/1",
                "switches": 16,
            }
        }
        margin = {
            "posthoc_audit_summary": {
                "overall": "170/200",
                "clean": "154/167",
                "noisy_or_ambiguous": "16/33",
                "delta_vs_baseline": 5,
                "fix_harm": "5/0",
                "clean_fix_harm": "2/0",
                "switches": 7,
            },
            "min_score_margin": 3,
        }

        rows = build_main_result_rows(ablation_summary, ungated, margin)
        by_key = {row["key"]: row for row in rows}

        self.assertEqual(by_key["r035_pure"]["claim_role"], "main mechanism candidate")
        self.assertEqual(by_key["r035_full"]["claim_role"], "full system; fallback separated")
        self.assertEqual(by_key["r039"]["claim_role"], "rejected as main due clean harm")
        self.assertEqual(by_key["r040"]["display"], "R040 margin-gated objective")
        self.assertEqual(by_key["r040"]["clean_fix_harm"], "2/0")

    def test_latex_table_marks_exploratory_scope_and_noisy_split(self):
        from experiment.aqua.paper_figure_artifacts import render_main_results_latex_table

        latex = render_main_results_latex_table(
            [
                {
                    "display": "ARG baseline",
                    "overall": "165/200",
                    "clean": "152/167",
                    "noisy_or_ambiguous": "13/33",
                    "delta_vs_baseline": 0,
                    "fix_harm": "0/0",
                    "clean_fix_harm": "0/0",
                    "switches": 0,
                    "claim_role": "primary baseline",
                },
                {
                    "display": "R035 multi-contract only",
                    "overall": "168/200",
                    "clean": "155/167",
                    "noisy_or_ambiguous": "13/33",
                    "delta_vs_baseline": 3,
                    "fix_harm": "3/0",
                    "clean_fix_harm": "3/0",
                    "switches": 3,
                    "claim_role": "main mechanism candidate",
                },
            ]
        )

        self.assertIn("AQuA first200 exploratory", latex)
        self.assertIn("Noisy/Amb.", latex)
        self.assertIn("main mechanism candidate", latex)
        self.assertIn("\\label{tab:aqua_first200_main_results}", latex)

    def test_contract_coverage_rows_use_rates_without_gold_inputs(self):
        from experiment.aqua.paper_figure_artifacts import build_contract_coverage_rows

        rows = build_contract_coverage_rows(
            {
                "summary": {
                    "total_tasks": 200,
                    "positive_top_score_tasks": 196,
                    "top_score_ties": 99,
                    "r035_pure_switch_tasks": 3,
                    "r035_switch_top_option_agreement": 3,
                    "r035_switch_unique_top_option_agreement": 1,
                },
                "objective_inputs_exclude": ["gold labels", "audit labels"],
            }
        )

        self.assertEqual(rows[0]["label"], "Positive top-score")
        self.assertAlmostEqual(rows[0]["rate"], 98.0)
        self.assertEqual(rows[2]["value"], "3/3")
        self.assertIn("gold labels", rows[0]["note"])

    def test_main_results_svg_expands_axis_and_has_no_inline_title(self):
        from experiment.aqua.paper_figure_artifacts import render_main_results_svg

        svg = render_main_results_svg(
            [
                {
                    "display": "High clean method",
                    "overall_rate": 87.0,
                    "clean_rate": 93.4,
                }
            ]
        )

        self.assertIn(">95<", svg)
        self.assertNotIn("AQuA first200 exploratory split", svg)


if __name__ == "__main__":
    unittest.main()
