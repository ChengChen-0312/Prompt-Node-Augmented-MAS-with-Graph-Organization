# Selective PromptNode Routing Design

## Goal

Improve AQuA sync20 beyond the ARG-Designer baseline using virtual Prompt Nodes
as graph-organization mechanisms, without task-id rules, memorized labels, or
fake math patches.

## Context

Prior PN variants showed that virtual nodes can be trained and executed inside
ARG-Designer, but they do not improve accuracy by themselves:

- Baseline ARG-Designer: `17/20`
- Router-contract PN, generated-only: `17/20`
- Router-contract PN, forced every graph: `14/20`

This matches `update2.docx`: Prompt Nodes need lifecycle behavior and routing,
not blanket insertion or global broadcast.

## Recommended Approach

Implement a selective final decision node:
`SelectivePromptNodeFinalRefer`.

It receives ordinary agent outputs plus PN router contracts when the graph
contains Prompt Nodes. It then performs a virtual lifecycle decision:

1. `Memory`: preserve direct agent evidence, option labels, computed values, and
   router contract fields separately.
2. `Verifier`: detect target shifts, option-binding risks, direct/router conflict,
   and `NO_EXACT_OPTION` cases.
3. `Router`: accept direct evidence, use router evidence, or escalate.
4. `Agent-like Prompt Node`: only when conflict or option-binding risk is present,
   run a stricter audit that separates mathematical truth from the submission
   option.

The node must not use row ids, hidden labels, or task-specific fixes. If the
math truth is absent from choices, the output must state that risk rather than
pretending the chosen option is mathematically exact.

## Evaluation Control

Existing canonical PN evaluation exposes only terminal nodes to the final
decision node. Selective routing needs both ordinary agent evidence and PN
contracts, so `evaluate_aqua.py` will get an explicit
`--decision_exposure_policy` argument:

- `auto`: current behavior
- `terminal`: expose only terminal nodes
- `all`: expose every node

R022 should use `all` so the final gate can compare direct evidence against PN
evidence.

## Success Gate

Primary gate remains AQuA sync20:

- Must exceed ARG-Designer `17/20`
- Same LLM: `gpt-4o-2024-08-06`
- No hard-coded task IDs or gold labels
- Record cost and task-level changes

If it ties or fails, record it as another negative result and pivot to larger
noise-aware evaluation rather than inflating the claim.
