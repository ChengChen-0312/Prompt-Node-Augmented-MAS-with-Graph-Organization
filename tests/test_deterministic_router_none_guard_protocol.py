import unittest


class DeterministicRouterNoneGuardProtocolTests(unittest.TestCase):
    def test_guard_prevents_forced_option_after_router_none(self):
        from experiment.aqua.deterministic_router_none_guard_protocol import (
            build_deterministic_router_none_guard_protocol,
        )

        rows, summary = build_deterministic_router_none_guard_protocol()

        self.assertEqual(summary["rule"], "r131_deterministic_router_none_guard_protocol")
        self.assertTrue(summary["implementation_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["decision_method_registered"])
        self.assertEqual(summary["decision_method"], "DeterministicRouterContractFinalRefer")
        self.assertEqual(summary["router_none_terminal_guard_predictions"], "3/3")
        self.assertEqual(summary["forced_option_after_router_none_prevented"], "3/3")
        self.assertEqual(summary["parser_prediction_for_abstain"], "None.")
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertTrue(summary["same_four_task_smoke_allowed_next"])
        self.assertEqual(
            summary["claim_boundary"],
            "implementation and offline guard protocol only; no API, cost, or accuracy result",
        )

        for row in rows:
            self.assertEqual(row["guard_raw_response"], "no valid option is supported")
            self.assertEqual(row["guard_prediction"], "None.")
            self.assertTrue(row["prevents_forced_option_after_router_none"])


if __name__ == "__main__":
    unittest.main()
