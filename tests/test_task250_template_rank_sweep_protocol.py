import unittest


class Task250TemplateRankSweepProtocolTests(unittest.TestCase):
    def test_protocol_preregisters_rank2_to_rank5_clean_switch_probe_only(self):
        from experiment.aqua.task250_template_rank_sweep_protocol import build_protocol

        protocol = build_protocol()

        self.assertEqual(protocol["rule"], "r099_task250_template_rank_sweep_protocol")
        self.assertEqual(protocol["task_id"], "task_250")
        self.assertEqual(protocol["task_split_indices"], [250])
        self.assertEqual(protocol["sweep_ranks"], [2, 3, 4, 5])
        self.assertEqual(protocol["excluded_ranks"], [1])
        self.assertEqual(protocol["desired_prediction"], "E")
        self.assertEqual(protocol["model"], "gpt-4o-2024-08-06")
        self.assertEqual(protocol["num_tasks"], 1)
        self.assertFalse(protocol["is_full_tail34"])
        self.assertEqual(
            protocol["claim_boundary"],
            "pre-registered task250 rank2-5 template sweep; no result or accuracy claim",
        )


if __name__ == "__main__":
    unittest.main()
