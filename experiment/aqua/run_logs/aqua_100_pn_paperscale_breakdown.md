# AQuA 100 Paper-Scale PromptNode Validation

**Date**: 2026-07-08
**Dataset slice**: first 100 AQuA test indices from `task_split_aqua.json`
**LLM**: `gpt-4o-2024-08-06`
**Baseline model**: `output/aqua_sync20_model_20260707-230509`
**PromptNode model**: `output/aqua_pn_router_contract_model_20260708-030015`

## Runs

| Run | Accuracy | Cost | Prompt tokens | Completion tokens | Result file |
| --- | ---: | ---: | ---: | ---: | --- |
| ARG baseline + `FinalRefer` | `83/100` | `$2.368215` | `181236` | `97469` | `aqua_100_arg_baseline_results.jsonl` |
| PN router-contract + `RouterContractFinalRefer` | `78/100` | `$3.415440` | `266919` | `138723` | `aqua_100_pn_router_contract_results.jsonl` |
| PN candidate selection + `RouterContractFinalRefer` | `79/100` | `$3.830860` | `319559` | `148871` | `aqua_100_pn_candidate_select_results.jsonl` |

The candidate-selection run sampled exactly 4 candidate graphs per task. At least one PN graph was available for `97/100` tasks, and the selector chose a PN graph for `97/100` tasks.

## Automated Option-Binding Audit

Audit file: `aqua_100_option_binding_audit.jsonl`

| Label | Count |
| --- | ---: |
| clean | 85 |
| noisy | 15 |

The audit is automated and should be manually spot-checked before paper submission. It is still useful for gating method development because it prevents sync20-style noisy-label chasing from being treated as mathematical improvement.

## Clean/Noisy Accuracy

| Method | Total | Clean rows | Noisy rows |
| --- | ---: | ---: | ---: |
| ARG baseline | `83/100` | `77/85` | `6/15` |
| PN router-contract | `78/100` | `73/85` | `5/15` |
| PN candidate selection | `79/100` | `76/85` | `3/15` |

95% Wilson intervals:

| Method / split | Accuracy | 95% Wilson CI |
| --- | ---: | ---: |
| ARG baseline total | `83/100` | `74.5% - 89.1%` |
| PN candidate total | `79/100` | `70.0% - 85.8%` |
| ARG baseline clean | `77/85` | `82.5% - 95.2%` |
| PN candidate clean | `76/85` | `81.1% - 94.3%` |

Paired exact McNemar/binomial tests are not significant, but the direction is negative for PN: candidate selection fixes 1 baseline error and harms 5 baseline-correct rows; router-contract fixes 4 and harms 9.

## Fix/Harm Analysis

### PN Candidate Selection

| Type | Count | Clean | Noisy |
| --- | ---: | ---: | ---: |
| Baseline wrong, PN correct | 1 | 1 | 0 |
| Baseline correct, PN wrong | 5 | 2 | 3 |

Clean fix:

- `task_122`: gold `A`, baseline `C`, PN candidate `A`.

Clean harms:

- `task_95`: gold `A`, baseline `A`, PN candidate `B`.
- `task_79`: gold `D`, baseline `D`, PN candidate `A`.

Noisy harms:

- `task_0`: gold `A`, baseline `A`, PN candidate `E`.
- `task_157`: gold `D`, baseline `D`, PN candidate `E`.
- `task_198`: gold `C`, baseline `C`, PN candidate `A`.

### PN Router-Contract

| Type | Count | Clean | Noisy |
| --- | ---: | ---: | ---: |
| Baseline wrong, PN correct | 4 | 2 | 2 |
| Baseline correct, PN wrong | 9 | 6 | 3 |

Clean fixes:

- `task_122`: gold `A`, baseline `C`, router `A`.
- `task_106`: gold `D`, baseline `None.`, router `D`.

Clean harms:

- `task_61`: gold `D`, baseline `D`, router `E`.
- `task_211`: gold `A`, baseline `A`, router `C`.
- `task_85`: gold `A`, baseline `A`, router `E`.
- `task_200`: gold `B`, baseline `B`, router `D`.
- `task_175`: gold `B`, baseline `B`, router `C`.
- `task_140`: gold `E`, baseline `E`, router `C`.

## Interpretation

This 100-row validation falsifies the current PromptNode-as-virtual-node design as a main SCI Q2 result. The method is structurally aligned with the user's design goal because PN nodes are generated/executed as graph nodes rather than appended after the answer, but accuracy is lower and cost is higher than ARG-Designer.

The next method iteration should not be another final-answer prompt patch. It needs a substantive algorithmic change, such as supervised uncertainty routing, graph-level evidence selection, or a confidence-preserving PN gate that can abstain from influencing final aggregation when router/verifier evidence is low quality.

