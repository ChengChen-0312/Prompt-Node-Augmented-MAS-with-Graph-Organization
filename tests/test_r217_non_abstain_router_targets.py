import unittest

from experiment.mmlu.r217_non_abstain_router_targets import (
    FORBIDDEN_MODEL_VISIBLE_FIELDS,
    build_router_target,
    scan_target_records,
)


class TestR217NonAbstainRouterTargets(unittest.TestCase):
    def _row(self, action="switch_to_objective"):
        return {
            "task_id": "task_1",
            "policy_input": {
                "baseline_prediction": "A",
                "objective_prediction": "C",
                "objective_prediction_differs_from_baseline": True,
                "objective_top_score": 3,
                "baseline_direct_majority": "A",
                "baseline_direct_majority_count": 1,
                "baseline_direct_valid_vote_count": 1,
                "baseline_direct_votes_split": False,
            },
            "target_action": action,
            "target_reason": "objective_top_score_ge3",
            "analysis": {"clean_label": "clean", "gold_binding_status": "exact"},
            "source_run": "unit",
        }

    def test_switch_to_objective_creates_non_abstain_router_target_without_leakage(self):
        target = build_router_target(self._row("switch_to_objective"), split_role="train")

        self.assertEqual(target["router_final_schema"]["schema_version"], "r217_non_abstain_router_v1")
        self.assertEqual(target["router_action"], "switch_to_objective")
        self.assertEqual(target["target_option_label"], "C")
        self.assertTrue(target["training_allowed"])
        self.assertFalse(target["frozen_eval_only"])
        self.assertEqual(target["model_visible_input"]["objective_prediction"], "C")
        self.assertTrue(
            set(FORBIDDEN_MODEL_VISIBLE_FIELDS).isdisjoint(target["model_visible_input"])
        )

    def test_fallback_to_arg_remains_abstain_none(self):
        target = build_router_target(self._row("fallback_to_arg"), split_role="train")

        self.assertEqual(target["router_action"], "abstain")
        self.assertEqual(target["target_option_label"], "NONE")

    def test_tail34_rows_are_frozen_eval_only(self):
        target = build_router_target(self._row("switch_to_objective"), split_role="frozen_eval")

        self.assertFalse(target["training_allowed"])
        self.assertTrue(target["frozen_eval_only"])
        self.assertEqual(target["router_action"], "switch_to_objective")

    def test_scan_target_records_flags_forbidden_model_visible_fields(self):
        clean = build_router_target(self._row("switch_to_objective"), split_role="train")
        bad = dict(clean)
        bad["model_visible_input"] = dict(clean["model_visible_input"])
        bad["model_visible_input"]["task_id"] = "task_1"

        summary = scan_target_records([clean, bad])

        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["leakage_violations"], 1)
        self.assertFalse(summary["leakage_pass"])


if __name__ == "__main__":
    unittest.main()
