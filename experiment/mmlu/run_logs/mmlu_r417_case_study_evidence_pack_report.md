# R417 Case Study Evidence Pack

**Claim boundary**: R417 extracts reproducible case-study evidence. It supports mechanism discussion only, not new accuracy claims.

## definition_challenge_fix

- Task: `MMLU-nonstem-moral_disputes_test-14`
- Mechanism: DefinitionChallenge gate forwards a candidate that fixes ARG without harm.
- Transition: `{'arg_prediction': 'A', 'candidate_label': 'C', 'final_prediction': 'C', 'true_answer': 'C', 'arg_correct': False, 'candidate_correct': True, 'final_correct': True, 'gate_forward': True, 'gate_block_reasons': []}`
- Evidence file: `experiment/mmlu/run_logs/mmlu_r413_definition_challenge_gate_api_results.jsonl`
- Caveat: none

## verifier_pruned_candidate_harm

- Task: `MMLU-nonstem-logical_fallacies_test-12`
- Mechanism: Conflict-resolution and gate contracts block a candidate that would have harmed an already-correct ARG answer.
- Transition: `{'arg_prediction': 'D', 'candidate_label': 'A', 'final_prediction': 'D', 'true_answer': 'D', 'arg_correct': True, 'candidate_correct': False, 'final_correct': True, 'gate_forward': False, 'gate_block_reasons': ['low_node_agreement', 'weak_definition_anchor', 'adversarial_challenge_failed', 'small_distractor_margin', 'option_binding_contract_failed', 'weak_memory_bridge']}`
- Evidence file: `experiment/mmlu/run_logs/mmlu_r413_definition_challenge_gate_api_results.jsonl`
- Caveat: The blocked row also exposes parser/contract fragility: the raw rationale contains embedded JSON. Use this as a safety-prune case, not as a pure semantic-verifier proof.

## gate_beats_candidate_pool

- Task: `R413_aggregate`
- Mechanism: The gate improves over both ARG and the raw candidate pool by forwarding selectively.
- Transition: `{'arg_correct': 21, 'candidate_correct': 21, 'hybrid_correct': 22, 'fixes': 1, 'harms': 0, 'wrong_forward_count': 0, 'pruned_candidate_harms': 1}`
- Evidence file: `experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json`
- Caveat: Aggregate mechanism case; use alongside task-level cases.

## Missing Case Evidence

- Explicit runtime logs for lifecycle update/compress/prune/merge/upgrade are still needed.
- A clean semantic-verifier-only suppressed-harm case should be collected if available.

- Next required run: `R418_lifecycle_trace_instrumentation_preflight`
