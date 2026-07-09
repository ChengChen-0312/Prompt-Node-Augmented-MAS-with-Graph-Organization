# R206 Method Redesign After MMLU Random12

**Claim boundary**: design memo only. No API evaluation, no new accuracy claim, and no claim that the current MMLU PromptEdge system exceeds ARG-Designer.

## What The Evidence Says

The current evidence splits into two different strengths.

| Evidence | Positive Signal | Limitation |
|---|---:|---|
| AQuA R065 objective-guided multi-view | `31/34` vs ARG `28/34`; clean `28/28`; fix/harm `3/0` | replay over expensive multi-view traces; no explicit PromptNode graph markers |
| MMLU R188 learned PN graph | any PN `50/50`, terminal router `42/50` | contract-ready only `2/50`; PN chain only `2/50` |
| MMLU R189 projection | projected contract-ready `50/50` | hybrid constrained decoder, not fully learned edge-linking |
| MMLU R202 random12 | projected `11/12` vs baseline `11/12`, harms `0` | no transfer improvement signal |

The important diagnosis is that AQuA currently has the answer-improvement signal, while MMLU currently has the first-class graph-engineering signal. They are not yet the same method.

## Failure Diagnosis

1. The learned MMLU graph policy emits PromptNode roles but does not reliably learn the ordered PromptNode chain and PromptEdge topology. R188 produced only `2/50` contract-ready raw graphs.
2. The R189 projection makes graphs executable, but projection alone is not an answer-improving mechanism. R202 preserved accuracy on random12 but did not improve it.
3. The current MMLU target export is a preserve-safe insertion target. It teaches structure but not enough task-conditioned switch behavior.
4. The AQuA R065/R095 signal depends on objective and safety features from multi-view traces. That is useful, but it is too expensive and must be distilled into a cheaper policy before it can be a mature SCI-Q2 system claim.

## Revised Method

Use a **PromptNode-PromptEdge Constrained Graph Policy**:

- PromptNodes are inserted before execution, not as post-hoc patches.
- PromptEdges can carry prompts as edge-level routing instructions, not only node-local text.
- The decoder learns task-conditioned activation and routing decisions.
- A constrained topology layer enforces only the safety-critical structural invariant: `PN_Memory -> PN_Verifier -> PN_Router -> final decision`.
- The paper must explicitly call this a hybrid constrained decoder unless an ablation proves raw learned graphs work without projection.

## Training Target Changes

The next training target should no longer be only `preserve_safe_insert`.

| Target | Purpose |
|---|---|
| `insert_none_or_insert_promptedge_chain` | learn when the virtual node chain is needed |
| `edge_permission_mask` | learn read/write/forward PromptEdge permissions |
| `router_final_or_abstain` | make PN_Router change the final answer only when evidence is strong |
| `objective_safety_switch` | distill AQuA R065/R095 objective-safety signal without gold labels |
| `promptedge_text_policy` | represent prompt guidance as edge text where appropriate |

## Required Ablations

Before another broad API run, the system needs these ablations:

| Ablation | What It Tests |
|---|---|
| ARG baseline | original comparison point |
| Raw learned PN/PE graph | whether ML learns topology without projection |
| Projected PN/PE graph | structural validity and safety |
| Projected PN/PE + router-final | whether final routing changes answers |
| Objective-safety distilled selector | whether AQuA R065 signal can be made cheap |
| PromptEdge-as-edge-text | whether prompt carried by edges improves routing/verification |

## Paper Direction

The SCI-Q2 path should be framed conservatively:

1. Main accuracy evidence is still AQuA tail34 R065/R068/R069 line, not MMLU.
2. MMLU is transfer/safety/negative evidence until a redesigned router-final policy improves a random slice.
3. The novelty claim should be about first-class PromptNode/PromptEdge graph augmentation with constrained learned routing, not "just adding virtual nodes".
4. The method section must separate learned decisions from structural constraints, because the current best executable MMLU graph uses projection.

## Next

- R207: build a consolidated claim/evidence matrix across AQuA and MMLU.
- R208: specify negative controls and ablations.
- R209: draft the SCI-Q2 paper outline around the claim that is actually supported.
- R210: mandatory goal audit before new API or paper-scale drafting.
