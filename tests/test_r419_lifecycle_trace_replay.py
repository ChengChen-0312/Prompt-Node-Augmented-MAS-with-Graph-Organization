import unittest


class TestR419LifecycleTraceReplay(unittest.TestCase):
    def test_replay_generates_lifecycle_events_from_r413_results(self):
        from experiment.mmlu.r419_lifecycle_trace_replay import build_lifecycle_trace

        events, summary = build_lifecycle_trace()

        self.assertEqual(summary["run_id"], "R419")
        self.assertEqual(summary["source_records"], 24)
        self.assertGreater(len(events), 0)
        event_types = {event["event_type"] for event in events}
        self.assertIn("PromptNodeWrite", event_types)
        self.assertIn("PromptNodeCompress", event_types)
        self.assertIn("PromptNodeMerge", event_types)
        self.assertIn("PromptEdgeForward", event_types)
        self.assertIn("PromptNodePrune", event_types)
        self.assertIn("PromptNodeUpgrade", event_types)

        self.assertEqual(summary["forwarded_tasks"], 11)
        self.assertEqual(summary["pruned_tasks"], 13)
        self.assertIn("MMLU-nonstem-moral_disputes_test-14", summary["upgrade_task_ids"])
        self.assertTrue(summary["case_study_trace_available"])
        self.assertEqual(summary["next_required_run"], "R420_paper_asset_table_refresh")


if __name__ == "__main__":
    unittest.main()
