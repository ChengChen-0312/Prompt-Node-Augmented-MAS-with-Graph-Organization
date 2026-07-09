import unittest


class TestR423MmluStemCostProbeManifest(unittest.TestCase):
    def test_manifest_builds_leakage_free_stem_cost_probe(self):
        from experiment.mmlu.r423_mmlu_stem_cost_probe_manifest import build_cost_probe_manifest

        records, summary = build_cost_probe_manifest()

        self.assertEqual(summary["run_id"], "R423")
        self.assertEqual(summary["tasks"], 12)
        self.assertEqual(summary["api_records"], 24)
        self.assertTrue(summary["leakage_pass"])
        self.assertTrue(summary["cost_probe_authorized_next"])
        prompt = "\n".join(records[0]["model_visible_messages"][i]["content"] for i in range(len(records[0]["model_visible_messages"])))
        self.assertNotIn("true_answer", prompt.lower())
        self.assertNotIn("task_id", prompt.lower())
        self.assertEqual(summary["next_required_run"], "R424_mmlu_stem_cost_probe_api_execution")


if __name__ == "__main__":
    unittest.main()
