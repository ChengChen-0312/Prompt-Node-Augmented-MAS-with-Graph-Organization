import tempfile
import unittest
from pathlib import Path

from experiment.mmlu.r191_projected_promptedge_smoke import (
    load_baseline_lookup,
    select_first_n_records,
    select_records_by_task_ids,
)


class TestR191MMLUProjectedSmokeRunner(unittest.TestCase):
    def test_load_baseline_lookup_by_task_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "baseline.jsonl"
            path.write_text(
                '{"task_id":"t1","predicted_answer":"A","is_correct":true}\n'
                '{"task_id":"t2","predicted_answer":"B","is_correct":false}\n',
                encoding="utf-8",
            )

            lookup = load_baseline_lookup(str(path))

        self.assertEqual(lookup["t1"]["predicted_answer"], "A")
        self.assertFalse(lookup["t2"]["is_correct"])

    def test_select_first_n_records_is_not_answer_based(self):
        records = [{"task_id": f"t{i}", "answer": "A"} for i in range(10)]
        selected = select_first_n_records(records, 4)

        self.assertEqual([row["task_id"] for row in selected], ["t0", "t1", "t2", "t3"])

    def test_select_records_by_task_ids_preserves_requested_order(self):
        records = [{"task_id": f"t{i}", "answer": "A"} for i in range(5)]
        selected = select_records_by_task_ids(records, ["t3", "t1"])

        self.assertEqual([row["task_id"] for row in selected], ["t3", "t1"])


if __name__ == "__main__":
    unittest.main()
