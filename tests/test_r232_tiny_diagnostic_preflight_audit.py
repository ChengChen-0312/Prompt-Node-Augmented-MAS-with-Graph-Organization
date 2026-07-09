import unittest
import hashlib

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import (
    audit_preflight_records,
    inspect_env_keys,
)


class TestR232TinyDiagnosticPreflightAudit(unittest.TestCase):
    def _api_record(self, **overrides):
        messages = [
            {"role": "system", "content": "Use visible signals only."},
            {"role": "user", "content": "Question text\nselected_label values: A, B, C, D, E, NONE."},
        ]
        prompt_text = "\n".join(message["content"] for message in messages)
        record = {
            "task_id": "task_1",
            "control_variant": "proposed_router_final",
            "api_required": True,
            "model": "gpt-4o-2024-08-06",
            "source_available": True,
            "leakage_pass": True,
            "manifest_leakage_violations": 0,
            "prompt_leakage_violations": 0,
            "estimated_cost": 0.002,
            "model_visible_messages": messages,
            "model_visible_prompt_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
        }
        record.update(overrides)
        return record

    def _deterministic_record(self):
        return {
            "task_id": "task_1",
            "control_variant": "abstain_only_router",
            "api_required": False,
            "model": "gpt-4o-2024-08-06",
            "source_available": True,
            "leakage_pass": True,
            "manifest_leakage_violations": 0,
            "prompt_leakage_violations": 0,
            "estimated_cost": 0.0,
            "model_visible_messages": [],
            "model_visible_prompt_sha256": "",
        }

    def test_valid_records_authorize_tiny_api(self):
        audit = audit_preflight_records(
            [self._api_record(), self._deterministic_record()],
            env_key_status={"has_api_key": True, "has_base_url": True, "loaded_keys": ["API_KEY"]},
            required_model="gpt-4o-2024-08-06",
            cost_cap=0.45,
        )

        self.assertTrue(audit["preflight_pass"])
        self.assertEqual(audit["api_status"], "authorized_tiny_diagnostic")

    def test_missing_env_key_blocks_api(self):
        audit = audit_preflight_records(
            [self._api_record()],
            env_key_status={"has_api_key": False, "has_base_url": False, "loaded_keys": []},
            required_model="gpt-4o-2024-08-06",
            cost_cap=0.45,
        )

        self.assertFalse(audit["preflight_pass"])
        self.assertIn("missing_api_key", audit["blockers"])

    def test_wrong_model_blocks_api(self):
        audit = audit_preflight_records(
            [self._api_record(model="gpt-4o-mini")],
            env_key_status={"has_api_key": True, "has_base_url": True, "loaded_keys": ["API_KEY"]},
            required_model="gpt-4o-2024-08-06",
            cost_cap=0.45,
        )

        self.assertFalse(audit["preflight_pass"])
        self.assertIn("model_mismatch", audit["blockers"])

    def test_prompt_leakage_blocks_api(self):
        audit = audit_preflight_records(
            [
                self._api_record(
                    prompt_leakage_violations=1,
                    model_visible_messages=[{"role": "user", "content": "true_answer: D"}],
                )
            ],
            env_key_status={"has_api_key": True, "has_base_url": True, "loaded_keys": ["API_KEY"]},
            required_model="gpt-4o-2024-08-06",
            cost_cap=0.45,
        )

        self.assertFalse(audit["preflight_pass"])
        self.assertIn("leakage_violations", audit["blockers"])

    def test_cost_over_cap_blocks_api(self):
        audit = audit_preflight_records(
            [self._api_record(estimated_cost=0.50)],
            env_key_status={"has_api_key": True, "has_base_url": True, "loaded_keys": ["API_KEY"]},
            required_model="gpt-4o-2024-08-06",
            cost_cap=0.45,
        )

        self.assertFalse(audit["preflight_pass"])
        self.assertIn("cost_over_cap", audit["blockers"])

    def test_env_inspection_reports_key_names_only(self):
        status = inspect_env_keys(["API_KEY=secret-value", "BASE_URL=https://example.test"])

        self.assertTrue(status["has_api_key"])
        self.assertTrue(status["has_base_url"])
        self.assertEqual(sorted(status["loaded_keys"]), ["API_KEY", "BASE_URL"])
        self.assertNotIn("secret-value", str(status))


if __name__ == "__main__":
    unittest.main()
