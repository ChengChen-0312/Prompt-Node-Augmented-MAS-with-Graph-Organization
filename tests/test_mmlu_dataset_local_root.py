import os
import tempfile
import unittest
from pathlib import Path


class MMLUDatasetLocalRootTests(unittest.TestCase):
    def test_mmlu_dataset_uses_env_data_root(self):
        from datasets.mmlu_dataset import MMLUDataset

        old_root = os.environ.get("MMLU_DATA_ROOT")
        with tempfile.TemporaryDirectory() as tmpdir:
            dev_dir = Path(tmpdir) / "dev"
            dev_dir.mkdir()
            (dev_dir / "toy_dev.csv").write_text(
                "What is 2+2?,3,4,5,6,B\n", encoding="utf-8"
            )
            os.environ["MMLU_DATA_ROOT"] = tmpdir
            try:
                dataset = MMLUDataset("dev")
            finally:
                if old_root is None:
                    os.environ.pop("MMLU_DATA_ROOT", None)
                else:
                    os.environ["MMLU_DATA_ROOT"] = old_root

        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset.record_to_target_answer(dataset[0]), "B")


if __name__ == "__main__":
    unittest.main()
