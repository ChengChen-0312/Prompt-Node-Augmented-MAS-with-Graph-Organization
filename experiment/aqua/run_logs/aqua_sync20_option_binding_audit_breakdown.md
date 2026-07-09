# AQuA sync20 Option-Binding Audit

**Date**: 2026-07-08
**Audit model**: `gpt-4o-2024-08-06`
**Dataset slice**: AQuA `task_split_aqua.json` first 20 test indices
**Purpose**: Determine whether continued PromptNode optimization on sync20 is measuring clean reasoning gains or overfitting noisy option bindings.

## Final Audit Summary

The final audit is `aqua_sync20_option_binding_audit_v4.jsonl`.

| Clean label | Count |
| --- | ---: |
| clean | 17 |
| noisy | 3 |

| Rationale issue | Count |
| --- | ---: |
| none | 17 |
| arithmetic_error | 3 |

All 20 rows were audited with high confidence. The audit combines an LLM JSON judgment with a narrow deterministic check for explicit linear-equation arithmetic mistakes in the official rationale. The deterministic check is audit-only; it is not used by any answering model or accuracy computation.

## Noisy Rows

| Task | Gold | Issue | Audit reason |
| --- | --- | --- | --- |
| `task_152` | `C` | arithmetic error | Official rationale solves `120 = 8x` as `x=10`, but the equation gives `x=15`, which is not among the choices. |
| `task_199` | `A` | arithmetic error | Official rationale contains arithmetic errors in the probability calculation; the faithful answer is not supported by the visible derivation. |
| `task_172` | `E` | arithmetic error | Official rationale computes the total distance as `126 km` instead of the value needed to support the gold option. |

## Clean/Noisy Accuracy Split

| Method | Total accuracy | Clean accuracy | Noisy accuracy | Wrong clean rows | Wrong noisy rows |
| --- | ---: | ---: | ---: | --- | --- |
| ARG baseline | `17/20` | `17/17` | `0/3` | none | `task_152`, `task_199`, `task_172` |
| Router-contract PN trained | `17/20` | `17/17` | `0/3` | none | `task_152`, `task_199`, `task_172` |
| PN candidate graph selection | `17/20` | `17/17` | `0/3` | none | `task_152`, `task_199`, `task_172` |
| Selective PN v2 | `16/20` | `16/17` | `0/3` | `task_132` | `task_152`, `task_199`, `task_172` |

## Interpretation

ARG-Designer already achieves `17/17` on the clean portion of sync20. Therefore, an honest improvement beyond `17/20` on this exact slice would have to solve at least one audited noisy row. That is not a credible SCI Q2 main claim unless the paper explicitly studies robustness to noisy labels and separates dataset-noise behavior from mathematical correctness.

PromptNode variants did not improve clean accuracy on this slice. The strongest SCI-oriented next step is not another sync20 prompt patch; it is a larger clean/noisy evaluation on 100-200 AQuA rows, then a transfer benchmark such as GSM8K or MMLU math. The paper claim should be framed around clean-row generalization, noise awareness, and cost-accuracy tradeoffs rather than sync20-only accuracy.

