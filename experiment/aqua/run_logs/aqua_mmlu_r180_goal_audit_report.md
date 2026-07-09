# R180 Five-Iteration SCI-Q2 Goal Audit

**Claim boundary**: audit only. No new API evaluation, no new accuracy claim, and no claim that PromptNode/PromptEdge currently exceeds ARG-Designer.

## Audit Decision

Status: `aligned_but_not_ready_for_broad_api`

No goal drift was detected. R176-R179 stayed aligned with the core target: ARG-Designer as baseline, same-model evaluation, first-class PromptNode/PromptEdge graph organization, no tail34/sync20 leakage, and robustness beyond a single AQuA split.

The route is not SCI-Q2 ready yet. AQuA local non-test data is exhausted for new switch-critical labels, and MMLU needs PN/PE engineering closure before any transfer accuracy claim.

## Evidence Since R175

- R176 found only `4` confirmed switch-critical AQuA override labels, plus `2` weak high-margin candidates. This is not enough to support a learned override-head claim.
- R177 found no additional non-test AQuA override source beyond first200 traces. Tail34 and sync20 remain diagnostic-only.
- R178 confirmed the local AQuA dataset has `254` rows: first200 plus tail34, so there is no unused local AQuA training pool.
- R179 confirmed MMLU has a same-model ARG transfer baseline (`88/100`) but PN/PE is not engineering-ready: MMLU PN constructor fails with `KeyError 'PN_Memory'`, the checkpoint has no PN roles, and the evaluator has no PN topology path.

## Current Best Supported State

- AQuA sync20 ARG baseline: `17/20`, clean `17/17`; sync20 is not a good main-claim split because clean ARG is saturated.
- Best prior AQuA held-out signal: R065 objective-guided multi-view selector, `31/34` vs ARG `28/34`, clean `28/28`, clean fix/harm `1/0`.
- Learned PromptNode insertion is supported by R174/R168-style target agreement.
- Learned override decision is not supported; current evidence favors a two-head design with learned insertion plus conservative, audited override.

## Authorized Next Steps

1. R181: add MMLU PN role descriptions and constructor tests without API.
2. R182: add a MMLU PN/PE topology adapter or export path for first-class virtual nodes.
3. R183: build a non-leaky MMLU PN/PE target export manifest.
4. R184: retrain or dry-run train a PN-capable MMLU graph generator.
5. R185: run the next goal audit before any MMLU transfer API smoke.

## Forbidden Until R185

- Do not train on AQuA tail34 or sync20.
- Do not claim learned override robustness from the four confirmed AQuA switch-critical labels.
- Do not run broad MMLU API evaluation until PN/PE roles, target export, and checkpoint role mapping are closed.
