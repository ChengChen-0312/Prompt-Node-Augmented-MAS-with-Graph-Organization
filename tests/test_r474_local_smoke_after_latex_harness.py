import unittest


class TestR474LocalSmokeAfterLatexHarness(unittest.TestCase):
    def test_latex_harness_smoke_passes_without_claiming_pdf(self):
        from experiment.mmlu.r474_local_smoke_after_latex_harness import run_smoke

        summary = run_smoke()

        self.assertEqual(summary["run_id"], "R474")
        self.assertTrue(summary["local_smoke_pass"])
        self.assertEqual(summary["failed_modules"], [])
        self.assertIn("tests.test_r472_latex_environment_options", summary["tested_modules"])
        self.assertIn("tests.test_r473_compile_command_harness", summary["tested_modules"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R475_waiting_for_external_audit_or_latex_engine")


if __name__ == "__main__":
    unittest.main()
