# R325 Hard Negative Augmentation Protocol

**Claim boundary**: R325 augments the selector manifest with answer-bearing false-forward cases mined from R316 controls. It prepares a harder offline retraining set but does not authorize API execution or paper claims.

- Base manifest records: `234`
- Hard negative records: `4`
- Augmented manifest records: `238`
- Hard negative variants: `['node_only_no_promptedge_text', 'plain_requery']`
- Feature leakage pass: `True`
- Next required run: `R326_goal_audit_after_selector_pretraining`
