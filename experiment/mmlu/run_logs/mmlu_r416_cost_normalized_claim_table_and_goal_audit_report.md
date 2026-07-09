# R416 Cost-Normalized Claim Table And Goal Audit

**Claim boundary**: R416 prepares paper-facing cost rows from available evidence. It exposes missing cost fields instead of authorizing submission claims.

| Row | Slice | Score | Cost | Cost/task | Correct/cost | Fix/Harm/Wrong | Role |
|---|---|---:|---:|---:|---:|---:|---|
| `AQuA_ARG_baseline` | `AQuA_tail34_official` | `28/34` | `0.93285` | `0.027437` | `30.015544` | `n/a` | ARG baseline |
| `AQuA_R068_cost_reduced` | `AQuA_tail34_official` | `31/34` | `3.597409` | `0.105806` | `8.617313` | `n/a` | cost-reduced PromptNode replay |
| `AQuA_R267_safety_cost` | `AQuA_tail34_audit_boundary` | `31/31` | `3.597409` | `0.116045` | `8.617313` | `n/a` | cost-reduced plus safety-gated replay |
| `MMLU_STEM_R306_cost_missing` | `MMLU_STEM_main97` | `95/97` | `None` | `None` | `None` | `2/0/n/a` | MMLU STEM positive result with missing raw API cost |
| `MMLU_DefinitionChallenge_R413` | `MMLU_definition_challenge_fresh24` | `22/24` | `0.220095` | `0.009171` | `99.956837` | `1/0/0` | fresh targeted nonmath PromptNode/PromptEdge gate |
| `MMLU_plain_requery_R316` | `MMLU_nonSTEM40_plain_requery_control` | `37/40` | `0.11794` | `0.002949` | `313.71884` | `1/1/n/a` | cost-matched plain requery control |

## Missing Cost Evidence

- `MMLU_STEM_cost_missing`
- `independent_integrity_audit_missing`

## Goal Check

- `still_aligned_with_sci_q2_goal`: `True`
- `arg_designer_remains_main_baseline`: `True`
- `promptnode_first_class_boundary_preserved`: `True`
- `cost_reporting_gap_visible`: `True`
- `broad_nonmath_overclaim_blocked`: `True`
- `next_needs_case_study_and_audit`: `True`

- Next required run: `R417_case_study_evidence_pack`
