# R323 Selector Model Dry Run

**Claim boundary**: R323 trains a transparent no-API selector only on the R322 manifest. It is a feasibility dry run, not a paper claim and not an API execution authorization.

- Learned policy: `{'model_type': 'transparent_family_whitelist_selector', 'allowed_promptnode_families': ['nonmath_semantic', 'symbolic_verifier'], 'min_candidate_confidence': 1.0, 'requires_candidate_answer_label': True, 'forbidden_promptnode_families': ['none', 'warning_only'], 'train_family_counts': {'none': {'negative': 143}, 'nonmath_semantic': {'positive': 2}, 'symbolic_verifier': {'positive': 3}, 'warning_only': {'negative': 16}}, 'forbidden_features_excluded': ['task_id', 'question', 'true_answer', 'predicted_answer', 'arg_prediction', 'is_correct', 'fix', 'harm']}`
- Forwarded warning-only count: `0`
- Feature leakage pass: `True`

## Metrics

| Split | Records | Accuracy | Target Forward | Predicted Forward | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| `train` | `164` | `1.0` | `5` | `5` | `1.0` | `1.0` |
| `dev` | `24` | `1.0` | `1` | `1` | `1.0` | `1.0` |
| `test` | `46` | `1.0` | `1` | `1` | `1.0` | `1.0` |

- Next required run: `R324_selector_feature_ablation`
