# R208 Negative Controls And Ablation Plan

**Claim boundary**: protocol only. No API evaluation and no new accuracy claim.

The purpose of R208 is to prevent the paper from becoming "we added virtual nodes and got lucky." The controls must separate structure, prompt budget, learned activation, router-final decisions, and cost.

## Main Questions

| Question | Required Evidence |
|---|---|
| Do PromptNodes help beyond extra prompt tokens? | compare against random PromptNode text and cost-matched ARG re-query |
| Do PromptEdges matter? | compare PN-only, PE-only, and PN+PE variants |
| Does ordering matter? | compare canonical `PN_Memory -> PN_Verifier -> PN_Router` against shuffled order |
| Does router-final safely change answers? | report fix/harm and clean fix/harm, not only accuracy |
| Is the method robust? | evaluate AQuA and MMLU with no tuning on target rows |

## Negative Controls

| Control | Why It Matters | Expected Failure Mode |
|---|---|---|
| Random PromptNode text | controls for more tokens and extra reasoning turn | no reliable improvement |
| Shuffled PromptEdge order | tests whether the PN chain semantics matter | weaker verification/routing |
| Node-only, no PromptEdge | tests whether virtual nodes alone are enough | poorer communication semantics |
| Edge-only prompt, no PromptNode | tests whether prompt-as-edge alone explains gains | brittle unless agents already expose evidence |
| Always insert PN/PE | tests indiscriminate insertion | higher cost and possible clean harms |
| Cost-matched ARG re-query | controls for simply spending more model calls | proposed method must beat this or be cheaper |
| Leakage scan | protects paper integrity | zero task-id/gold/correctness/audit-label inputs |

## Ablation Ladder

| Variant | What It Proves If Positive |
|---|---|
| ARG baseline | baseline reproduction |
| Raw learned PN/PE graph | whether ML learns topology without projection |
| Projected PN/PE structure only | whether valid graph structure is enough |
| Projected PN/PE + router-final | whether PN evidence can safely change answers |
| PN+PE with prompt carried by edge text | whether prompts as edges improve routing |
| Distilled objective-safety selector | whether AQuA R065/R095 signal can be made cheaper |
| Cost-matched ARG re-query | whether gains are not just extra budget |

## Dataset Protocol

| Dataset | Role |
|---|---|
| AQuA sync20 R001 | baseline breakdown and same-model reproduction only |
| AQuA first200 | allowed training/distillation source for selector features |
| AQuA tail34 | held-out validation, with clean/noisy audit |
| MMLU transfer100/random slices | transfer and robustness, no tuning on selected rows |

## Metrics

Report all of these together:

- accuracy and accuracy delta versus ARG
- clean accuracy and clean fix/harm
- overall fix/harm
- raw versus projected contract-ready rate
- selection/switch rate
- cost per correct and incremental cost per fix
- leakage violations
- task-level switch table

## Go/No-Go Before New API

R210 may allow a new API run only if:

- all selected inputs exclude gold labels, correctness, audit labels, and task ids;
- dry-run logs raw graph, projected graph, PN roles, PromptEdge permissions, and router-final output separately;
- the cost cap is explicit;
- success and failure criteria are pre-registered.

Stop or redesign if:

- random/shuffled controls match the proposed method;
- router-final introduces clean harm;
- MMLU remains neutral after router-final redesign;
- cost-matched ARG re-query is as good as the proposed method.

## Paper Use

These controls let the paper argue mechanism, not just outcome. Without them, only the narrow AQuA R065 result is defensible, and the method remains too close to prompt engineering for an SCI-Q2 target.
