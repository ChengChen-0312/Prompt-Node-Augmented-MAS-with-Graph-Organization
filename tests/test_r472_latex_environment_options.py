import unittest


class TestR472LatexEnvironmentOptions(unittest.TestCase):
    def test_latex_options_record_engine_status_without_installing(self):
        from experiment.mmlu.r472_latex_environment_options import run_options

        summary = run_options()

        self.assertEqual(summary["run_id"], "R472")
        self.assertFalse(summary["installation_performed"])
        self.assertIn("latexmk", summary["engine_probe"])
        self.assertIn("pdflatex", summary["engine_probe"])
        self.assertGreaterEqual(len(summary["install_options"]), 2)
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R473_compile_command_harness")


if __name__ == "__main__":
    unittest.main()
