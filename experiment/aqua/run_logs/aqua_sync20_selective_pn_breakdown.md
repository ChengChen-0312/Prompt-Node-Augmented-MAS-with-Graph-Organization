# AQuA sync20 Selective PromptNode Routing Breakdown

Date: 2026-07-08

## Purpose

Test R022: a selective PromptNode final gate that can compare direct agent
evidence with `PN_Router` contracts and activate an Agent-like audit only under
conflict or option-binding risk.

This implements the lifecycle idea from `update2.docx` at the final-decision
layer:

- Memory: preserve direct and PN evidence separately.
- Verifier: audit target preservation and option binding.
- Router: decide whether to accept direct evidence, use PN evidence, or escalate.
- Agent-like Prompt Node: audit only when conflict/risk appears.

## Code Changes

- Added decision method: `SelectivePromptNodeFinalRefer`
- Added eval arg: `--decision_exposure_policy auto|all|terminal`
- Added tests:
  - `tests/test_selective_prompt_node_final.py`
  - updated `tests/test_prompt_node_pyg_pipeline.py`

## Evaluation Setup

- Model: `output/aqua_pn_router_contract_model_20260708-030015`
- LLM: `gpt-4o-2024-08-06`
- Topology policy: `canonicalize_generated`
- Decision exposure: `all`
- Split: AQuA sync20

Command used for v2:

```bash
../../.venv/bin/python evaluate_aqua.py \
  --model_path output/aqua_pn_router_contract_model_20260708-030015 \
  --llm_name gpt-4o-2024-08-06 \
  --decision_method SelectivePromptNodeFinalRefer \
  --output_file aqua_sync20_selective_pn_v2_results.jsonl \
  --summary_log_file ./res_logs/aqua_sync20_selective_pn_v2_summary.jsonl \
  --limit 20 \
  --eval_batch_size 4 \
  --prompt_node_policy none \
  --prompt_node_topology_policy canonicalize_generated \
  --decision_exposure_policy all
```

## Results

| Run | Accuracy | Cost | PN Graphs | Notes |
| --- | ---: | ---: | ---: | --- |
| ARG baseline | `17/20` | `$0.508365` | `0/20` | baseline |
| Router-contract trained | `17/20` | `$0.634350` | `11/20` | tied baseline |
| Selective PN v1 | `17/20` | `$0.750860` | `11/20` | invalid apparent fix; `The answer is NONE` parsed as `E` |
| Selective PN v2 | `16/20` | `$0.758515` | `11/20` | parser artifact removed |

## Selective v2 Details

- `PN_ACTION`: `USE_ROUTER=9`, `ESCALATE_AGENTLIKE=2`
- `BINDING_STATUS`: `EXACT_MATCH=8`, `EQUIVALENT_FORM=1`, `NO_EXACT_OPTION=2`
- `NOISE_RISK`: `LOW=9`, `MEDIUM=1`, `HIGH=1`
- Invalid final `NONE`: `0`

Wrong rows:

| Task | Gold | Baseline Pred | Selective v2 Pred | Note |
| --- | --- | --- | --- | --- |
| `task_152` | `C` | `E` | `E` | unchanged noisy/option-mismatch row |
| `task_199` | `A` | `C` | `C` | unchanged |
| `task_172` | `E` | `C` | `A` | still wrong after Agent-like escalation |
| `task_132` | `B` | `B` | `D` | new harm |

## Parser Artifact

Selective v1 produced `The answer is NONE` on two rows. The existing AQuA parser
extracts uppercase letters from non-singleton answer strings, so `NONE` can be
misread as option `E`. This is not a valid accuracy gain and must not be used as
evidence.

Selective v2 explicitly forbids `The answer is NONE`, and the score drops to
`16/20`.

## Verdict

- `claim_supported`: no
- Selective final-prompt routing does not exceed ARG-Designer.
- It can expose conflict/noise, but without a learned graph-level selection
  mechanism it still introduces harms.

## Next Direction

Move the virtual-node mechanism earlier than final prompting:

1. Generate multiple candidate ARG/PN graph organizations.
2. Use Prompt Nodes to score graph-level risk/benefit before execution or before
   final aggregation.
3. Select the candidate graph, not just the final answer.

This better matches the paper idea: Prompt Nodes should participate in graph
organization and lifecycle control, not merely rewrite the final decision.
