import os
import sys
import unittest
from unittest import mock


class AquaEvaluationValidityTests(unittest.TestCase):
    def test_gpt_evaluation_requires_api_key_before_running(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.evaluate_aqua import assert_llm_environment_ready

        with mock.patch.dict(os.environ, {"API_KEY": "", "OPENAI_API_KEY": ""}):
            with self.assertRaisesRegex(RuntimeError, "Missing API_KEY or OPENAI_API_KEY"):
                assert_llm_environment_ready("gpt-4o-2024-08-06")

    def test_mock_evaluation_does_not_require_api_key(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.evaluate_aqua import assert_llm_environment_ready

        with mock.patch.dict(os.environ, {"API_KEY": "", "OPENAI_API_KEY": ""}):
            assert_llm_environment_ready("mock")

    def test_all_retry_errors_with_zero_tokens_is_invalid_infrastructure_run(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.evaluate_aqua import assert_valid_evaluation_run

        records = [
            {
                "task_id": "task_1",
                "predicted_answer": None,
                "raw_response": None,
                "is_solved": False,
                "error": "RetryError[<Future state=finished raised RuntimeError>]",
            },
            {
                "task_id": "task_2",
                "predicted_answer": None,
                "raw_response": None,
                "is_solved": False,
                "error": "Missing API_KEY or OPENAI_API_KEY.",
            },
        ]

        with self.assertRaisesRegex(RuntimeError, "No successful LLM calls"):
            assert_valid_evaluation_run(
                records,
                total_tasks=2,
                prompt_tokens=0,
                completion_tokens=0,
            )

    def test_mixed_task_error_after_llm_usage_remains_valid_for_reporting(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.evaluate_aqua import assert_valid_evaluation_run

        records = [
            {
                "task_id": "task_1",
                "predicted_answer": "A",
                "raw_response": "The answer is A",
                "is_solved": True,
            },
            {
                "task_id": "task_2",
                "predicted_answer": None,
                "raw_response": None,
                "is_solved": False,
                "error": "Graph generation failed.",
            },
        ]

        assert_valid_evaluation_run(
            records,
            total_tasks=2,
            prompt_tokens=1200,
            completion_tokens=300,
        )


if __name__ == "__main__":
    unittest.main()
