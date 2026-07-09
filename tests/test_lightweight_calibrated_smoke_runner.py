import unittest


class LightweightCalibratedSmokeRunnerTests(unittest.TestCase):
    def _baseline_record(self):
        return {
            "task_id": "task_250",
            "question": "dummy",
            "true_answer": "E",
            "predicted_answer": "A",
            "is_solved": False,
            "agent_outputs": [
                {"node": 0, "role": "MathSolver", "outputs": ["The answer is A"]},
                {"node": 1, "role": "MathSolver", "outputs": ["The answer is B"]},
            ],
            "generated_graph": {"roles": ["MathSolver", "MathSolver"], "edges": [[0, 1]]},
        }

    def _calibrated_record(self):
        return {
            "task_id": "task_250",
            "question": "dummy",
            "true_answer": "E",
            "predicted_answer": "E",
            "is_solved": True,
            "agent_outputs": [
                {
                    "node": 0,
                    "role": "PN_Router",
                    "outputs": [
                        "SUPPORTED_OPTION: E\n"
                        "BINDING_STATUS: EXACT_MATCH\n"
                        "FINAL_EVIDENCE_SUMMARY: calibrated evidence"
                    ],
                },
                {"node": 1, "role": "MathSolver", "outputs": ["The answer is E"]},
            ],
            "generated_graph": {
                "roles": ["PN_Router", "MathSolver"],
                "edges": [[0, 1]],
            },
        }

    def test_builds_non_leaky_switch_record_from_single_calibrated_view(self):
        from experiment.aqua.lightweight_calibrated_smoke_runner import (
            FORBIDDEN_POLICY_INPUT_FIELDS,
            build_calibrated_probe_record,
        )

        record = build_calibrated_probe_record(
            self._baseline_record(),
            self._calibrated_record(),
        )

        self.assertEqual(record["task_id"], "task_250")
        self.assertEqual(record["probe_protocol"], "calibrated_single_view_probe")
        self.assertEqual(record["promptnode_view_count"], 1)
        self.assertEqual(record["view_predictions"], {"calibrated": "E"})
        self.assertEqual(record["selected_source"], "calibrated_probe")
        self.assertEqual(record["selected_method"], "calibrated")
        self.assertEqual(record["proxy_action"], "switch_to_objective")
        self.assertEqual(record["predicted_answer"], "E")
        self.assertTrue(record["is_solved"])
        self.assertTrue(record["fix"])
        self.assertFalse(record["harm"])
        self.assertEqual(record["top_score"], record["policy_input"]["objective_top_score"])
        self.assertFalse(FORBIDDEN_POLICY_INPUT_FIELDS.intersection(record["policy_input"]))

    def test_summary_preserves_four_task_smoke_boundary(self):
        from experiment.aqua.lightweight_calibrated_smoke_runner import (
            REGRESSION_TASK_IDS,
            build_calibrated_smoke_summary,
        )

        rows = [
            {
                "task_id": "task_8",
                "is_solved": True,
                "baseline_is_solved": True,
                "calibrated_is_solved": False,
                "selected_source": "baseline",
                "proxy_action": "fallback_to_arg",
                "fix": False,
                "harm": False,
                "calibrated_harm": True,
                "promptnode_view_count": 1,
                "policy_input": {"objective_top_score": 2},
            },
            {
                "task_id": "task_250",
                "is_solved": True,
                "baseline_is_solved": False,
                "calibrated_is_solved": True,
                "selected_source": "calibrated_probe",
                "proxy_action": "switch_to_objective",
                "fix": True,
                "harm": False,
                "calibrated_harm": False,
                "promptnode_view_count": 1,
                "policy_input": {"objective_top_score": 7},
            },
        ]

        summary = build_calibrated_smoke_summary(rows, cost=0.12, prompt_tokens=10, completion_tokens=5)

        self.assertEqual(summary["rule"], "r119_lightweight_calibrated_smoke_runner")
        self.assertEqual(summary["probe_protocol"], "calibrated_single_view_probe")
        self.assertEqual(summary["regression_tasks"], REGRESSION_TASK_IDS)
        self.assertEqual(summary["total_tasks"], 2)
        self.assertEqual(summary["selected_accuracy"], "2/2")
        self.assertEqual(summary["baseline_accuracy"], "1/2")
        self.assertEqual(summary["switch_tasks"], ["task_250"])
        self.assertEqual(summary["suppressed_calibrated_harm_tasks"], ["task_8"])
        self.assertEqual(summary["fix_harm"], "1/0")
        self.assertEqual(summary["max_promptnode_views_per_task"], 1)
        self.assertFalse(summary["broad_heldout_claim_ready"])
        self.assertEqual(summary["cost"], 0.12)
        self.assertEqual(
            summary["claim_boundary"],
            "four-task prospective calibrated-probe smoke only; not broad held-out accuracy or SCI-ready claim",
        )

    def test_refreshes_cached_gpt_chat_environment_after_loading_env(self):
        import os

        import mas_framework.llm.gpt_chat as gpt_chat
        from experiment.aqua.lightweight_calibrated_smoke_runner import refresh_gpt_chat_env

        old_api_key = os.environ.get("API_KEY")
        old_openai_key = os.environ.get("OPENAI_API_KEY")
        old_base_url = os.environ.get("BASE_URL")
        old_cached_key = gpt_chat.MINE_API_KEY
        old_cached_base = gpt_chat.MINE_BASE_URL
        try:
            os.environ["API_KEY"] = "test-key"
            os.environ["OPENAI_API_KEY"] = "test-openai-key"
            os.environ["BASE_URL"] = "https://example.test/v1"
            gpt_chat.MINE_API_KEY = ""
            gpt_chat.MINE_BASE_URL = None

            refresh_gpt_chat_env()

            self.assertEqual(gpt_chat.MINE_API_KEY, "test-key")
            self.assertEqual(gpt_chat.MINE_BASE_URL, "https://example.test/v1")
        finally:
            if old_api_key is None:
                os.environ.pop("API_KEY", None)
            else:
                os.environ["API_KEY"] = old_api_key
            if old_openai_key is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = old_openai_key
            if old_base_url is None:
                os.environ.pop("BASE_URL", None)
            else:
                os.environ["BASE_URL"] = old_base_url
            gpt_chat.MINE_API_KEY = old_cached_key
            gpt_chat.MINE_BASE_URL = old_cached_base


if __name__ == "__main__":
    unittest.main()
