import unittest
import subprocess
import sys


class ContractAblationAnalysisTests(unittest.TestCase):
    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/contract_ablation_analysis.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_summarize_variant_records_splits_clean_noisy_and_switch_sources(self):
        from experiment.aqua.contract_ablation_analysis import summarize_variant_records

        records = [
            {
                "task_id": "clean_fix",
                "true_answer": "B",
                "baseline_prediction": "A",
                "predicted_answer": "B",
                "selected_source": "multi_contract_union",
            },
            {
                "task_id": "noisy_harm",
                "true_answer": "C",
                "baseline_prediction": "C",
                "predicted_answer": "A",
                "selected_source": "ensemble_invalid",
            },
            {
                "task_id": "clean_keep",
                "true_answer": "D",
                "baseline_prediction": "D",
                "predicted_answer": "D",
                "selected_source": "baseline",
            },
        ]
        audit_labels = {
            "clean_fix": "clean",
            "noisy_harm": "noisy",
            "clean_keep": "clean",
        }

        summary = summarize_variant_records("synthetic", records, audit_labels)

        self.assertEqual(summary["variant"], "synthetic")
        self.assertEqual(summary["overall"], "2/3")
        self.assertEqual(summary["clean"], "2/2")
        self.assertEqual(summary["noisy_or_ambiguous"], "0/1")
        self.assertEqual(summary["fix_harm"], "1/1")
        self.assertEqual(summary["clean_fix_harm"], "1/0")
        self.assertEqual(summary["noisy_fix_harm"], "0/1")
        self.assertEqual(summary["switches"], 2)
        self.assertEqual(summary["switch_sources"], {"ensemble_invalid": 1, "multi_contract_union": 1})

    def test_format_markdown_table_uses_paper_columns(self):
        from experiment.aqua.contract_ablation_analysis import format_markdown_table

        rows = [
            {
                "variant": "ARG baseline",
                "overall": "165/200",
                "clean": "152/167",
                "noisy_or_ambiguous": "13/33",
                "delta_vs_baseline": 0,
                "fix_harm": "0/0",
                "clean_fix_harm": "0/0",
                "switches": 0,
                "notes": "reference",
            }
        ]

        table = format_markdown_table(rows)

        self.assertIn("| Variant | Overall | Clean | Noisy/Ambiguous | Delta vs ARG | Fix/Harm | Clean Fix/Harm | Switches | Notes |", table)
        self.assertIn("| ARG baseline | `165/200` | `152/167` | `13/33` | `+0` | `0/0` | `0/0` | `0` | reference |", table)


if __name__ == "__main__":
    unittest.main()
