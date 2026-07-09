# AQuA 100 Result-Level PN Ensemble

**Date**: 2026-07-08
**Dataset slice**: first 100 AQuA test indices from `task_split_aqua.json`
**Purpose**: Exploratory check whether PromptNode runs contain complementary evidence to ARG-Designer without using labels inside the prediction rule.

## Ensemble Rule

The script `experiment/aqua/ensemble_results.py` combines existing result JSONL files by majority vote over valid A-E predictions.

Method order:

1. `baseline`: `aqua_100_arg_baseline_results.jsonl`
2. `router`: `aqua_100_pn_router_contract_results.jsonl`
3. `candidate`: `aqua_100_pn_candidate_select_results.jsonl`
4. `conservative`: `aqua_100_pn_conservative_router_results.jsonl`
5. `calibrated`: `aqua_100_pn_calibrated_utility_results.jsonl`

Tie-breaker: `baseline`.

This is a label-free aggregation rule, but it is exploratory because it was constructed after several AQuA100 runs already existed. It needs held-out validation before it can become a paper claim.

## Result

| Method | Total | Clean | Noisy |
| --- | ---: | ---: | ---: |
| ARG baseline | `83/100` | `77/85` | `6/15` |
| PN result ensemble | `85/100` | `79/85` | `6/15` |

sync20 subset: `17/20`, tied with ARG baseline. The ensemble does not solve the three noisy sync20 rows.

## Fix/Harm Against ARG Baseline

| Type | Task | Clean label | Gold | ARG pred | Ensemble pred |
| --- | --- | --- | --- | --- | --- |
| FIX | `task_135` | noisy | `D` | `None.` | `D` |
| FIX | `task_122` | clean | `A` | `C` | `A` |
| HARM | `task_0` | noisy | `A` | `A` | `E` |
| FIX | `task_146` | noisy | `B` | `None.` | `B` |
| FIX | `task_106` | clean | `D` | `None.` | `D` |
| HARM | `task_198` | noisy | `C` | `C` | `A` |

Net effect: +2 clean rows and 0 noisy-row net change.

## Interpretation

This is the first larger-slice result showing a clean-row gain over ARG-Designer: `79/85` vs `77/85`. However, it does not satisfy the original sync20 target and is not yet a publishable claim because it is result-level exploratory aggregation over existing runs. The next step is a pre-registered held-out ensemble evaluation, preferably on the remaining AQuA test rows or a transfer dataset.

