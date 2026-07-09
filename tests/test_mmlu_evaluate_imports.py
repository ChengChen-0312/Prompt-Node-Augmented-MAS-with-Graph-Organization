import unittest


class MMLUEvaluateImportsTests(unittest.TestCase):
    def test_role_constraints_loader_works_from_repo_root_import(self):
        from experiment.mmlu.evaluate_mmlu import load_role_constraints

        role_constraints = load_role_constraints()

        self.assertIn("Critic", role_constraints)
        self.assertIn("Mathematician", role_constraints)
        self.assertTrue(role_constraints["Critic"])


if __name__ == "__main__":
    unittest.main()
