# Calibrated PN Utility Gate Design

## Goal

Build R027: a PromptNode utility gate that decides whether virtual-node evidence should influence the final AQuA answer using only runtime evidence available before final aggregation. The method must not use test labels, task ids, gold answers, or noisy-label patches.

## Context

R025 showed that train-time PromptNode virtual nodes underperform ARG-Designer on AQuA 100: ARG `83/100`, PN router `78/100`, PN candidate selection `79/100`. R026 showed that conservative abstention reduces harm but only ties clean accuracy: conservative PN variants reach `82/100`, clean `77/85`, while ARG is `83/100`, clean `77/85`.

The failure mode is not simply weak PromptNode evidence. Some strong PN contracts override correct ordinary-agent majorities, while some PN contracts help when ordinary agents are missing or divided. The gate must estimate PN utility instead of always using or always suppressing PN evidence.

## Design

Add a registered final decision node named `CalibratedPNUtilityFinalRefer`.

The gate extracts:

- ordinary-agent A-E votes from non-`PN_*` upstream outputs;
- majority option, majority count, and number of valid ordinary votes;
- PN router contracts from `SUPPORTED_OPTION`, `BINDING_STATUS`, and `FINAL_EVIDENCE_SUMMARY`;
- whether router evidence is strong (`EXACT_MATCH`, `EQUIVALENT_FORM`, or `EQUIVALENT`) and whether it conflicts with ordinary-agent majority;
- whether router evidence is weak (`NO_EXACT_OPTION`, `UNSUPPORTED_LABEL`, `CONFLICT`, `NONE`, or missing).

The first implementation uses a transparent calibrated policy:

1. If ordinary agents have a valid majority of at least two votes and all PN contracts are weak, return the ordinary majority directly.
2. If ordinary agents have a valid majority of at least two votes and strong PN contracts disagree with that majority, return the ordinary majority directly.
3. If there is no valid ordinary majority and exactly one strong PN-supported A-E option exists, return the PN-supported option directly.
4. Otherwise fall back to `ConservativeRouterContractFinalRefer`, so the LLM still aggregates uncertain cases.

This policy is intentionally conservative: it treats PromptNodes as an evidence-routing mechanism, not as a label oracle. It can exceed prior PN variants only if runtime graph evidence separates fix cases from harm cases.

## Calibration Protocol

The policy must be calibrated or sanity-checked on non-test rows only. Use `base_tasks_indices` and `finetune_tasks_indices` from `task_split_aqua.json`, or other train/finetune rows, to compare candidate thresholds. Do not use AQuA test labels, sync20 labels, or the first 100 test labels to choose thresholds after evaluation.

The AQuA 100 evaluation is valid only after the policy is fixed. Report total accuracy, clean accuracy, noisy-label behavior, cost, fix/harm counts, and whether the result exceeds ARG-Designer.

## Testing

Unit tests must cover:

- direct-vote extraction ignores `PN_*` roles;
- weak PN contracts plus ordinary majority produce a direct deterministic answer;
- strong conflicting PN contracts plus ordinary majority produce a direct deterministic answer;
- strong PN contracts with no ordinary majority produce a PN deterministic answer;
- uncertain cases fall back to conservative LLM aggregation.

## Paper Interpretation

If R027 exceeds ARG on clean rows, it becomes a candidate SCI Q2 contribution: virtual nodes improve accuracy through calibrated evidence routing. If it ties or underperforms, the result still supports the negative claim that virtual nodes alone are insufficient and motivates a learned utility model.

