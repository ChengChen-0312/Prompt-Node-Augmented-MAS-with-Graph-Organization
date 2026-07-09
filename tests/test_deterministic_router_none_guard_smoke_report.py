import json
import os
import tempfile
import unittest


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


class DeterministicRouterNoneGuardSmokeReportTests(unittest.TestCase):
    def test_report_tracks_abstention_integrity_separately_from_clean_recovery(self):
        from experiment.aqua.deterministic_router_none_guard_smoke_report import (
            build_deterministic_router_none_guard_smoke_summary,
            build_evaluate_command,
            write_switch_task_split,
        )

        payload = write_switch_task_split()
        self.assertEqual(payload["test_indices"], [108, 250])
        command = build_evaluate_command()
        self.assertIn("--decision_method DeterministicRouterContractFinalRefer", command)
        self.assertIn("--forced_template_candidate_rank 5", command)

        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = os.path.join(tmpdir, "baseline.jsonl")
            forced_path = os.path.join(tmpdir, "forced.jsonl")
            forced_summary_path = os.path.join(tmpdir, "forced_summary.jsonl")
            _write_jsonl(
                baseline_path,
                [
                    {"task_id": "task_8", "predicted_answer": "E", "true_answer": "E"},
                    {"task_id": "task_108", "predicted_answer": "B", "true_answer": "D"},
                    {"task_id": "task_188", "predicted_answer": "D", "true_answer": "D"},
                    {"task_id": "task_250", "predicted_answer": "A", "true_answer": "E"},
                ],
            )
            _write_jsonl(
                forced_path,
                [
                    {
                        "task_id": "task_108",
                        "predicted_answer": "D",
                        "true_answer": "D",
                        "generated_graph": {"roles": ["PN_Memory", "PN_Verifier", "PN_Router"]},
                        "agent_outputs": [
                            {
                                "role": "PN_Router",
                                "outputs": [
                                    "SUPPORTED_OPTION: D\nBINDING_STATUS: EXACT_MATCH\nFINAL_EVIDENCE_SUMMARY: exact"
                                ],
                            }
                        ],
                    },
                    {
                        "task_id": "task_250",
                        "predicted_answer": "None.",
                        "true_answer": "E",
                        "generated_graph": {"roles": ["PN_Memory", "PN_Verifier", "PN_Router"]},
                        "agent_outputs": [
                            {
                                "role": "PN_Router",
                                "outputs": [
                                    "SUPPORTED_OPTION: NONE\nBINDING_STATUS: NO_EXACT_OPTION\nFINAL_EVIDENCE_SUMMARY: absent"
                                ],
                            }
                        ],
                    },
                ],
            )
            _write_jsonl(forced_summary_path, [{"cost": 0.031, "prompt_tokens": 10, "completion_tokens": 5}])

            summary = build_deterministic_router_none_guard_smoke_summary(
                baseline_jsonl=baseline_path,
                forced_jsonl=forced_path,
                forced_summary_jsonl=forced_summary_path,
            )

        self.assertEqual(summary["rule"], "r132_deterministic_router_none_guard_smoke")
        self.assertEqual(summary["decision_method"], "DeterministicRouterContractFinalRefer")
        self.assertEqual(summary["baseline_accuracy"], "2/4")
        self.assertEqual(summary["selected_accuracy"], "3/4")
        self.assertEqual(summary["clean_fix_harm"], "0/0")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        self.assertEqual(summary["router_none_abstained"], "1/1")
        self.assertEqual(summary["forced_option_after_router_none_prevented"], "1/1")
        self.assertTrue(summary["integrity_gate_passed"])
        self.assertFalse(summary["smoke_gate_passed"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertTrue(summary["exact_option_repair_required"])

    def test_report_treats_composite_no_exact_status_as_router_none(self):
        from experiment.aqua.deterministic_router_none_guard_smoke_report import (
            build_deterministic_router_none_guard_smoke_summary,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = os.path.join(tmpdir, "baseline.jsonl")
            forced_path = os.path.join(tmpdir, "forced.jsonl")
            forced_summary_path = os.path.join(tmpdir, "forced_summary.jsonl")
            _write_jsonl(
                baseline_path,
                [
                    {"task_id": "task_8", "predicted_answer": "E", "true_answer": "E"},
                    {"task_id": "task_108", "predicted_answer": "B", "true_answer": "D"},
                    {"task_id": "task_188", "predicted_answer": "D", "true_answer": "D"},
                    {"task_id": "task_250", "predicted_answer": "A", "true_answer": "E"},
                ],
            )
            _write_jsonl(
                forced_path,
                [
                    {
                        "task_id": "task_108",
                        "predicted_answer": "D",
                        "true_answer": "D",
                        "generated_graph": {"roles": ["PN_Memory", "PN_Verifier", "PN_Router"]},
                        "agent_outputs": [
                            {
                                "role": "PN_Router",
                                "outputs": [
                                    "SUPPORTED_OPTION: D\nBINDING_STATUS: EXACT_MATCH\nFINAL_EVIDENCE_SUMMARY: exact"
                                ],
                            }
                        ],
                    },
                    {
                        "task_id": "task_250",
                        "predicted_answer": "None.",
                        "true_answer": "E",
                        "generated_graph": {"roles": ["PN_Memory", "PN_Verifier", "PN_Router"]},
                        "agent_outputs": [
                            {
                                "role": "PN_Router",
                                "outputs": [
                                    "SUPPORTED_OPTION: NONE\nBINDING_STATUS: NO_EXACT_OPTION/CONFLICT\nFINAL_EVIDENCE_SUMMARY: absent"
                                ],
                            }
                        ],
                    },
                ],
            )
            _write_jsonl(forced_summary_path, [{"cost": 0.031, "prompt_tokens": 10, "completion_tokens": 5}])

            summary = build_deterministic_router_none_guard_smoke_summary(
                baseline_jsonl=baseline_path,
                forced_jsonl=forced_path,
                forced_summary_jsonl=forced_summary_path,
            )

        self.assertEqual(summary["router_none_abstained"], "1/1")
        self.assertTrue(summary["integrity_gate_passed"])


if __name__ == "__main__":
    unittest.main()
