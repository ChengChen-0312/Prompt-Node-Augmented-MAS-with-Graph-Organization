# R324 Selector Feature Ablation

**Claim boundary**: R324 tests whether the R323 dry-run result identifies real feature contributions. Because several easy ablations tie the full selector, the current manifest needs hard negative answer-bearing candidates before a training claim.

| Variant | Test Accuracy | Test Precision | Test Recall | False Forward | Missed Forward |
|---|---:|---:|---:|---:|---:|
| `full_structural_selector` | `1.0` | `1.0` | `1.0` | `0` | `0` |
| `remove_promptnode_family` | `1.0` | `1.0` | `1.0` | `0` | `0` |
| `remove_candidate_answer_label` | `1.0` | `1.0` | `1.0` | `0` | `0` |
| `confidence_only` | `1.0` | `1.0` | `1.0` | `0` | `0` |
| `random_same_forward_budget` | `0.9565217391304348` | `0.0` | `0.0` | `1` | `1` |

- Hard negative gap detected: `True`
- PromptEdge feature contribution identified: `False`
- Next required run: `R325_hard_negative_augmentation_protocol`
