# R322 Selector Training Preflight

**Claim boundary**: R322 freezes an offline graph-policy selector manifest. It authorizes only the next no-API dry run, not API execution or paper claims.

- Manifest records: `234`
- Positive forward targets: `7`
- Split counts: `{'test': 46, 'train': 164, 'dev': 24}`
- Positive split counts: `{'train': 5, 'dev': 1, 'test': 1}`
- PromptNode family counts: `{'none': 201, 'symbolic_verifier': 5, 'warning_only': 26, 'nonmath_semantic': 2}`
- Feature leakage pass: `True`
- Offline selector training authorized next: `True`
- API execution authorized next: `False`
- Next required run: `R323_selector_model_dry_run`
