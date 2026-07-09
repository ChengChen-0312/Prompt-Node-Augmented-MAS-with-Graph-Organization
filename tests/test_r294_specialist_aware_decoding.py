import unittest


class TestR294SpecialistAwareDecoding(unittest.TestCase):
    def test_specialist_aware_selection_prefers_stem_specialist_when_contracts_tie(self):
        from experiment.mmlu.r294_specialist_aware_decoding import select_specialist_aware_candidate

        no_specialist = {
            "candidate_index": 0,
            "subject": "high_school_mathematics",
            "roles": ["Historian", "PN_Memory", "PN_Verifier", "PN_Router"],
            "promptedge_contract_ready": True,
            "has_pn_chain": True,
            "has_all_pn_roles": True,
            "router_is_terminal": True,
            "has_any_pn": True,
            "pn_role_count": 3,
            "is_dag": True,
        }
        with_specialist = {
            **no_specialist,
            "candidate_index": 1,
            "roles": ["Mathematician", "PN_Memory", "PN_Verifier", "PN_Router"],
        }

        selected = select_specialist_aware_candidate([no_specialist, with_specialist])

        self.assertEqual(selected["candidate_index"], 1)

    def test_count_changed_from_reference_uses_reference_selected_manifest(self):
        from experiment.mmlu.r294_specialist_aware_decoding import count_changed_from_reference

        selected = [
            {"task_id": "a", "candidate_index": 1},
            {"task_id": "b", "candidate_index": 2},
        ]
        reference = [
            {"task_id": "a", "candidate_index": 1},
            {"task_id": "b", "candidate_index": 0},
        ]

        self.assertEqual(count_changed_from_reference(selected, reference), 1)


if __name__ == "__main__":
    unittest.main()
