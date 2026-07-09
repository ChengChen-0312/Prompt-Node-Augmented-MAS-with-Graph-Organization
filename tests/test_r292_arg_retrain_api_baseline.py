import unittest


class TestR292ArgRetrainAPIBaseline(unittest.TestCase):
    def test_summarize_arg_records_reports_accuracy(self):
        from experiment.mmlu.r292_arg_retrain_api_baseline import summarize_records

        rows = [
            {"is_correct": True, "api_error": "", "num_nodes": 5, "num_edges": 4},
            {"is_correct": False, "api_error": "", "num_nodes": 4, "num_edges": 3},
        ]

        summary = summarize_records(rows, api_cost=0.5, prompt_tokens=1000, completion_tokens=100)

        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["correct"], 1)
        self.assertEqual(summary["accuracy"], 0.5)
        self.assertEqual(summary["mean_nodes"], 4.5)
        self.assertEqual(summary["mean_edges"], 3.5)


if __name__ == "__main__":
    unittest.main()
