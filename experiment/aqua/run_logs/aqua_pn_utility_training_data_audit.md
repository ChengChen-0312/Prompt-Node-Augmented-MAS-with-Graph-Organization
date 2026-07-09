# PN Utility Classifier Training Data Audit

**Date**: 2026-07-08
**Purpose**: Check whether R028 can train a learned PN utility classifier without using AQuA test labels.

## Split Availability

`experiment/aqua/task_split_aqua.json` contains:

| Split field | Count |
| --- | ---: |
| `base_tasks_indices` | 8 |
| `finetune_tasks_indices` | 12 |
| `test_indices` | 234 |

Only 20 rows are available outside the test split. This is not enough to train a reliable learned utility classifier for deciding whether PN evidence should override, complement, or abstain from final aggregation.

## Calibration Check Already Run

The 20-row non-test calibration split produced:

| Run | Accuracy | Cost |
| --- | ---: | ---: |
| ARG baseline | `17/20` | `$0.500720` |
| R027 calibrated PN utility | `17/20` | `$0.658225` |

This small calibration check did not show improvement and is too small for a trained classifier.

## Verdict

R028 learned utility classifier is data-limited under the current split. Training it on the first 100 AQuA test labels would be leakage and cannot support a SCI Q2 claim. A valid learned gate would require collecting more non-test traces or defining a new train/dev/test split before evaluation.

