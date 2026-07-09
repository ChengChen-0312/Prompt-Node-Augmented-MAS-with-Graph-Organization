# R334 Prospective Selector Eval Preflight

**Claim boundary**: R334 constructs a leakage-checked held-out manifest only. It authorizes a bounded API smoke next if leakage remains clean.

- Tasks: `48`
- Records: `144`
- Family counts: `{'mmlu_nonstem': 24, 'mmlu_stem': 24}`
- Variant counts: `{'arg_baseline_direct': 48, 'cost_matched_plain_requery': 48, 'selector_promptnode_promptedge_policy': 48}`
- Leakage pass: `True`
- API calls next: `96`
- API execution authorized next: `True`
- Next required run: `R335_prospective_selector_eval_api_smoke`
