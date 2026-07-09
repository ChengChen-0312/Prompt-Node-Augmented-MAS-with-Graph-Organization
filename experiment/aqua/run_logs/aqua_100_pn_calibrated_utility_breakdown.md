# AQuA 100 Calibrated PN Utility Gate

**Date**: 2026-07-08
**Dataset slice**: first 100 AQuA test indices from `task_split_aqua.json`
**Calibration slice**: 20 non-test rows from `base_tasks_indices + finetune_tasks_indices`
**LLM**: `gpt-4o-2024-08-06`
**PromptNode model**: `output/aqua_pn_router_contract_model_20260708-030015`
**Decision method**: `CalibratedPNUtilityFinalRefer`

## Method

`CalibratedPNUtilityFinalRefer` extracts ordinary-agent votes and PN router contracts before final aggregation. It returns a deterministic answer only for clear utility cases:

1. ordinary agents have at least two matching A-E votes and all PN contracts are weak;
2. ordinary agents have at least two matching A-E votes and strong PN contracts conflict with that majority;
3. ordinary agents provide no valid A-E votes and exactly one strong PN-supported option exists.

All other cases fall back to `ConservativeRouterContractFinalRefer`.

The method uses no task ids, test labels, gold answers, or noisy-label patches.

## Calibration Check

| Run | Split | Accuracy | Cost |
| --- | --- | ---: | ---: |
| ARG baseline | calibration20 | `17/20` | `$0.500720` |
| Calibrated PN utility | calibration20 | `17/20` | `$0.658225` |

The calibration split did not show an obvious negative signal, but it also did not show improvement.

## AQuA 100 Results

| Method | Total | Clean | Noisy | Cost |
| --- | ---: | ---: | ---: | ---: |
| ARG baseline | `83/100` | `77/85` | `6/15` | `$2.368215` |
| Conservative PN router | `82/100` | `77/85` | `5/15` | `$3.397410` |
| Calibrated PN utility | `79/100` | `73/85` | `6/15` | `$3.342645` |

Against ARG baseline, calibrated utility PN had 3 fixes and 7 harms:

| Split | Fixes | Harms |
| --- | ---: | ---: |
| clean | 0 | 4 |
| noisy | 3 | 3 |

Changed rows:

| Type | Task | Clean label | Gold | ARG pred | R027 pred |
| --- | --- | --- | --- | --- | --- |
| HARM | `task_132` | clean | `B` | `B` | `E` |
| HARM | `task_79` | clean | `D` | `D` | `C` |
| FIX | `task_135` | noisy | `D` | `None.` | `D` |
| FIX | `task_10` | noisy | `B` | `C` | `B` |
| HARM | `task_200` | clean | `B` | `B` | `A` |
| HARM | `task_77` | noisy | `B` | `B` | `C` |
| HARM | `task_0` | noisy | `A` | `A` | `E` |
| HARM | `task_217` | clean | `A` | `A` | `D` |
| FIX | `task_146` | noisy | `B` | `None.` | `B` |
| HARM | `task_198` | noisy | `C` | `C` | `A` |

## Trigger Analysis

| Gate path | Correct | Total |
| --- | ---: | ---: |
| fallback LLM | `76` | `91` |
| PN without direct votes | `3` | `4` |
| direct over conflicting PN | `0` | `2` |
| direct over weak PN | `0` | `3` |

The deterministic majority guard did not generalize on this new run. It created clean harms and reduced clean accuracy from `77/85` to `73/85`.

## Interpretation

R027 fails the paper gate. A hand-written utility rule is not a reliable substitute for a learned or better-calibrated utility model. The result strengthens the negative conclusion: virtual nodes alone, plus rule-based evidence gating, do not yet exceed ARG-Designer under the same model setting.

The next iteration should collect training-split traces and train a small utility classifier, or redesign the graph generator so PN nodes produce lower-variance, verifiable evidence before final aggregation.

