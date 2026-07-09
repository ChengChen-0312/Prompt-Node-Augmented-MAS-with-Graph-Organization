import unittest


class AquaResultEnsembleTests(unittest.TestCase):
    def test_majority_vote_prefers_majority_option(self):
        from experiment.aqua.ensemble_results import majority_vote_prediction

        prediction = majority_vote_prediction(
            {"baseline": "A", "pn_a": "B", "pn_b": "B"},
            method_order=["baseline", "pn_a", "pn_b"],
            tie_breaker="baseline",
        )

        self.assertEqual(prediction, "B")

    def test_majority_vote_tie_prefers_tie_breaker(self):
        from experiment.aqua.ensemble_results import majority_vote_prediction

        prediction = majority_vote_prediction(
            {"baseline": "A", "pn_a": "B"},
            method_order=["baseline", "pn_a"],
            tie_breaker="baseline",
        )

        self.assertEqual(prediction, "A")

    def test_majority_vote_ignores_invalid_predictions(self):
        from experiment.aqua.ensemble_results import majority_vote_prediction

        prediction = majority_vote_prediction(
            {"baseline": "None.", "pn_a": "C", "pn_b": None},
            method_order=["baseline", "pn_a", "pn_b"],
            tie_breaker="baseline",
        )

        self.assertEqual(prediction, "C")

    def test_build_ensemble_records_preserves_method_predictions(self):
        from experiment.aqua.ensemble_results import build_ensemble_records

        result_sets = {
            "baseline": {
                "task_1": {"task_id": "task_1", "true_answer": "B", "predicted_answer": "A"},
            },
            "pn": {
                "task_1": {"task_id": "task_1", "true_answer": "B", "predicted_answer": "B"},
            },
        }

        records = build_ensemble_records(
            result_sets,
            method_order=["baseline", "pn"],
            tie_breaker="baseline",
        )

        self.assertEqual(records[0]["task_id"], "task_1")
        self.assertEqual(records[0]["predicted_answer"], "A")
        self.assertFalse(records[0]["is_solved"])
        self.assertEqual(records[0]["method_predictions"], {"baseline": "A", "pn": "B"})


if __name__ == "__main__":
    unittest.main()

