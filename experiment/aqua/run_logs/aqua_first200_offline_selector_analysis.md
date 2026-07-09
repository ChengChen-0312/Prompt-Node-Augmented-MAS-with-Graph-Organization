# AQuA First200 Offline PN Utility Selector Analysis

**Date**: 2026-07-08
**Slices**: first100 + next100 from `task_split_aqua.json`
**Input systems**: ARG baseline, PN router-contract, PN candidate selection, PN conservative router, PN calibrated utility, PN result ensemble
**LLM/API use**: none; this is a replay over existing `gpt-4o-2024-08-06` result files

## Raw Data Table

| Replay | Train Slice | Test Slice | Learned Rule | Selector | Baseline | Ensemble | Delta vs Baseline | Switches | Fix/Harm |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cross-slice A | `aqua_100` | `aqua_next100` | `ensemble_if_baseline_invalid` | `85/100` | `82/100` | `85/100` | `+3` | `5` | `3/0` |
| Cross-slice B | `aqua_next100` | `aqua_100` | `ensemble_if_baseline_invalid` | `86/100` | `83/100` | `85/100` | `+3` | `6` | `3/0` |
| Combined replay | same rule | first200 | `ensemble_if_baseline_invalid` | `171/200` | `165/200` | `170/200` | `+6` | `11` | `6/0` |

Both cross-slice directions independently select the same rule. The rule does not inspect task IDs, gold labels, clean/noisy status, or rationales at inference time. It switches to the PN ensemble only when the ARG baseline parsed prediction is not a valid `A`-`E` option.

## Clean/Noisy Breakdown

| Method | Overall | Clean | Noisy/Ambiguous |
| --- | ---: | ---: | ---: |
| ARG baseline | `165/200` | `152/167` | `13/33` |
| PN result ensemble | `170/200` | `154/167` | `16/33` |
| Offline selector | `171/200` | `153/167` | `18/33` |

The selector's official-score gain is concentrated in noisy/ambiguous rows. It improves clean rows by only `+1/167` over ARG baseline, while the PN result ensemble improves clean rows by `+2/167`.

## Switched Rows

| Task | Slice | Audit Label | Gold | Baseline | Ensemble | Selector Correct |
| --- | --- | --- | --- | --- | --- | --- |
| `task_152` | `aqua_100` | noisy | `C` | `None` | `E` | no |
| `task_135` | `aqua_100` | noisy | `D` | `None` | `D` | yes |
| `task_112` | `aqua_100` | noisy | `C` | `None` | `D` | no |
| `task_146` | `aqua_100` | noisy | `B` | `None` | `B` | yes |
| `task_106` | `aqua_100` | clean | `D` | `None` | `D` | yes |
| `task_32` | `aqua_100` | clean | `B` | `None` | `A` | no |
| `task_162` | `aqua_next100` | noisy | `A` | `None` | `A` | yes |
| `task_232` | `aqua_next100` | noisy | `E` | `None` | `E` | yes |
| `task_20` | `aqua_next100` | noisy | `C` | `None` | `E` | no |
| `task_117` | `aqua_next100` | noisy | `C` | `None` | `A` | no |
| `task_207` | `aqua_next100` | noisy | `C` | `None` | `C` | yes |

## Paired Check

Against ARG baseline on first200, the selector has `6` fixes and `0` harms, giving a two-sided exact binomial/McNemar-style p-value of `0.03125` on the official labels. On audited clean rows only, it has `1` fix and `0` harms, so there is no meaningful statistical support for a clean-math improvement.

## Interpretation

1. The offline selector converts part of the PN ensemble signal into a more stable official-label improvement (`171/200`) than the plain result ensemble (`170/200`).
2. The selected rule is not a deep learned utility model. It is an answer-space validity gate: if ARG-Designer abstains or says the answer is not in the options, fall back to PN consensus.
3. This is useful engineering evidence but weak paper evidence. Most gains come from AQuA rows that the audit marked noisy or contradictory, so the result should not be used as the main SCI claim.
4. For a publishable method, the next selector must use richer runtime features before the final answer is malformed: direct-agent agreement, PN verifier confidence, option-binding status, graph role coverage, and cost-aware abstention. It must be validated on tail34 or another held-out multiple-choice benchmark after API quota is restored.

## Result-To-Claim Verdict

- **claim_supported**: partial
- **what_results_support**: A label-free-at-inference fallback selector can raise official first200 AQuA accuracy from `165/200` to `171/200` by using PN ensemble predictions only when ARG-Designer emits an invalid option.
- **what_results_do_not_support**: This does not yet support a strong SCI Q2 claim that PromptNode reasoning improves clean mathematical accuracy. Clean-row gain is only `+1/167` over ARG baseline.
- **recommended_claim_revision**: "PromptNode virtual nodes are most useful when treated as a constrained option-binding fallback; future work must learn a richer utility selector that improves clean rows without relying on noisy-label recovery."
