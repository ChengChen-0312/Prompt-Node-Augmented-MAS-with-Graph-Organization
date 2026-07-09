import unittest


class TestR418LifecycleTraceInstrumentationPreflight(unittest.TestCase):
    def test_preflight_defines_lifecycle_schema_and_authorizes_replay(self):
        from experiment.mmlu.r418_lifecycle_trace_instrumentation_preflight import build_lifecycle_preflight

        summary = build_lifecycle_preflight()

        self.assertEqual(summary["run_id"], "R418")
        self.assertIn("update", summary["lifecycle_actions"])
        self.assertIn("compress", summary["lifecycle_actions"])
        self.assertIn("prune", summary["lifecycle_actions"])
        self.assertIn("merge", summary["lifecycle_actions"])
        self.assertIn("upgrade", summary["lifecycle_actions"])
        self.assertIn("PromptNodeWrite", summary["event_schema"]["event_types"])
        self.assertIn("PromptEdgeForward", summary["event_schema"]["event_types"])
        self.assertIn("PromptNodePrune", summary["event_schema"]["event_types"])
        self.assertTrue(summary["trace_replay_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R419_lifecycle_trace_replay")


if __name__ == "__main__":
    unittest.main()
