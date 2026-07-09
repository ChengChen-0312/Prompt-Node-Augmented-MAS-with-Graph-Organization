import unittest
from pathlib import Path


class TestR432PaperMainTexScaffold(unittest.TestCase):
    def test_scaffold_links_existing_sections_without_overclaiming(self):
        from experiment.mmlu.r432_paper_main_tex_scaffold import run_scaffold

        summary = run_scaffold()

        self.assertEqual(summary["run_id"], "R432")
        self.assertTrue(Path(summary["main_tex"]).exists())
        self.assertTrue(Path(summary["math_commands_tex"]).exists())
        self.assertTrue(Path(summary["references_bib"]).exists())
        self.assertEqual(summary["stale_section_files"], [])
        expected_sections = [str(path) for path in sorted(Path("paper/sections").glob("*.tex"))]
        self.assertEqual(summary["referenced_sections"], expected_sections)
        self.assertTrue(summary["scaffold_links_all_existing_sections"])
        self.assertFalse(summary["complete_paper_draft"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R433_front_matter_and_related_work_preflight")


if __name__ == "__main__":
    unittest.main()
