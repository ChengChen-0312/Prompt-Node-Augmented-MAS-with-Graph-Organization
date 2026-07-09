# R062 Integrated Selective PromptNode Evaluator Design

## Goal

Turn the R061 replay rule into a fresh online evaluator. The evaluator should
run ARG-Designer first, inspect only visible direct-agent votes, and activate a
canonical PromptNode lifecycle only when the direct evidence is conflicted.

## Motivation

R061 improves tail34 in replay (`29/34` versus ARG `28/34`) but it still uses
already executed dense R058 traces. A paper-level system claim needs an
integrated run where PromptNodes are not executed by default. R062 is the first
implementation step toward that claim.

## Runtime Flow

For each AQuA task:

1. Generate and execute the ARG baseline graph with `FinalRefer`.
2. Extract non-PromptNode direct votes from ARG agent outputs.
3. If direct votes do not contain at least two distinct A-E options, or if any
   direct option has count `>= 2`, stop and keep the ARG prediction.
4. If the prefilter passes, generate and execute the PromptNode graph using the
   R055/R058 PromptNode checkpoint, canonical PromptNode topology, terminal
   exposure, and `RouterContractFinalRefer`.
5. Apply the R061 router gate: strong router contract, router option in direct
   votes, and valid PromptNode prediction.
6. Select PromptNode only when the full gate passes; otherwise keep ARG.

This means PromptNodes are conditionally activated online. They are not used as
a post-hoc patch and are not run on every task.

## Leakage Boundary

The prefilter and gate must not read `true_answer`, `is_solved`, task ids,
clean/noisy labels, or outcome-derived fields. Those fields may appear only in
the final record for evaluation after selection.

## Inputs

- Baseline model: `experiment/aqua/output/aqua_sync20_model_20260707-230509`
- PromptNode model: `experiment/aqua/output/aqua_pn_graph_policy_r055_full`
- LLM: `gpt-4o-2024-08-06`
- Split: AQuA sync20 for smoke, then AQuA tail34.

## Outputs

- Integrated selective JSONL records.
- Summary JSONL/JSON with selected accuracy, baseline accuracy, PN-call count,
  full-gate switch count, fix/harm, and cost.
- Markdown report explaining that R062 is a fresh integrated run.

## Success Criteria

- Smoke run executes without API/environment errors.
- R062 tail34 should match or beat ARG `28/34` without observed harm.
- PromptNode calls should be fewer than total tasks.
- The report must separate baseline prefilter activations from final PN switches.
