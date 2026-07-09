import unittest


class ForcedTemplateTail34AuditReportTests(unittest.TestCase):
    def test_r092_full_run_audit_separates_clean_harms_from_noisy_fix(self):
        from experiment.aqua.forced_template_tail34_audit_report import (
            build_tail34_audit_summary,
        )

        summary = build_tail34_audit_summary()

        self.assertEqual(summary["rule"], "r093_forced_template_tail34_clean_noisy_audit")
        self.assertEqual(summary["num_tasks"], 34)
        self.assertEqual(summary["clean_label_counts"], {"noisy": 6, "clean": 28})
        self.assertEqual(summary["overall"], {
            "baseline_solved": 28,
            "forced_template_solved": 25,
            "gate_solved": 27,
            "fix_harm": {"fix": 1, "harm": 2},
        })
        self.assertEqual(summary["by_clean_label"]["clean"]["num_tasks"], 28)
        self.assertEqual(summary["by_clean_label"]["clean"]["baseline_solved"], 27)
        self.assertEqual(summary["by_clean_label"]["clean"]["forced_template_solved"], 24)
        self.assertEqual(summary["by_clean_label"]["clean"]["gate_solved"], 25)
        self.assertEqual(summary["by_clean_label"]["clean"]["fix_harm"], {"fix": 0, "harm": 2})
        self.assertEqual(sorted(summary["by_clean_label"]["clean"]["harm_tasks"]), ["task_188", "task_8"])
        self.assertEqual(summary["by_clean_label"]["noisy"]["num_tasks"], 6)
        self.assertEqual(summary["by_clean_label"]["noisy"]["baseline_solved"], 1)
        self.assertEqual(summary["by_clean_label"]["noisy"]["forced_template_solved"], 1)
        self.assertEqual(summary["by_clean_label"]["noisy"]["gate_solved"], 2)
        self.assertEqual(summary["by_clean_label"]["noisy"]["fix_harm"], {"fix": 1, "harm": 0})
        self.assertEqual(summary["by_clean_label"]["noisy"]["fix_tasks"], ["task_108"])
        self.assertEqual(summary["decision_field_violations"], 0)
        self.assertEqual(
            summary["claim_boundary"],
            "clean/noisy audit of R092 full forced-template validation, not a new method",
        )


if __name__ == "__main__":
    unittest.main()
