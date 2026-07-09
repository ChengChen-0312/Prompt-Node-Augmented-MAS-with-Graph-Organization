# R370 Adversarial Verifier Probe Analysis

**Claim boundary**: R370 analyzes the targeted R369 probe. It rejects unconstrained domain verifiers as unsafe and keeps only the history-passage signal as a future preflight candidate.

- Domain candidates/correct/precision: `8/2/0.25`
- Adversarial block count: `0`
- History correct: `2`
- Wrong-domain subjects: `{'college_chemistry': 2, 'college_mathematics': 1, 'high_school_chemistry': 1, 'high_school_physics': 2}`
- Root causes: `['adversarial_prompt_repeated_prior_candidate', 'unconstrained_domain_verifier_is_unsafe', 'needs_evidence_type_specific_gate_features', 'passage_history_entailment_is_promising_but_needs_fresh_validation']`
- Next required run: `R371_adversarial_probe_hard_negative_update`
