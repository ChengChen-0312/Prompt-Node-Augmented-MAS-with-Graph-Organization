import unittest


class TestR420PaperAssetTableRefresh(unittest.TestCase):
    def test_asset_manifest_collects_claim_cost_case_and_lifecycle_assets(self):
        from experiment.mmlu.r420_paper_asset_table_refresh import build_paper_asset_manifest

        summary = build_paper_asset_manifest()

        self.assertEqual(summary["run_id"], "R420")
        asset_types = {asset["asset_type"] for asset in summary["paper_assets"]}
        self.assertIn("claim_matrix", asset_types)
        self.assertIn("cost_table", asset_types)
        self.assertIn("case_study_pack", asset_types)
        self.assertIn("lifecycle_trace", asset_types)
        self.assertIn("C6_definition_challenge_fresh_positive", summary["claim_ids"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R421_submission_readiness_goal_audit")


if __name__ == "__main__":
    unittest.main()
