import unittest


class TestR330PaperTablesAndFiguresPlan(unittest.TestCase):
    def test_paper_table_figure_plan_covers_results_ablations_selector_and_cases(self):
        from experiment.mmlu.r330_paper_tables_and_figures_plan import build_paper_tables_and_figures_plan

        summary = build_paper_tables_and_figures_plan()
        table_ids = {table["id"] for table in summary["tables"]}
        figure_ids = {figure["id"] for figure in summary["figures"]}

        self.assertEqual(summary["run_id"], "R330")
        self.assertIn("main_results", table_ids)
        self.assertIn("ablation_controls", table_ids)
        self.assertIn("selector_training_gate", table_ids)
        self.assertIn("case_studies", table_ids)
        self.assertIn("promptnode_augmented_graph_workflow", figure_ids)
        self.assertIn("selector_training_pipeline", figure_ids)
        self.assertIn("method", summary["ready_to_draft_sections"])
        self.assertIn("experiments", summary["ready_to_draft_sections"])
        self.assertIn("prospective selector evaluation", summary["missing_before_sci_q2_submission"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R331_paper_outline_scaffold")


if __name__ == "__main__":
    unittest.main()
