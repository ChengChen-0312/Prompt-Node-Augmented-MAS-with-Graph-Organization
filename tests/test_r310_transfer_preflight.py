import unittest


class TestR310TransferPreflight(unittest.TestCase):
    def test_transfer_preflight_creates_nonstem_split_and_blocks_training(self):
        from experiment.mmlu.r310_transfer_preflight import build_transfer_preflight_summary

        records, summary = build_transfer_preflight_summary(max_per_subject=5)

        self.assertEqual(summary["run_id"], "R310")
        self.assertEqual(summary["nonstem_preflight"]["records"], 40)
        self.assertEqual(summary["nonstem_preflight"]["subject_count"], 8)
        self.assertEqual(summary["transfer_splits"]["aqua_tail34_audit_clean"]["r065"], "31/31")
        self.assertEqual(summary["transfer_splits"]["mmlu_stem_main97"]["arg"], "88/97")
        self.assertEqual(summary["transfer_splits"]["mmlu_stem_main97"]["r306"], "95/97")
        self.assertFalse(summary["claim_permissions"]["transfer_accuracy_claim_allowed"])
        self.assertFalse(summary["training_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R311_nonstem_arg_promptnode_eval")
        self.assertEqual(len(records), 40)

    def test_nonstem_records_have_promptnode_candidate_schema(self):
        from experiment.mmlu.r310_transfer_preflight import build_transfer_preflight_summary

        records, summary = build_transfer_preflight_summary(max_per_subject=5)

        self.assertTrue(all("candidate" in row for row in records))
        self.assertTrue(all(row.get("answer") == row.get("true_answer") for row in records))
        self.assertTrue(all(row["candidate"]["model_visible_features_only"] for row in records))
        self.assertGreaterEqual(summary["nonstem_preflight"]["candidate_records"], 1)


if __name__ == "__main__":
    unittest.main()
