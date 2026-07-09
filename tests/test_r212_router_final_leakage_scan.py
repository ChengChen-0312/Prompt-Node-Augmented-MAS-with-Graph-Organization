import json
import tempfile
import unittest
from pathlib import Path

from experiment.mmlu.r212_router_final_leakage_scan import scan_manifest


class TestR212RouterFinalLeakageScan(unittest.TestCase):
    def _write_manifest(self, rows):
        tmpdir = tempfile.TemporaryDirectory()
        path = Path(tmpdir.name) / "manifest.jsonl"
        path.write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n",
            encoding="utf-8",
        )
        self.addCleanup(tmpdir.cleanup)
        return path

    def _clean_row(self):
        return {
            "question": "Q",
            "is_correct": True,
            "source_question_hash": "abc",
            "router_final_schema": {
                "schema_version": "r211_router_final_v1",
                "router_action": "abstain",
                "target_option_label": "NONE",
                "model_visible_fields": ["question", "roles", "edges"],
                "forbidden_model_visible_fields": [
                    "answer",
                    "true_answer",
                    "is_correct",
                    "task_id",
                    "source_question_hash",
                ],
                "gold_answer_used": False,
            },
        }

    def test_scan_clean_manifest_has_zero_violations(self):
        path = self._write_manifest([self._clean_row(), self._clean_row()])

        summary = scan_manifest(str(path))

        self.assertEqual(summary["rows"], 2)
        self.assertEqual(summary["missing_schema"], 0)
        self.assertEqual(summary["leakage_violations"], 0)
        self.assertEqual(summary["router_actions"], {"abstain": 2})
        self.assertTrue(summary["abstain_only"])

    def test_scan_flags_model_visible_forbidden_field(self):
        row = self._clean_row()
        row["router_final_schema"]["model_visible_fields"].append("is_correct")
        path = self._write_manifest([row])

        summary = scan_manifest(str(path))

        self.assertEqual(summary["leakage_violations"], 1)
        self.assertIn("model_visible_forbidden_intersection", summary["violations"][0]["reason"])
        self.assertFalse(summary["leakage_pass"])

    def test_scan_flags_missing_schema(self):
        path = self._write_manifest([{"question": "Q"}])

        summary = scan_manifest(str(path))

        self.assertEqual(summary["missing_schema"], 1)
        self.assertFalse(summary["schema_pass"])


if __name__ == "__main__":
    unittest.main()
