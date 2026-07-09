import unittest


class TestR473CompileCommandHarness(unittest.TestCase):
    def test_compile_harness_never_claims_pdf_without_successful_engine_run(self):
        from experiment.mmlu.r473_compile_command_harness import run_harness

        summary = run_harness()

        self.assertEqual(summary["run_id"], "R473")
        self.assertIn("engine_available", summary)
        self.assertIn("compile_attempted", summary)
        self.assertIn("pdf_exists", summary)
        if not summary["engine_available"]:
            self.assertFalse(summary["compile_attempted"])
            self.assertEqual(summary["compile_status"], "blocked_no_latex_engine")
            self.assertFalse(summary["pdf_verified"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R474_local_smoke_after_latex_harness")


if __name__ == "__main__":
    unittest.main()
