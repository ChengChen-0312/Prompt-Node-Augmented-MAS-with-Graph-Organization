# R336 Prospective Selector Eval Smoke Analysis

**Claim boundary**: R336 analyzes the 6-task API smoke. It supports only selector no-harm on the smoke and a plain-requery harm control; it does not support a prospective improvement claim.

- Selector vs ARG: `{'arg': '4/6', 'selector': '4/6', 'delta_correct': 0, 'fix_harm': '0/0'}`
- Plain requery vs ARG: `{'arg': '4/6', 'plain_requery': '2/6', 'delta_correct': -2, 'fix_harm': '0/2'}`
- Claim permissions: `{'selector_no_harm_smoke_allowed': True, 'selector_improvement_claim_allowed': False, 'plain_requery_harm_control_allowed': True, 'full_prospective_claim_allowed': False, 'sci_q2_ready': False}`
- Expand authorized next: `True`
- Next required run: `R337_prospective_selector_eval_expand24`
