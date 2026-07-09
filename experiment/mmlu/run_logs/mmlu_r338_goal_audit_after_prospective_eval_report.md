# R338 Goal Audit After Prospective Eval

**Claim boundary**: R338 is the five-iteration audit after R333-R337. The prospective selector completed a 24-task held-out smoke, but it tied ARG rather than improving it; therefore prospective improvement remains blocked.

- Prospective result: `{'arg': '20/24', 'selector': '20/24', 'plain_requery': '17/24', 'selector_delta_correct': 0, 'selector_fix_harm': '0/0', 'plain_requery_harms': 3}`

## Claim Permissions

- `prospective_selector_improvement_claim_allowed`: `False`
- `prospective_selector_no_harm_claim_allowed`: `True`
- `plain_requery_harm_control_allowed`: `True`
- `broad_general_promptnode_claim_allowed`: `False`
- `sci_q2_ready`: `False`

## Course Correction

- Analyze why the prospective selector does not switch before spending more API.
- Do not expand to 48/full prospective evaluation until a mechanism-level fix is identified.
- Keep current paper claims anchored on AQuA audit-clean and MMLU STEM positive evidence.
- Use prospective selector as no-harm/cost-control evidence only unless later runs show positive gain.

- Next required run: `R339_selector_non_switch_failure_analysis`
