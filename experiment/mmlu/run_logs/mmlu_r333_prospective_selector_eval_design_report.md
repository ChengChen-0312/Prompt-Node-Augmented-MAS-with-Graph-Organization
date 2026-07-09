# R333 Prospective Selector Eval Design

**Claim boundary**: R333 freezes the prospective selector-evaluation protocol only. It does not construct prompts or call APIs.

- Protocol: `prospective_mmlu_selector_heldout`
- Target size: `{'stem': 24, 'nonstem': 24}`
- Variants: `['arg_baseline_fixed_or_direct', 'selector_promptnode_promptedge_policy', 'cost_matched_plain_requery_control']`
- Success criteria: `['beat_arg_on_clean_stem_or_aqua_like_slice', 'no_harm_on_nonstem', 'fix_harm_nonnegative', 'cost_not_worse_than_plain_requery', 'no_label_audit_exclusions_in_main_metric_without_appendix_report']`
- Estimated budget: `{'records': 48, 'variants_with_api': 2, 'max_api_calls': 96, 'reason': 'Bounded smoke-scale prospective check before larger held-out evaluation.'}`
- API execution authorized next: `False`
- Next required run: `R334_prospective_selector_eval_preflight`
