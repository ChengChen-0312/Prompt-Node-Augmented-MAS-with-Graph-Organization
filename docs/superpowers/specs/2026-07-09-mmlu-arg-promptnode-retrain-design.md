# MMLU ARG vs PromptNode Retrain Design

## Goal

Build a fair MMLU train-time comparison between a retrained ARG-Designer graph policy and a retrained PromptNode-augmented graph policy. The experiment must test whether virtual nodes help after they are present in the graph-policy training distribution, instead of being added only as prompt-time or post-hoc patches.

## Problem

Current MMLU evidence shows that prompt-only PromptNode/PromptEdge variants do not beat plain requery. This is not a decisive rejection of PromptNode because the MMLU node variants are not true trained graph policies. They expose ARG's initial answer and graph instructions in the prompt, which can add anchoring and prompt overhead. The missing evidence is a same-split, same-model, train-time comparison.

## Compared Systems

1. `MMLU-ARG-Retrain`: ARG-Designer graph policy trained with the original MMLU role vocabulary and no PromptNode roles.
2. `MMLU-PromptNode-Retrain`: graph policy trained from the beginning with PromptNode roles and PromptEdge metadata in the training graph distribution.
3. Control references: plain requery, node-only prompt, prior PN+PE prompt, and v3 edge-gated PN+PE prompt from R274/R279.

## PromptNode Requirements

- PromptNodes are first-class graph nodes before execution.
- Required roles: `PN_Memory`, `PN_Verifier`, `PN_Router`, and optionally `PN_EdgeGate` when the training data supports it.
- Edge permissions must be represented at least as metadata: `read`, `write`, and `forward`.
- Lifecycle metadata must be auditable: `update`, `compress`, `prune`, `merge`, `upgrade`.
- No training, prompt, selector, or evaluation path may use hidden labels as model-visible input.

## Data and Splits

- Use existing MMLU local data root: `/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/datasets/MMLU`.
- Use existing transfer split artifacts for evaluation: `mmlu_stem_transfer100`, `full24`, and `tiny16`.
- Use a fixed training split manifest before training. The evaluation tasks must not be included in generated training targets.
- The first training comparison can use one seed for feasibility. Paper-ready claims need three seeds or a clearly stated computational limitation.

## Training Protocol

`MMLU-ARG-Retrain` uses the original ARG-Designer training path and role mapping. Existing checkpoint `experiment/mmlu/output/mmlu_arg_base_model_r159` is useful as a baseline reference, but the fair comparison should rebuild or at least re-audit the checkpoint under the same split and run metadata.

`MMLU-PromptNode-Retrain` must train with an expanded role mapping. Existing R184/R186/R188 artifacts show this path is viable: role mapping size grows from 6 to 9 and includes `PN_Memory`, `PN_Verifier`, and `PN_Router`. R281 freezes the protocol before launching the longer retrain.

## Evaluation Protocol

Each checkpoint generates graphs for the same held-out items. Generated graphs are audited before API execution. API evaluation uses `gpt-4o-2024-08-06`, `FinalRefer`, and the same cost/logging protocol as prior MMLU runs. Report accuracy, fix/harm, cost, clean graph audit, PromptNode usage, and generated topology statistics.

## Success Criteria

The strongest claim is supported only if trained PromptNode graph policy beats retrained ARG and does not lose to plain requery on the held-out transfer setting. A weaker but still useful claim is supported if it beats retrained ARG with lower harm and has interpretable PromptNode usage, while plain requery remains stronger.

## Risks

- Existing PN-capable training data may be biased toward prompt-generated targets rather than robust graph policies.
- MMLU full24 is small; transfer100 or multi-seed evaluation is needed for paper-level evidence.
- MPS local training may be slower or hit unsupported operations. CPU fallback must remain available.
- The current old ARG checkpoint role mapping is incompatible with PN role mapping, so direct finetuning is invalid.

