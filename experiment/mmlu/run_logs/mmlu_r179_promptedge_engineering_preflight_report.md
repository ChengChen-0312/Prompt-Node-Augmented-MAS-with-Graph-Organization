# R179 MMLU PromptNode/PromptEdge Engineering Preflight

**Claim boundary**: no API evaluation and no accuracy claim. This run only checks whether the existing MMLU branch can execute and learn first-class PromptNode/PromptEdge graphs under the ARG-Designer-style model path.

## Result

- MMLU ARG transfer baseline exists: `88/100` from `experiment/mmlu/res_logs/mmlu_r162_transfer_eval_summary.json`.
- `TestGraph` has a `PN_` branch that would select `PromptNode`.
- The branch is blocked in MMLU because `TestGraph._build_from_pyg` calls `prompt_set.get_description(role)` before the `PN_` branch takes effect.
- A constructor-only smoke with role `PN_Memory` fails with `KeyError 'PN_Memory'`.
- The MMLU checkpoint `experiment/mmlu/output/mmlu_arg_base_model_r159` has six node roles and no PN roles.
- `experiment/mmlu/evaluate_mmlu.py` has no PromptNode topology/policy flag and no PN-capable graph-policy path.

## Engineering State

The current MMLU branch is not ready for a PromptNode/PromptEdge accuracy run. It can serve as a robustness route for a SCI-Q2 story only after the PN/PE graph interface is made first-class in MMLU, not as a post-hoc patch.

Required steps before an MMLU API run:

1. Add `PN_Memory`, `PN_Verifier`, and `PN_Router` role descriptions to the MMLU prompt registries used by both execution and training.
2. Add constructor tests proving a MMLU graph with PN roles builds without an API call.
3. Export PN/PE target graphs for MMLU without using transfer100 labels as training labels.
4. Retrain a PN-capable MMLU graph generator so the model can learn when to add virtual nodes and how to link them.
5. Only then run a bounded same-model MMLU transfer smoke against the R162 ARG baseline.

## SCI-Q2 Implication

This keeps the work aligned with the paper goal. AQuA local data is exhausted without contaminating tail34/sync20, so MMLU is a reasonable robustness branch, but using it now would overclaim. The next safe step is PN/PE engineering closure, followed by target export and retraining.
