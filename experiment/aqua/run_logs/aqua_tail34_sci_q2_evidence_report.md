# AQuA Tail34 SCI-Q2 Goal Evidence Report

**Date:** 2026-07-08

## Goal Boundary

PromptNode must be treated as a first-class virtual MAS graph node: identity type, structured content, connection edges, read/write/forward permissions, budget, and lifecycle actions. R065 is useful evidence, but only partial compliance with that design.

**Update2 compliance:** `partial`

R065 gives a positive held-out accuracy signal for multi-view contract/objective selection, but generated_graph/ranked_variants contain 0 explicit PromptNode graph markers on tail34. It validates the selector direction, not yet the full update2 train-time virtual-node graph policy.

## Tail34 Result Table

| Variant | Overall | Clean | Noisy/Amb. | Delta | Fix/Harm | Clean F/H | Switches | PN graph hits | Cost | Cost/correct | Relative cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ARG baseline | `28/34` | `27/28` | `1/6` | `+0` | `0/0` | `0/0` | `0` | `0/34` | `$0.932850` | `$0.0333` | `1.00x` |
| PN router | `30/34` | `27/28` | `3/6` | `+2` | `3/1` | `1/1` | `5` | `0/34` | `$1.045305` | `$0.0348` | `1.12x` |
| PN candidate | `28/34` | `26/28` | `2/6` | `+0` | `1/1` | `0/1` | `4` | `0/34` | `$0.982645` | `$0.0351` | `1.05x` |
| PN conservative | `28/34` | `25/28` | `3/6` | `+0` | `3/3` | `1/3` | `7` | `0/34` | `$1.045870` | `$0.0374` | `1.12x` |
| PN calibrated | `29/34` | `26/28` | `3/6` | `+1` | `3/2` | `1/2` | `6` | `0/34` | `$1.044135` | `$0.0360` | `1.12x` |
| PN result ensemble | `31/34` | `28/28` | `3/6` | `+3` | `3/0` | `1/0` | `4` | `0/34` | `$5.050805` | `$0.1629` | `5.41x` |
| Objective-guided selector | `31/34` | `28/28` | `3/6` | `+3` | `3/0` | `1/0` | `4` | `0/34` | `$5.050805` | `$0.1629` | `5.41x` |
| Margin-3 objective selector | `28/34` | `27/28` | `1/6` | `+0` | `0/0` | `0/0` | `0` | `0/34` | `$5.050805` | `$0.1804` | `5.41x` |

## Cost-Normalized Reading

- Full multi-view execution cost: `$5.050805` for 34 tasks.
- Objective-guided selector and result ensemble are CPU-only after traces exist, but a deployable system must pay for baseline + four PN views unless we train/distill a cheaper graph policy.
- Objective-guided selector adds `+3` solved tasks over ARG with incremental cost per extra correct `$1.3727`.

## Objective Switch Cases

| Task | Audit | Outcome | Gold | ARG | Selected | Top score | Method predictions | Boundary |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| task_114 | noisy/unsupported/arithmetic_error | fix | D | C | D | 2 | ARG baseline=C, PN router=D, PN candidate=D, PN conservative=D, PN calibrated=D, PN result ensemble=D | accuracy switch uses multi-view contract evidence, but this record has no explicit PromptNode role in generated_graph/ranked_variants |
| task_59 | noisy/contradictory/arithmetic_error | neutral | C | B | D | 2 | ARG baseline=B, PN router=D, PN candidate=A, PN conservative=A, PN calibrated=D, PN result ensemble=D | accuracy switch uses multi-view contract evidence, but this record has no explicit PromptNode role in generated_graph/ranked_variants |
| task_108 | noisy/contradictory/arithmetic_error | fix | D | B | D | 2 | ARG baseline=B, PN router=D, PN candidate=C, PN conservative=D, PN calibrated=D, PN result ensemble=D | accuracy switch uses multi-view contract evidence, but this record has no explicit PromptNode role in generated_graph/ranked_variants |
| task_250 | clean/exact/none | fix | E | A | E | 3 | ARG baseline=A, PN router=E, PN candidate=A, PN conservative=E, PN calibrated=E, PN result ensemble=E | accuracy switch uses multi-view contract evidence, but this record has no explicit PromptNode role in generated_graph/ranked_variants |

## Claims Allowed Now

1. On AQuA tail34, multi-view objective-guided selection reaches `31/34` versus ARG `28/34`, with fix/harm `3/0` and clean fix/harm `1/0`.
2. The gain is not only noisy-label exploitation: the audited clean split is `28/28`, including one clean fix and zero clean harms.
3. The current positive signal is cost-heavy and only partially implements the update2 PromptNode design.

## Claims Not Allowed Yet

- Do not claim that R065 already trains PromptNode as a first-class virtual node.
- Do not claim general MAS improvement from one 34-task AQuA split.
- Do not hide the multi-view execution cost.

## Required Next Work

- Implement PromptNode as a first-class generated graph node with identity, edges, permissions, budget, and lifecycle labels.
- Train or distill a graph-policy/selector so the R065 signal is approximated without running all four PN views.
- Validate on MMLU STEM transfer or a larger AQuA held-out split with clean/noisy audit and cost normalization.
