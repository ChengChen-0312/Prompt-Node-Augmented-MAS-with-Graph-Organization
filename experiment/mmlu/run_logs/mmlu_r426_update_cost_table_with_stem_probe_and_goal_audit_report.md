# R426 Update Cost Table With STEM Probe And Goal Audit

**Claim boundary**: R426 replaces the missing MMLU STEM cost row with a probe estimate. This improves draft completeness but does not make submission cost evidence exact or audited.

| Row | Score | Cost | Evidence | Note |
|---|---:|---:|---|---|
| `AQuA_ARG_baseline` | `28/34` | `0.93285` | `direct_or_existing_summary` | AQuA replay cost from R271. |
| `AQuA_R068_cost_reduced` | `31/34` | `3.597409` | `direct_or_existing_summary` | Retains R065 official score with lower multi-view cost. |
| `AQuA_R267_safety_cost` | `31/31` | `3.597409` | `direct_or_existing_summary` | Audit-boundary interpretation; not the highest official score. |
| `MMLU_STEM_R306_probe_estimate` | `95/97` | `0.676454` | `probe_estimate_not_exact` | Cost is extrapolated from R424 12-task probe; not exact R306 accounting. |
| `MMLU_DefinitionChallenge_R413` | `22/24` | `0.220095` | `direct_or_existing_summary` | Cost includes both ARG direct baseline and DefinitionChallenge candidate calls. |
| `MMLU_plain_requery_R316` | `37/40` | `0.11794` | `direct_or_existing_summary` | Approximate half of R316 total API cost, because node-only and plain-requery each made 40 API calls. |

## Missing Cost Evidence

- `independent_integrity_audit_missing`

## Goal Check

- `still_aligned_with_sci_q2_goal`: `True`
- `arg_designer_remains_main_baseline`: `True`
- `promptnode_first_class_boundary_preserved`: `True`
- `mmlu_stem_cost_gap_reduced`: `True`
- `estimate_not_misrepresented_as_exact`: `True`
- `external_audit_still_required`: `True`
- `overclaiming_blocked`: `True`

- Next required run: `R427_external_integrity_audit_refresh`
