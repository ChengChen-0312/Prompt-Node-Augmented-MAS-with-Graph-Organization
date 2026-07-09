# R067 PromptNode Update2 Metadata Supervision Report

## Claim Boundary

R067 is a training-target and infrastructure result. It does not report AQuA answer accuracy.

The purpose is to close the gap identified by R066: R065 has a positive multi-view selector signal, but it does not yet prove that PromptNode is trained as a first-class virtual MAS graph node. R067 updates the R052/R053 graph-policy export so that positive graph targets include:

- PromptNode node identities
- read/write/forward permissions
- budget limits
- lifecycle actions
- edge-level permissions

This is closer to `/Users/chencheng/Downloads/论文/update2.docx` than role-only PN insertion.

## Update2 Mapping

| Code role | Paper identity type | Runtime behavior | Why this avoids the Router identity mistake |
| --- | --- | --- | --- |
| `PN_Memory` | Memory | shared_state | Memory is an identity type. |
| `PN_Verifier` | Instruction/Verifier | verify | Verifier is an identity type. |
| `PN_Router` | Agent-like | Router | Router is stored as runtime behavior, not as a PromptNode identity type. |

## Artifacts

| Artifact | Result |
| --- | --- |
| `experiment/aqua/aqua_first200_graph_policy_distill_rows.jsonl` | `800` policy rows |
| positive policy rows | `76` |
| positive PromptNode policy rows | `76` |
| positive PromptNode spec rows | `76` |
| positive PromptNode edge-permission rows | `76` |
| outcome-field violations | `0` |
| `experiment/FinetuneData_AQuA_PN_GraphPolicy_R053` | `76` ARGDesigner-compatible `.pt` files |
| PromptNode `.pt` files | `76` |
| PromptNode spec `.pt` files | `76` |
| PromptNode edge-permission `.pt` files | `76` |

## Training-Path Smoke

The updated `.pt` files were loaded through `AquaGraphDataset(pretrain=False)` and passed through ARGDesigner using the PromptNode-compatible checkpoint:

- base model: `experiment/aqua/output/aqua_pn_router_contract_model_20260708-030015`
- smoke output: `experiment/aqua/output/aqua_pn_graph_policy_r067_metadata_smoke`
- sampled graphs: `8`
- DAG check: `8/8`
- PromptNode roles present: `PN_Memory`, `PN_Router`, `PN_Verifier`
- forward finite loss: `True`
- forward loss: `246.7950`

## Interpretation

R067 provides a stronger method bridge for the SCI-Q2 plan:

1. R065 shows where multi-view contract/objective evidence can improve tail34 accuracy.
2. R066 shows R065 is too expensive and only partial update2 compliance.
3. R067 makes the train-time graph-policy data explicitly carry PromptNode identities, permissions, budgets, lifecycle actions, and edge permissions.

The next experiment should train or fine-tune a graph policy on these updated targets and evaluate a selective PromptNode system. Dense generated PromptNode execution is already rejected by R060, so the next accuracy run should not simply run every generated PN graph; it should include a selector/abstention policy.
