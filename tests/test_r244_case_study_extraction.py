import unittest

from experiment.mmlu.r244_case_study_extraction import select_case_studies


class TestR244CaseStudyExtraction(unittest.TestCase):
    def test_select_case_studies(self):
        rows = [
            {"task_id": "fix", "split_role": "frozen_eval", "fix": True, "harm": False, "switch": True, "baseline_correct": False, "selected_correct": True},
            {"task_id": "protect", "split_role": "train", "fix": False, "harm": False, "switch": False, "baseline_correct": True, "selected_correct": True, "clean_label": "clean"},
            {"task_id": "nofix", "split_role": "train", "fix": False, "harm": False, "switch": True, "baseline_correct": False, "selected_correct": False},
        ]

        selected = select_case_studies(rows)

        self.assertEqual(selected["frozen_fix"]["task_id"], "fix")
        self.assertEqual(selected["abstain_protected_clean"]["task_id"], "protect")
        self.assertEqual(selected["no_fix_objective_wrong"]["task_id"], "nofix")


if __name__ == "__main__":
    unittest.main()
