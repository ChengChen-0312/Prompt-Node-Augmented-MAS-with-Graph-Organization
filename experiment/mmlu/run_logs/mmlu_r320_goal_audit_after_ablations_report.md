# R320 Goal Audit After Ablations

**Claim boundary**: R320 is the required five-iteration goal audit after R315-R319. The work stayed aligned with the SCI-Q2 PromptNode goal by completing reviewer-facing ablations, but it still does not justify a broad general-improvement claim or training a selector from warning-only non-STEM nodes.

## Alignment

- `still_aligned_with_sci_q2_goal`: `True`
- `arg_designer_baseline_preserved`: `True`
- `promptnode_as_first_class_graph_node_preserved`: `True`
- `promptedge_as_first_class_constraint_preserved`: `True`
- `priority_ablations_completed`: `True`
- `promptedge_text_validated`: `True`
- `cost_matched_requery_checked`: `True`
- `symbolic_and_nonmath_contributions_separated`: `True`
- `nonstem_negative_transfer_not_hidden`: `True`
- `claim_boundary_narrowed_correctly`: `True`

## Claim Permissions

- `aqua_clean_improvement_allowed`: `True`
- `mmlu_stem_improvement_allowed`: `True`
- `mmlu_nonstem_no_harm_allowed`: `True`
- `mmlu_nonstem_improvement_allowed`: `False`
- `broad_general_promptnode_claim_allowed`: `False`
- `training_authorized`: `False`
- `sci_q2_ready`: `False`

## Course Correction

- Treat non-STEM semantic/warning PromptNodes as lifecycle and safety signals unless a future prospective run shows answer-bearing gains.
- Do not claim generic transfer improvement: current positive evidence is AQuA audit-clean and MMLU STEM, while non-STEM supports no-harm only.
- Use the completed ablations to write the method boundary: PromptNode identity, PromptEdge text, SafetyGate, and lifecycle pruning are all necessary controls.
- Before training, build a paper evidence table and a selector-training gate that forbids learning from label-audited or warning-only override failures.

- Next required run: `R321_paper_evidence_table_and_training_gate`
