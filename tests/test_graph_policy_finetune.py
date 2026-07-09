import json
import os
import subprocess
import sys
import tempfile
import unittest


PN_ROLES = {"PN_Memory", "PN_Verifier", "PN_Router"}


def _write_config(path, role_mapping):
    os.makedirs(path, exist_ok=True)
    open(os.path.join(path, "best_model.pth"), "wb").close()
    with open(os.path.join(path, "configuration.txt"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "dataset": "aqua",
                "data_dir": "../ColdStartData_Aqua",
                "device": "cpu",
                "epochs": 100,
                "batch_size": 4,
                "lr": 5e-5,
                "max_prev_node": 3,
                "max_head_and_tail": None,
                "is_dag": True,
                "role_mapping": role_mapping,
                "id_to_role": {str(value): key for key, value in role_mapping.items()},
                "START_TOKEN_ID": len(role_mapping),
                "END_TOKEN_ID": len(role_mapping) + 1,
            },
            f,
        )


class GraphPolicyFinetuneTests(unittest.TestCase):
    def test_find_latest_promptnode_base_model_requires_promptnode_roles(self):
        from experiment.aqua.train_graph_policy_finetune import find_latest_promptnode_base_model

        with tempfile.TemporaryDirectory() as tmpdir:
            _write_config(os.path.join(tmpdir, "old_arg"), {"Math Solver": 0, "Programming Expert": 1})
            _write_config(
                os.path.join(tmpdir, "pn_arg"),
                {
                    "Math Solver": 0,
                    "Programming Expert": 1,
                    "PN_Memory": 2,
                    "PN_Verifier": 3,
                    "PN_Router": 4,
                },
            )

            found = find_latest_promptnode_base_model(tmpdir)

        self.assertTrue(found.endswith("pn_arg"))

    def test_prepare_finetune_args_overrides_config_with_r054_settings(self):
        from experiment.aqua.train_graph_policy_finetune import prepare_finetune_args

        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = os.path.join(tmpdir, "pn_arg")
            role_mapping = {
                "Math Solver": 0,
                "Programming Expert": 1,
                "PN_Memory": 2,
                "PN_Verifier": 3,
                "PN_Router": 4,
            }
            _write_config(base_dir, role_mapping)
            args = prepare_finetune_args(
                base_model_dir=base_dir,
                finetune_data_dir="experiment/FinetuneData_AQuA_PN_GraphPolicy_R053",
                output_dir=os.path.join(tmpdir, "out"),
                epochs=1,
                batch_size=2,
                lr=1e-4,
                device="cpu",
                max_train_graphs=3,
            )

        self.assertEqual(args.dataset, "aqua")
        self.assertEqual(args.epochs, 1)
        self.assertEqual(args.batch_size, 2)
        self.assertEqual(args.lr, 1e-4)
        self.assertEqual(args.device, "cpu")
        self.assertEqual(args.data_dir, "experiment/ColdStartData_Aqua")
        self.assertEqual(args.data_dir_ef, "experiment/FinetuneData_AQuA_PN_GraphPolicy_R053")
        self.assertEqual(args.max_train_graphs, 3)
        self.assertTrue(PN_ROLES.issubset(set(args.role_mapping)))

    def test_validate_checkpoint_role_compatibility_rejects_non_promptnode_base(self):
        from experiment.aqua.train_graph_policy_finetune import validate_checkpoint_role_compatibility

        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = os.path.join(tmpdir, "old_arg")
            _write_config(base_dir, {"Math Solver": 0, "Programming Expert": 1})
            with self.assertRaisesRegex(ValueError, "PromptNode roles"):
                validate_checkpoint_role_compatibility(base_dir)

    def test_real_r053_data_builds_finetune_components_from_promptnode_base(self):
        from experiment.aqua.train_graph_policy_finetune import (
            build_finetune_components,
            prepare_finetune_args,
        )

        args = prepare_finetune_args(
            base_model_dir="experiment/aqua/output/aqua_pn_mvr_clean_model_20260708-015036",
            finetune_data_dir="experiment/FinetuneData_AQuA_PN_GraphPolicy_R053",
            output_dir="experiment/aqua/output/r054_test_tmp",
            epochs=1,
            batch_size=2,
            lr=5e-5,
            device="cpu",
            max_train_graphs=2,
        )
        components = build_finetune_components(args)

        self.assertEqual(len(components["dataset"]), 2)
        self.assertGreaterEqual(components["stats"]["max_num_nodes"], 4)
        self.assertTrue(PN_ROLES.issubset(set(components["args"].role_mapping)))

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/train_graph_policy_finetune.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
