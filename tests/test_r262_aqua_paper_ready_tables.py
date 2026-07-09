import unittest

from experiment.aqua.r262_paper_ready_result_tables import (
    assess_cost_boundary,
    build_result_table,
    parse_accuracy,
)


class TestR262AquaPaperReadyTables(unittest.TestCase):
    def test_parse_accuracy(self):
        self.assertEqual(parse_accuracy("31/34"), (31, 34))

    def test_table_computes_delta_and_cost_ratio(self):
        rows = [
            {"run_id": "ARG", "accuracy": "28/34", "cost": 0.934},
            {"run_id": "R065", "accuracy": "31/34", "cost": 5.05},
        ]
        table = build_result_table(rows)
        r065 = [row for row in table if row["run_id"] == "R065"][0]

        self.assertEqual(r065["delta_vs_arg_correct"], 3)
        self.assertGreater(r065["cost_ratio_vs_arg"], 5.0)

    def test_cost_boundary_flags_expensive_teacher(self):
        summary = assess_cost_boundary(
            [
                {"run_id": "R065", "correct": 31, "total": 34, "cost": 5.05, "fresh_integrated": False},
                {"run_id": "R072", "correct": 29, "total": 34, "cost": 2.82, "fresh_integrated": True},
            ]
        )

        self.assertEqual(summary["best_accuracy_run"], "R065")
        self.assertEqual(summary["best_fresh_cost_run"], "R072")


if __name__ == "__main__":
    unittest.main()
