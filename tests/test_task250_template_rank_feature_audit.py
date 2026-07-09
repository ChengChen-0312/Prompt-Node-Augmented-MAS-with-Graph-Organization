import unittest


class Task250TemplateRankFeatureAuditTests(unittest.TestCase):
    def test_metadata_heuristic_selects_task250_matching_ranks_as_hypothesis_only(self):
        from experiment.aqua.task250_template_rank_feature_audit import build_feature_audit_summary

        summary = build_feature_audit_summary()

        self.assertEqual(summary["rule"], "r101_task250_template_rank_feature_audit")
        self.assertEqual(summary["task_id"], "task_250")
        self.assertEqual(summary["matching_ranks"], [2, 5])
        self.assertEqual(summary["nonmatching_ranks"], [1, 3, 4])
        self.assertEqual(summary["heuristic_selected_ranks"], [2, 5])
        self.assertEqual(summary["heuristic_precision"], "2/2")
        self.assertEqual(summary["heuristic_recall"], "2/2")
        self.assertEqual(summary["heuristic_input_field_violations"], 0)
        self.assertEqual(
            summary["claim_boundary"],
            "task250 metadata feature audit; heuristic hypothesis only, not a general selector",
        )


if __name__ == "__main__":
    unittest.main()
