import unittest


class PromptNodeModelCompatTests(unittest.TestCase):
    def test_sampling_roles_are_filtered_to_checkpoint_role_mapping(self):
        from experiment.model import filter_sampling_roles_for_mapping

        role_embeddings = {
            "Math Solver": object(),
            "Programming Expert": object(),
            "PN_Memory": object(),
        }
        role_to_id = {"Math Solver": 0, "Programming Expert": 1}

        roles = filter_sampling_roles_for_mapping(role_embeddings, role_to_id)

        self.assertEqual(roles, ["Math Solver", "Programming Expert"])


if __name__ == "__main__":
    unittest.main()
