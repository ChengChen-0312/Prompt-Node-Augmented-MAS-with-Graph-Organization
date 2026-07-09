import unittest
from pathlib import Path


class TestR463SourcePackageManifest(unittest.TestCase):
    def test_source_package_manifest_includes_paper_sources_and_excludes_secrets(self):
        from experiment.mmlu.r463_source_package_manifest import run_manifest

        summary = run_manifest()
        repo = Path(__file__).resolve().parents[1]
        manifest = (repo / summary["manifest_md"]).read_text(encoding="utf-8")

        self.assertEqual(summary["run_id"], "R463")
        self.assertIn("paper/main.tex", summary["package_sources"])
        self.assertIn("paper/references.bib", summary["package_sources"])
        self.assertIn("paper/appendices/label_audit.tex", summary["package_sources"])
        self.assertIn("paper/tables/main_results.tex", summary["package_sources"])
        self.assertIn(".env", summary["excluded_patterns"])
        self.assertNotIn("sk-", manifest)
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R464_external_audit_authorization_checklist")


if __name__ == "__main__":
    unittest.main()
