import unittest


class TestR462JournalTemplateProbe(unittest.TestCase):
    def test_template_probe_records_jair_primary_and_springer_backup(self):
        from experiment.mmlu.r462_journal_template_probe import run_probe

        summary = run_probe()

        self.assertEqual(summary["run_id"], "R462")
        self.assertEqual(summary["primary_template_target"], "JAIR")
        self.assertEqual(summary["backup_template_target"], "KAIS")
        self.assertIn("JAIR Author Kit", summary["template_sources"]["JAIR"]["template"])
        self.assertIn("Springer Nature", summary["template_sources"]["KAIS"]["template"])
        self.assertFalse(summary["template_conversion_performed"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R463_source_package_manifest")


if __name__ == "__main__":
    unittest.main()
