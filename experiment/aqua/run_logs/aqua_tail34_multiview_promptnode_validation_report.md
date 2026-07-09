# AQuA Tail34 Multi-View PromptNode Validation Report

## Boundary

This report uses the pre-registered AQuA tail34 split and the same LLM setting used for the ARG-Designer reproduction: `gpt-4o-2024-08-06`.

The multi-view PromptNode traces use `output/aqua_pn_router_contract_model_20260708-030015`, matching the earlier R035/R038 first200 mechanism line. This is different from the later R055 graph-policy checkpoint. The result therefore validates the multi-view PromptNode contract/objective direction, not the dense R055 graph-policy direction.

The selector summaries use `true_answer` and the option-binding audit only for post-hoc evaluation. The selector itself uses label-free PromptNode/direct-agent contract features.

## Raw Tail34 Results

| Variant | Accuracy | Delta vs ARG | Fix/Harm vs ARG | Switches vs ARG | Cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| R059 ARG baseline | `28/34` | `+0` | `0/0` | `0` | `$0.932850` |
| PN router-contract view | `30/34` | `+2` | `3/1` | `5` | `$1.045305` |
| PN candidate-graph view | `28/34` | `+0` | `1/1` | `4` | `$0.982645` |
| PN conservative-router view | `28/34` | `+0` | `3/3` | `7` | `$1.045870` |
| PN calibrated-utility view | `29/34` | `+1` | `3/2` | `6` | `$1.044135` |
| Result-level multi-view ensemble | `31/34` | `+3` | `3/0` | `4` | `post-hoc over above views` |
| R035 strict multi-contract only | `28/34` | `+0` | `0/0` | `0` | `replay` |
| R035 strict multi-contract + invalid fallback | `28/34` | `+0` | `0/0` | `0` | `replay` |
| Objective-guided selector, margin `0` | `31/34` | `+3` | `3/0` | `4` | `replay over above views` |
| Objective-guided selector, margin `3` | `28/34` | `+0` | `0/0` | `0` | `replay` |

Switch tasks for the objective-guided selector are `task_114`, `task_59`, `task_108`, and `task_250`. It fixes `task_114`, `task_108`, and `task_250`; `task_59` remains wrong, so it is not counted as a harm.

## Option-Binding Audit

The tail34 option-binding audit contains `34/34` rows.

| Audit field | Result |
| --- | ---: |
| Clean rows | `28` |
| Noisy rows | `6` |
| Exact gold binding | `28` |
| Contradictory gold binding | `5` |
| Unsupported gold binding | `1` |
| High-confidence audit rows | `34` |

With this audit, the objective-guided selector reaches:

| Split | Accuracy | Fix/Harm vs ARG |
| --- | ---: | ---: |
| Overall | `31/34` | `3/0` |
| Clean | `28/28` | `1/0` |
| Noisy/Ambiguous | `3/6` | `2/0` |

This matters for the paper: the tail34 gain is not only noisy-label exploitation. There is one clean fix without observed clean harm.

## Interpretation

The dense R055 graph-policy PromptNode path failed tail34, but the older multi-view PromptNode contract path now has a positive tail34 signal. The strongest current tail34 result is the label-free objective-guided selector: `31/34` overall, clean `28/28`, and fix/harm `3/0`.

R035 strict multi-contract union does not transfer to tail34 because its thresholds are too conservative and produce no switches. The useful rule is the R038/R039 objective-guided unique-top selector with margin `0`; the R040 margin `3` selector is too conservative on tail34.

## Paper Implication

For an SCI Q2-oriented paper, the viable story is now:

1. PromptNodes are first-class graph-organization units, not answer patches.
2. Single dense PromptNode execution can harm performance, so the paper must include it as a negative control.
3. Multi-view PromptNode contracts/objectives can identify safe answer-changing situations.
4. Tail34 provides prospective evidence that objective-guided PromptNode selection can exceed ARG-Designer on both official accuracy and audited clean accuracy.

The remaining weakness is cost and system form. The current objective selector consumes multiple PromptNode views, so cost-normalized evaluation and a train-time graph-policy version are still needed before claiming a mature practical system.

## Sources

- ARG baseline: `experiment/aqua/aqua_tail34_arg_baseline_results.jsonl`
- Multi-view traces: `experiment/aqua/aqua_tail34_pn_router_contract_results.jsonl`, `experiment/aqua/aqua_tail34_pn_candidate_select_results.jsonl`, `experiment/aqua/aqua_tail34_pn_conservative_router_results.jsonl`, `experiment/aqua/aqua_tail34_pn_calibrated_utility_results.jsonl`
- Ensemble: `experiment/aqua/aqua_tail34_pn_result_ensemble_results.jsonl`
- Objective selector: `experiment/aqua/aqua_tail34_objective_guided_selector_results.jsonl`
- Margin selector: `experiment/aqua/aqua_tail34_margin3_objective_guided_selector_results.jsonl`
- Audit: `experiment/aqua/aqua_tail34_option_binding_audit.jsonl`
