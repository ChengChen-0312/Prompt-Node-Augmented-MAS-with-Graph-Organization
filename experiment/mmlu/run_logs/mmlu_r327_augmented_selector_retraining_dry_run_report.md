# R327 Augmented Selector Retraining Dry Run

**Claim boundary**: R327 retrains the transparent selector on the hard-negative augmented manifest. It identifies PromptEdge text as a safety feature in the offline manifest, but it is still not an API or paper-result claim.

- Learned policy: `{'model_type': 'augmented_promptedge_aware_family_selector', 'allowed_promptnode_families': ['nonmath_semantic', 'symbolic_verifier'], 'min_candidate_confidence': 0.95, 'requires_candidate_answer_label': True, 'requires_promptedge_text_present': True, 'forbidden_promptnode_families': ['answer_bearing_no_promptedge_text', 'none', 'warning_only'], 'train_family_counts': {'answer_bearing_no_promptedge_text': {'negative': 2}, 'none': {'negative': 143}, 'nonmath_semantic': {'positive': 2}, 'symbolic_verifier': {'positive': 3}, 'warning_only': {'negative': 16}}}`
- Forwarded hard negatives: `0`
- PromptEdge contribution identified: `True`

## Feature Ablation

| Variant | Test Accuracy | Test Precision | Test Recall | False Forward | Missed Forward |
|---|---:|---:|---:|---:|---:|
| `full_augmented_selector` | `1.0` | `1.0` | `1.0` | `0` | `0` |
| `no_family_no_promptedge_text_feature` | `0.9787234042553191` | `0.5` | `1.0` | `1` | `0` |
| `no_family_with_promptedge_text_feature` | `1.0` | `1.0` | `1.0` | `0` | `0` |

- Next required run: `R328_selector_policy_claim_update`
