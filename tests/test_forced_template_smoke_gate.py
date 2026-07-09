import unittest


class ForcedTemplateSmokeGateTests(unittest.TestCase):
    def test_gate_accepts_clean_positive_smokes_and_suppresses_none_boundary(self):
        from experiment.aqua.forced_template_smoke_gate import build_gate_summary

        summary = build_gate_summary()

        self.assertEqual(summary["rule"], "r086_forced_template_smoke_gate")
        self.assertEqual(summary["clean_positive_rows"], 3)
        self.assertEqual(summary["clean_positive_accepted"], 3)
        self.assertEqual(summary["boundary_rows"], 1)
        self.assertEqual(summary["boundary_suppressed"], 1)
        self.assertEqual(summary["accepted_rows"], 3)
        self.assertEqual(summary["suppressed_rows"], 1)
        self.assertEqual(summary["decision_field_violations"], 0)
        self.assertEqual(summary["claim_boundary"], "smoke-gate replay only, not tail34 accuracy")

    def test_decision_features_exclude_outcome_and_group_fields(self):
        from experiment.aqua.forced_template_smoke_gate import (
            FORBIDDEN_DECISION_FIELDS,
            build_decision_features,
            load_default_smoke_rows,
        )

        rows = load_default_smoke_rows()
        for row in rows:
            features = build_decision_features(row)
            self.assertFalse(FORBIDDEN_DECISION_FIELDS.intersection(features))


if __name__ == "__main__":
    unittest.main()
