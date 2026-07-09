# R411 Curriculum Gate Ablation And Goal Audit

**Claim boundary**: R411 is a same-split diagnostic ablation. It may define a prospective gate hypothesis, but it cannot support a positive nonmath paper claim.

- Best diagnostic gate: `logical_fallacy_definition_gate`
- Best correct/fix/harm/wrong-forward: `28/1/0/1`
- Same split only: `True`

## Gate Ablations

- `parser_repair_conservative`: correct `27`, fix/harm/wrong `0/0/0`
- `relaxed_margin_015`: correct `28`, fix/harm/wrong `2/1/4`
- `logical_fallacy_definition_gate`: correct `28`, fix/harm/wrong `1/0/1`
- `non_sociology_relaxed_gate`: correct `28`, fix/harm/wrong `1/0/2`
- `logic_moral_philosophy_gate`: correct `28`, fix/harm/wrong `1/0/2`

## Goal Check

- `still_aligned_with_sci_q2_goal`: `True`
- `arg_designer_remains_main_baseline`: `True`
- `promptnode_first_class_boundary_preserved`: `True`
- `nonmath_positive_claim_not_yet_supported`: `True`
- `fresh_transfer_required_next`: `True`
- `overclaiming_blocked`: `True`

- Next required run: `R412_fresh_definition_challenge_gate_preflight`
