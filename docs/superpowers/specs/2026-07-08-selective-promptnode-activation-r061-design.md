# R061 Selective PromptNode Activation Design

## Goal

Build a label-free replay layer that decides when to use an existing
PromptNode-enabled R058 answer instead of the ARG-Designer baseline answer.
The immediate purpose is to test whether virtual Prompt Nodes should be
activated selectively, rather than inserted densely into every graph.

## Context

ARG-Designer remains the paper baseline. On AQuA sync20 it reaches `17/20`,
and the clean audited subset is already `17/17`, so claiming a sync20 increase
would require chasing noisy labels. R055-R058 proved that PromptNodes can be
generated before execution and can preserve sync20 accuracy, but held-out
tail34 rejects dense PromptNode execution: ARG reaches `28/34`, while R058
reaches `25/34` with `1/4` fix/harm.

R061 therefore tests a narrower scientific claim: PromptNodes are useful as
conditional graph-organization mechanisms. They should be activated only when
ordinary direct evidence is uncertain and the PromptNode router provides strong
option-binding evidence.

## Activation Rule

For each task, R061 consumes only the already visible runtime traces from:

- ARG baseline JSONL result.
- R058 router-contract terminal JSONL result.

The gate activates the PromptNode answer only when all conditions hold:

1. Direct non-PromptNode votes contain at least two distinct valid A-E options.
2. No direct option reaches majority count `>= 2`.
3. The PromptNode router has a valid supported option with `EXACT_MATCH`,
   `EQUIVALENT_FORM`, or `EQUIVALENT` binding.
4. The router option is one of the direct-vote options.
5. The router and PromptNode prediction are valid A-E options.

If the gate is false, the selected answer is the ARG baseline answer. If the
gate is true, the selected answer is the R058 PromptNode answer.

## Leakage Boundary

The activation decision must not read `true_answer`, `is_solved`, task ids,
clean/noisy audit labels, or any outcome-derived field. Gold labels are used
only after selection to compute accuracy, fixes, and harms.

The output record may include `true_answer` and `is_solved` for evaluation, but
the nested `gate_features` object must remain outcome-free.

## Outputs

- Replay JSONL with one selected record per task.
- Summary JSON with total accuracy, baseline accuracy, PromptNode accuracy,
  switch count, fix/harm, and switched task ids.
- Markdown report that states the result boundary: R061 is a replay over
  existing traces, not a fresh integrated API run.

## Success Criteria

R061 is promising only if it:

- Does not reduce sync20 relative to ARG (`17/20` expected).
- Improves tail34 relative to ARG without harm.
- Keeps gate features free of labels and task-specific patches.

If these conditions hold, the next experiment should implement a fresh
integrated selective evaluator: run ARG evidence first, activate PromptNodes
only when the gate fires, then validate on the same model setting.
