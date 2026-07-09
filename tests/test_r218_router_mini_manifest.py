import unittest

from experiment.mmlu.r218_router_mini_manifest import build_mini_manifest


class TestR218RouterMiniManifest(unittest.TestCase):
    def _target(self, idx, split, action):
        return {
            "task_id": f"{split}_{action}_{idx}",
            "split_role": split,
            "router_action": action,
            "training_allowed": split == "train",
            "frozen_eval_only": split == "frozen_eval",
        }

    def test_mini_manifest_keeps_all_train_switches_and_limited_train_abstains(self):
        records = [
            self._target(1, "train", "switch_to_objective"),
            self._target(2, "train", "switch_to_objective"),
            self._target(1, "train", "abstain"),
            self._target(2, "train", "abstain"),
            self._target(3, "train", "abstain"),
            self._target(4, "train", "abstain"),
        ]

        mini, summary = build_mini_manifest(records, max_abstain_per_switch=1)

        self.assertEqual(summary["train_switch_records"], 2)
        self.assertEqual(summary["train_abstain_records_selected"], 2)
        self.assertEqual(len(mini), 4)
        self.assertEqual(
            [row["router_action"] for row in mini],
            ["switch_to_objective", "switch_to_objective", "abstain", "abstain"],
        )

    def test_mini_manifest_keeps_all_frozen_eval_records(self):
        records = [
            self._target(1, "train", "switch_to_objective"),
            self._target(1, "train", "abstain"),
            self._target(1, "frozen_eval", "switch_to_objective"),
            self._target(2, "frozen_eval", "abstain"),
        ]

        mini, summary = build_mini_manifest(records, max_abstain_per_switch=1)

        frozen = [row for row in mini if row["split_role"] == "frozen_eval"]
        self.assertEqual(len(frozen), 2)
        self.assertEqual(summary["frozen_eval_records"], 2)
        self.assertEqual(summary["frozen_eval_switch_records"], 1)


if __name__ == "__main__":
    unittest.main()
