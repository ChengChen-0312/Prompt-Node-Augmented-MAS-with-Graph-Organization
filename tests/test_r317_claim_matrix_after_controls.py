import unittest


class TestR317ClaimMatrixAfterControls(unittest.TestCase):
    def test_claim_matrix_records_plain_requery_and_promptedge_controls(self):
        from experiment.mmlu.r317_claim_matrix_after_controls import build_claim_matrix_summary

        summary = build_claim_matrix_summary()
        evidence = summary["evidence"]

        self.assertEqual(summary["run_id"], "R317")
        self.assertEqual(evidence["mmlu_nonstem_plain_requery"]["proposed"], "37/40")
        self.assertEqual(evidence["mmlu_nonstem_plain_requery"]["fix_harm"], "1/1")
        self.assertEqual(evidence["mmlu_nonstem_node_only_no_edge_text"]["proposed"], "35/40")
        self.assertEqual(evidence["mmlu_nonstem_node_only_no_edge_text"]["fix_harm"], "0/2")
        self.assertFalse(summary["claim_permissions"]["plain_requery_beaten_on_nonstem"])
        self.assertTrue(summary["claim_permissions"]["promptedge_text_needed_for_nonstem_safety"])
        self.assertFalse(summary["training_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R318_symbolic_family_ablation")


if __name__ == "__main__":
    unittest.main()
