# R365 Wrong-Forward And Missed-Fix Analysis

**Claim boundary**: R365 diagnoses why R363 gains only one item. It does not authorize more API; it identifies candidate quality and missing verifier families as the next bottlenecks.

- Wrong forwards: `1` `['MMLU-college_mathematics_test-15']`
- Missed fixes: `10`
- Missed-fix subjects: `{'college_chemistry': 4, 'college_mathematics': 1, 'high_school_chemistry': 1, 'high_school_physics': 2, 'high_school_us_history': 2}`
- Root causes: `['candidate_quality_not_gate_threshold_is_primary_bottleneck', 'single_candidate_forward_lacks_adversarial_verification', 'chemistry_and_physics_specialized_verifiers_missing', 'passage_history_entailment_verifier_too_weak']`

## Recommended Next Design

- Add adversarial verifier edge for high-confidence single-candidate forwards.
- Add chemistry/physics verifier candidates with stricter evidence contracts.
- Add passage-entailment verifier for history tasks with quoted source text.
- Keep R360 gate threshold conservative; improve candidate generation before relaxing it.

- Next required run: `R366_goal_audit_after_source_invariant_fresh_eval`
