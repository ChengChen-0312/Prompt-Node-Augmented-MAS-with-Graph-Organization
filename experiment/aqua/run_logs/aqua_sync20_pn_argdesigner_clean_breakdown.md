# Clean PN-ARGDesigner AQuA Sync20 Breakdown

Timestamp: 2026-07-08 02:28 Asia/Shanghai

## Purpose

Evaluate the train-time Prompt Node version of ARG-Designer on AQuA sync20 after fixing the data-pollution bug where `PN_*` roles could be sampled as ordinary solver roles in simple/cold-start graphs.

This is a train-time virtual-node run, not a post-hoc final-answer patch.

## Configuration

- Baseline: ARG-Designer `FinalRefer`
- Method: PN-ARGDesigner with `PN_Memory`, `PN_Verifier`, `PN_Router`
- Runtime model: `gpt-4o-2024-08-06`
- Dataset: AQuA sync20
- Model dir: `experiment/aqua/output/aqua_pn_mvr_clean_model_20260708-015036`
- Finetune data dir: `experiment/FinetuneData_AQuA_PN_MVR_clean_20260708-015033`
- Evaluation result file: `experiment/aqua/aqua_sync20_pn_argdesigner_clean_results.jsonl`
- Evaluation summary: `experiment/aqua/res_logs/aqua_sync20_pn_argdesigner_clean_summary.jsonl`

## Implementation Fixes Before This Run

1. Added a real-agent role filter:
   - Real roles: `Math Solver`, `Mathematical Analyst`, `Programming Expert`, `Inspector`
   - Prompt-node roles are no longer eligible for random simple/cold-start role sampling.

2. Added `--finetune_data_dir` to `experiment/aqua/finetune_aqua.py`.
   - This avoids mixing clean PN data with earlier polluted data in `../FinetuneData_AQuA`.

3. Verified by unit tests:
   - `10` tests passed with `.venv/bin/python -m unittest discover -s tests -v`
   - Compile check passed for PN-related modules.

## Finetune Data Audit

New finetune directory: `experiment/FinetuneData_AQuA_PN_MVR_clean_20260708-015033`

- Total `.pt` files: `78`
- `memory_verifier_router` files: `10`
- `none` policy files: `68`
- Files with PN roles and `policy=none`: `0`
- PN role counts:
  - `PN_Memory`: `11`
  - `PN_Verifier`: `11`
  - `PN_Router`: `11`

Conclusion: the previous PN-as-normal-agent pollution is fixed for this clean run.

## Training Summary

Pretraining:

- Cold-start graphs: `21`
- Role mapping: `7` roles
- Best pretrain checkpoint: epoch `30`, validation loss `1.7850`

Finetuning:

- Finetune graphs: `78`
- DAG check: `78/78`
- Role mapping: `7` roles
- Best finetune checkpoint: epoch `92`, validation loss `2.4570`

## Evaluation Result

Baseline ARG-Designer:

- Accuracy: `17/20 = 85.00%`
- Cost: `$0.508365`
- Prompt tokens: `36,723`
- Completion tokens: `21,650`

Clean PN-ARGDesigner:

- Accuracy: `17/20 = 85.00%`
- Cost: `$0.661815`
- Prompt tokens: `48,156`
- Completion tokens: `28,069`

Result: tied baseline accuracy with higher cost. This fails the success gate `>=18/20`.

## Prediction Diff Against Baseline

Changed predictions: `1/20`

- `task_199`: true `A`
  - Baseline predicted `C` and was wrong.
  - Clean PN-ARGDesigner predicted `E` and was still wrong.

Wrong tasks for clean PN-ARGDesigner:

- `task_152`: true `C`, predicted `E`
  - Roles: `Math Solver -> Programming Expert -> Mathematical Analyst`
  - No PN sampled.
- `task_199`: true `A`, predicted `E`
  - Roles: `Math Solver`, `Programming Expert`, `PN_Verifier`
  - Edges: `0 -> 1`, `0 -> 2`
  - PN_Verifier summarized evidence but did not catch answer-option binding mismatch.
- `task_172`: true `E`, predicted `C`
  - Roles: `Math Solver`, `Programming Expert`, `PN_Router`, `PN_Router`
  - Edges: `0 -> 1`, `0 -> 3`, `1 -> 2`
  - The sampled graph used duplicate routers without a Memory/Verifier chain.

## PN Sampling Statistics On Sync20

- Test graphs containing at least one PN role: `9/20`
- PN role counts:
  - `PN_Verifier`: `7`
  - `PN_Router`: `2`
  - `PN_Memory`: `2`
- Overall role counts:
  - `Math Solver`: `28`
  - `Programming Expert`: `10`
  - `Mathematical Analyst`: `7`
  - `Inspector`: `4`
  - `PN_Verifier`: `7`
  - `PN_Router`: `2`
  - `PN_Memory`: `2`

## Interpretation

The v1 method successfully makes Prompt Nodes part of train-time data and inference graphs, but it does not yet improve accuracy.

The main failure is not implementation plumbing. The main failure is method design:

1. PN roles are sampled as ordinary node labels by the ARG decoder.
2. The decoder can create semantically invalid PN structures, such as duplicated `PN_Router` nodes and missing `PN_Memory -> PN_Verifier -> PN_Router` chains.
3. The current `PN_Verifier` behaves mostly like an evidence summarizer. It does not reliably enforce target preservation, answer-option binding, or contradiction checks.
4. Cost increases because PN nodes add extra execution tokens, while the final answer quality does not improve.

Therefore, only adding virtual nodes is not enough for a SCI Q2-level method claim. The next iteration needs a stronger algorithmic contribution, not just more PN roles.

## Next Iteration Direction

The next method should move from "free-form PN roles" to "constrained typed Prompt Node control":

1. Add a PN grammar during graph decoding:
   - no duplicate PN roles in the same chain;
   - if `PN_Router` appears, require upstream `PN_Memory` and `PN_Verifier`;
   - route real-agent outputs through `PN_Memory -> PN_Verifier -> PN_Router` before final aggregation.

2. Make `PN_Verifier` perform structured checks:
   - extracted final answer label;
   - option text/value binding;
   - target-question preservation;
   - unsupported-label detection;
   - conflict detection across agents.

3. Add evaluation metrics beyond accuracy:
   - wrong-to-right flips;
   - right-to-wrong flips;
   - option-binding error rate;
   - cost per solved task;
   - PN structural validity rate.

4. Required ablations before paper claims:
   - grammar-constrained PN vs free PN;
   - PN without verifier checks;
   - PN roles executed as normal `MathSolver`;
   - same node budget without PN semantics.

