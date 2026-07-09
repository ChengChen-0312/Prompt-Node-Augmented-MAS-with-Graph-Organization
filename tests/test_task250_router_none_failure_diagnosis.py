import unittest


class Task250RouterNoneFailureDiagnosisTests(unittest.TestCase):
    def test_diagnosis_demotes_rank5_history_to_router_none_boundary(self):
        from experiment.aqua.task250_router_none_failure_diagnosis import (
            build_task250_router_none_failure_diagnosis,
        )

        rows, summary = build_task250_router_none_failure_diagnosis()

        self.assertEqual(summary["rule"], "r129_task250_router_none_failure_diagnosis")
        self.assertTrue(summary["diagnosis_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertEqual(summary["compared_runs"], ["R128", "R100", "R106"])
        self.assertEqual(summary["r128_prediction"], "A")
        self.assertEqual(summary["r100_prediction"], "E")
        self.assertEqual(summary["r106_prediction"], "E")
        self.assertEqual(summary["router_none_no_exact_runs"], "3/3")
        self.assertEqual(summary["final_option_after_router_none_runs"], "3/3")
        self.assertFalse(summary["router_contract_supported_clean_fix"])
        self.assertTrue(summary["historical_success_is_nearest_choice_coercion"])
        self.assertTrue(summary["r128_final_layer_overrode_router_none"])
        self.assertFalse(summary["rank_selection_sufficient"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_required_protocol"],
            "deterministic_none_guard_or_exact_option_repair_before_api",
        )
        self.assertEqual(
            summary["claim_boundary"],
            "diagnosis only; no API run, no new accuracy result, and task250 rank5 historical success is not a clean router-supported fix",
        )

        by_run = {row["run_name"]: row for row in rows}
        for run_name in ["R128", "R100", "R106"]:
            self.assertEqual(by_run[run_name]["router_supported_option"], "NONE")
            self.assertEqual(by_run[run_name]["router_binding_status"], "NO_EXACT_OPTION")
            self.assertTrue(by_run[run_name]["final_layer_selected_option_after_router_none"])
            self.assertEqual(by_run[run_name]["selected_rank"], 5)

        self.assertFalse(by_run["R128"]["is_solved"])
        self.assertTrue(by_run["R100"]["is_solved"])
        self.assertTrue(by_run["R106"]["is_solved"])


if __name__ == "__main__":
    unittest.main()
