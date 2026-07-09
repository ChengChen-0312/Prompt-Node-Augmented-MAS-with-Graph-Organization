# AQuA 100 Conservative PromptNode Gate

**Date**: 2026-07-08
**Dataset slice**: first 100 AQuA test indices from `task_split_aqua.json`
**LLM**: `gpt-4o-2024-08-06`
**PromptNode model**: `output/aqua_pn_router_contract_model_20260708-030015`

## Method Change

`ConservativeRouterContractFinalRefer` was added as a confidence-preserving PN gate. It only lets PN router contracts drive the final decision when the contract has:

- `SUPPORTED_OPTION` in `A-E`
- `BINDING_STATUS` in `EXACT_MATCH`, `EQUIVALENT_FORM`, or `EQUIVALENT`

If all router contracts are weak, for example `NO_EXACT_OPTION`, `UNSUPPORTED_LABEL`, or `CONFLICT`, the gate abstains and falls back to non-PN agent evidence. This does not use gold labels or task-specific patches.

## Results

| Method | Total | Clean | Noisy | Cost |
| --- | ---: | ---: | ---: | ---: |
| ARG baseline | `83/100` | `77/85` | `6/15` | `$2.368215` |
| PN router-contract | `78/100` | `73/85` | `5/15` | `$3.415440` |
| PN candidate selection | `79/100` | `76/85` | `3/15` | `$3.830860` |
| Conservative PN router | `82/100` | `77/85` | `5/15` | `$3.397410` |
| Conservative PN candidate | `82/100` | `77/85` | `5/15` | `$3.914520` |

## Fix/Harm Against ARG Baseline

| Method | Fixes | Harms | Clean fixes | Clean harms | Noisy fixes | Noisy harms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PN router-contract | 4 | 9 | 2 | 6 | 2 | 3 |
| PN candidate selection | 1 | 5 | 1 | 2 | 0 | 3 |
| Conservative PN router | 3 | 4 | 3 | 3 | 0 | 1 |
| Conservative PN candidate | 2 | 3 | 1 | 1 | 1 | 2 |

The conservative gate substantially reduces PN harm and recovers clean accuracy to the ARG baseline level. It still does not exceed ARG-Designer and remains more expensive.

## Interpretation

The conservative gate is a useful design correction, not a successful main result. It validates the diagnosis that weak PN evidence was perturbing final aggregation, but a rule-based abstention policy is insufficient to produce a publishable accuracy gain.

For a SCI Q2-oriented method, the next iteration should train or calibrate the PN gate on the training split. The gate should predict whether PN evidence is likely to fix, harm, or abstain using features available before the final answer, such as binding status, verifier conflict, agreement among agents, graph score, and PN/router confidence.

