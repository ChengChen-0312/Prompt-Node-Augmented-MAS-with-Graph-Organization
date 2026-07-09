import unittest


class LightweightObjectiveProbeReplayTests(unittest.TestCase):
    def test_single_calibrated_view_matches_frozen_objective_safety_targets(self):
        from experiment.aqua.lightweight_objective_probe_replay import (
            build_lightweight_objective_probe_replay_summary,
        )

        summary = build_lightweight_objective_probe_replay_summary()

        self.assertEqual(summary["rule"], "r118_lightweight_objective_probe_replay")
        self.assertTrue(summary["replay_only"])
        self.assertEqual(summary["candidate_subset_count"], 10)
        self.assertEqual(summary["one_view_success_count"], 1)
        self.assertEqual(summary["two_view_success_count"], 3)
        self.assertEqual(summary["best_min_view_subset"], ["calibrated"])
        self.assertEqual(summary["best_min_view_count"], 1)
        self.assertEqual(summary["best_min_view_target_agreement"], "34/34")
        self.assertEqual(summary["best_min_view_switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["best_min_view_false_switch_tasks"], [])
        self.assertEqual(summary["best_min_view_missed_switch_tasks"], [])
        self.assertEqual(summary["recommended_probe_protocol"], "calibrated_single_view_probe")
        self.assertFalse(summary["api_result_ready"])
        self.assertEqual(
            summary["claim_boundary"],
            "offline probe replay only; no new API, measured cost, or accuracy claim",
        )


if __name__ == "__main__":
    unittest.main()
