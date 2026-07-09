# R360 Source-Invariant Graph-Policy Retraining

**Claim boundary**: R360 retrains the offline graph-policy gate after removing source_run features and uses a conservative 0.7 forward threshold. It remains an offline feasibility step.

- Decision threshold: `0.7`
- Dev FP/FN: `0/0`
- Test FP/FN: `0/0`
- Top positive features: `['candidate_evidence_count', 'gate_score', 'candidate_has_answer_label', 'lifecycle_has_upgrade', 'lifecycle_has_update']`
- Next required run: `R361_goal_audit_after_source_invariant_policy`
