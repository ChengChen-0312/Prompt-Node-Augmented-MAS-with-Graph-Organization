import json
import os
import tempfile
import unittest


def _write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


class MMLUTransferDatasetTests(unittest.TestCase):
    def test_dataset_respects_split_indices_and_preserves_task_fields(self):
        from experiment.mmlu.transfer_dataset import MMLUTransferDataset

        with tempfile.TemporaryDirectory() as tmpdir:
            records_path = os.path.join(tmpdir, "records.jsonl")
            split_path = os.path.join(tmpdir, "split.json")
            _write_jsonl(
                records_path,
                [
                    {"task_id": "t0", "task": "Question 0", "answer": "A", "subject": "math"},
                    {"task_id": "t1", "task": "Question 1", "answer": "B", "subject": "physics"},
                    {"task_id": "t2", "question": "Question 2", "answer": "C", "subject": "cs"},
                ],
            )
            with open(split_path, "w", encoding="utf-8") as f:
                json.dump({"test_indices": [2, 0]}, f)

            dataset = MMLUTransferDataset(records_path, split_path)

            self.assertEqual(len(dataset), 2)
            self.assertEqual([dataset[i]["task_id"] for i in range(len(dataset))], ["t2", "t0"])
            self.assertEqual(dataset.record_to_input(dataset[0]), {"task": "Question 2"})
            self.assertEqual(dataset.record_to_target_answer(dataset[0]), "C")

    def test_dataset_can_filter_by_split_task_ids(self):
        from experiment.mmlu.transfer_dataset import MMLUTransferDataset

        with tempfile.TemporaryDirectory() as tmpdir:
            records_path = os.path.join(tmpdir, "records.jsonl")
            split_path = os.path.join(tmpdir, "split.json")
            _write_jsonl(
                records_path,
                [
                    {"task_id": "t0", "task": "Question 0", "answer": "A"},
                    {"task_id": "t1", "task": "Question 1", "answer": "B"},
                    {"task_id": "t2", "task": "Question 2", "answer": "C"},
                ],
            )
            with open(split_path, "w", encoding="utf-8") as f:
                json.dump({"task_ids": ["t2", "t1"]}, f)

            dataset = MMLUTransferDataset(records_path, split_path)

            self.assertEqual([record["task_id"] for record in dataset], ["t2", "t1"])

    def test_postprocess_answer_extracts_valid_option_or_abstains(self):
        from experiment.mmlu.transfer_dataset import MMLUTransferDataset

        self.assertEqual(MMLUTransferDataset.postprocess_answer("The answer is Option C."), "C")
        self.assertEqual(MMLUTransferDataset.postprocess_answer(["I choose D because of elimination."]), "D")
        self.assertEqual(MMLUTransferDataset.postprocess_answer("No valid option is supported."), "")


if __name__ == "__main__":
    unittest.main()
