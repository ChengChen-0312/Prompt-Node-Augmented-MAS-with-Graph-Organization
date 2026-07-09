# R405 Experiment Integrity Local Precheck

**Claim boundary**: R405 is a deterministic local precheck for result existence, number consistency, and claim boundaries. It does not replace the required independent experiment-audit reviewer.

- Local precheck status: `pass_external_pending`
- External review required: `True`
- Integrity audit complete: `False`
- Paper claim authorized: `False`

## Checks

- `source_files_exist`: `PASS`
- `claim_number_consistency`: `PASS`
- `overclaim_boundary`: `PASS`

## Claim Checks

- `C1_aqua_audit_clean_gain`: `PASS`; boundary=`allow_narrow_main_claim`; values=`{'baseline': '28/31', 'promptnode': '31/31', 'delta_correct': 3}`
- `C2_mmlu_stem_gain`: `PASS`; boundary=`allow_narrow_main_claim`; values=`{'baseline': '88/97', 'promptnode': '95/97', 'delta_correct': 7, 'fix_harm': '7/0'}`
- `C3_history_optionbinding_pilot_gain`: `PASS`; boundary=`appendix_or_mechanism_pilot_only`; values=`{'records': 24, 'arg_correct': 21, 'hybrid_correct': 24, 'delta_correct': 3, 'harms': 0}`
- `C4_mixed_nonmath_no_harm`: `PASS`; boundary=`allow_no_harm_boundary_claim`; values=`{'records': 48, 'arg_correct': 41, 'hybrid_correct': 41, 'delta_correct': 0, 'harms': 0}`
- `C5_broad_general_improvement`: `PASS`; boundary=`forbid_as_claim`; values=`{'claim_status': 'unsupported', 'paper_use': 'forbidden_claim', 'integrate_contrastive_path': False, 'main_paper_claim_allowed': False}`

- Next required run: `R406_external_integrity_review_package`
