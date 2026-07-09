import unittest


class TestR284MMLURetrainedGraphAuditCompare(unittest.TestCase):
    def test_summarize_audit_comparison_separates_arg_and_promptnode_structure(self):
        from experiment.mmlu.r284_retrained_graph_audit_compare import (
            summarize_audit_comparison,
        )

        arg_training = {
            "run_id": "R282",
            "role_mapping_size": 6,
            "pn_roles_present": [],
        }
        pn_training = {
            "run_id": "R283",
            "role_mapping_size": 9,
            "pn_roles_present": ["PN_Memory", "PN_Verifier", "PN_Router"],
        }
        arg_details = [
            {
                "is_dag": True,
                "num_nodes": 6,
                "num_edges": 8,
                "roles": ["Critic", "Mathematician"],
                "has_any_pn": False,
                "promptedge_contract_ready": False,
            }
        ]
        pn_details = [
            {
                "is_dag": True,
                "num_nodes": 9,
                "num_edges": 12,
                "roles": ["Mathematician", "PN_Memory", "PN_Verifier", "PN_Router"],
                "has_any_pn": True,
                "has_all_pn_roles": True,
                "promptedge_contract_ready": True,
            }
        ]

        summary = summarize_audit_comparison(
            arg_training=arg_training,
            promptnode_training=pn_training,
            arg_details=arg_details,
            promptnode_details=pn_details,
            run_id="R284",
        )

        self.assertEqual(summary["run_id"], "R284")
        self.assertTrue(summary["no_api"])
        self.assertEqual(summary["arg"]["training_role_mapping_size"], 6)
        self.assertEqual(summary["arg"]["pn_roles_present"], [])
        self.assertEqual(summary["arg"]["any_pn_rate"], 0.0)
        self.assertEqual(summary["promptnode"]["training_role_mapping_size"], 9)
        self.assertEqual(summary["promptnode"]["pn_roles_present"], ["PN_Memory", "PN_Verifier", "PN_Router"])
        self.assertEqual(summary["promptnode"]["any_pn_rate"], 1.0)
        self.assertEqual(summary["promptnode"]["contract_ready_rate"], 1.0)
        self.assertTrue(summary["structural_claim_supported"])
        self.assertFalse(summary["accuracy_claim_supported"])


if __name__ == "__main__":
    unittest.main()
