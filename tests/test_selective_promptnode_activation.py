import subprocess
import sys
import unittest


def _router_record(task_id="task_fix", prediction="D", router_option="D", status="EXACT_MATCH"):
    return {
        "task_id": task_id,
        "true_answer": "D",
        "predicted_answer": prediction,
        "question": "q",
        "agent_outputs": [
            {"node": 0, "role": "Math Solver", "outputs": ["The answer is D"]},
            {
                "node": 1,
                "role": "PN_Router",
                "outputs": [
                    f"SUPPORTED_OPTION: {router_option}\n"
                    f"BINDING_STATUS: {status}\n"
                    "FINAL_EVIDENCE_SUMMARY: verified option binding"
                ],
            },
        ],
    }


class SelectivePromptNodeActivationTests(unittest.TestCase):
    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/selective_promptnode_activation.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_extract_direct_votes_ignores_prompt_nodes(self):
        from experiment.aqua.selective_promptnode_activation import extract_direct_votes

        record = {
            "agent_outputs": [
                {"node": 0, "role": "Math Solver", "outputs": ["The answer is B"]},
                {"node": 1, "role": "Inspector", "outputs": ["The answer is D"]},
                {"node": 2, "role": "PN_Router", "outputs": ["SUPPORTED_OPTION: A"]},
                {"node": 3, "role": "PN_Verifier", "outputs": ["The answer is C"]},
            ]
        }

        self.assertEqual(extract_direct_votes(record), ["B", "D"])

    def test_gate_activates_on_direct_conflict_and_strong_router_option(self):
        from experiment.aqua.selective_promptnode_activation import should_activate_promptnode

        base_record = {
            "task_id": "task_fix",
            "true_answer": "D",
            "predicted_answer": "B",
            "agent_outputs": [
                {"node": 0, "role": "Math Solver", "outputs": ["The answer is B"]},
                {"node": 1, "role": "Inspector", "outputs": ["The answer is D"]},
            ],
        }

        activate, features = should_activate_promptnode(base_record, _router_record())

        self.assertTrue(activate)
        self.assertEqual(features["direct_vote_counts"], {"B": 1, "D": 1})
        self.assertEqual(features["router_option"], "D")
        self.assertNotIn("true_answer", features)
        self.assertNotIn("is_solved", features)
        self.assertNotIn("task_id", features)

    def test_gate_blocks_when_direct_vote_has_majority(self):
        from experiment.aqua.selective_promptnode_activation import should_activate_promptnode

        base_record = {
            "task_id": "task_majority",
            "predicted_answer": "B",
            "agent_outputs": [
                {"node": 0, "role": "Math Solver", "outputs": ["The answer is B"]},
                {"node": 1, "role": "Inspector", "outputs": ["The answer is B"]},
                {"node": 2, "role": "Programming Expert", "outputs": ["The answer is D"]},
            ],
        }

        activate, features = should_activate_promptnode(base_record, _router_record("task_majority"))

        self.assertFalse(activate)
        self.assertEqual(features["direct_max_count"], 2)
        self.assertEqual(features["block_reason"], "direct_majority")

    def test_gate_blocks_when_router_option_is_not_a_direct_vote(self):
        from experiment.aqua.selective_promptnode_activation import should_activate_promptnode

        base_record = {
            "task_id": "task_outside",
            "predicted_answer": "B",
            "agent_outputs": [
                {"node": 0, "role": "Math Solver", "outputs": ["The answer is B"]},
                {"node": 1, "role": "Inspector", "outputs": ["The answer is D"]},
            ],
        }

        activate, features = should_activate_promptnode(
            base_record,
            _router_record("task_outside", prediction="C", router_option="C"),
        )

        self.assertFalse(activate)
        self.assertEqual(features["block_reason"], "router_not_in_direct_votes")

    def test_build_records_selects_promptnode_only_when_gate_fires(self):
        from experiment.aqua.selective_promptnode_activation import (
            build_selective_records,
            summarize_selected_records,
        )

        base_records = {
            "task_fix": {
                "task_id": "task_fix",
                "true_answer": "D",
                "predicted_answer": "B",
                "question": "q1",
                "agent_outputs": [
                    {"node": 0, "role": "Math Solver", "outputs": ["The answer is B"]},
                    {"node": 1, "role": "Inspector", "outputs": ["The answer is D"]},
                ],
            },
            "task_keep": {
                "task_id": "task_keep",
                "true_answer": "A",
                "predicted_answer": "A",
                "question": "q2",
                "agent_outputs": [
                    {"node": 0, "role": "Math Solver", "outputs": ["The answer is A"]},
                    {"node": 1, "role": "Inspector", "outputs": ["The answer is A"]},
                ],
            },
        }
        pn_records = {
            "task_fix": _router_record("task_fix", prediction="D", router_option="D"),
            "task_keep": _router_record("task_keep", prediction="B", router_option="B"),
        }

        records = build_selective_records(base_records, pn_records)
        summary = summarize_selected_records(records)

        by_task = {record["task_id"]: record for record in records}
        self.assertEqual(by_task["task_fix"]["selected_source"], "promptnode")
        self.assertEqual(by_task["task_fix"]["predicted_answer"], "D")
        self.assertEqual(by_task["task_keep"]["selected_source"], "baseline")
        self.assertEqual(by_task["task_keep"]["predicted_answer"], "A")
        self.assertNotIn("true_answer", by_task["task_fix"]["gate_features"])
        self.assertEqual(summary["selected_promptnode_count"], 1)
        self.assertEqual(summary["fixes_vs_baseline"], 1)
        self.assertEqual(summary["harms_vs_baseline"], 0)


if __name__ == "__main__":
    unittest.main()
