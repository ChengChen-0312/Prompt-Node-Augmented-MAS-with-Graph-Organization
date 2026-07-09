# AQuA sync20 Router-Contract PromptNode Supervision Breakdown

Date: 2026-07-08

## Baseline

- Baseline: ARG-Designer `FinalRefer`
- Split: AQuA sync20 from `task_split_aqua.json`
- LLM: `gpt-4o-2024-08-06`
- Result: `17/20 = 85.00%`
- Cost: `$0.508365`
- Wrong rows: `task_152`, `task_199`, `task_172`

## Method Under Test

Router-contract PromptNode supervision adds machine-readable contract fields to
`PN_Router`:

- `SUPPORTED_OPTION`
- `BINDING_STATUS`
- `FINAL_EVIDENCE_SUMMARY`
- `SUPPRESS_UNSUPPORTED_LABELS`

Training/evaluation code paths:

- Prompt-node roles: `PN_Memory`, `PN_Verifier`, `PN_Router`
- Model dir: `output/aqua_pn_router_contract_model_20260708-030015`
- Finetune data dir: `../FinetuneData_AQuA_RouterContract_20260708-030012`
- Decision method: `RouterContractFinalRefer`

## Stage 2 Data Generation

- Stage 2a pruned generated graphs: `11` solved PN-supervised graphs
- Stage 2b simple graphs: `62` solved graphs
- Stage 2c replay graphs: `6` copied graphs
- Total Stage 3 finetune graphs: `79`
- PN roles present in finetune data: `11` graphs
- Contamination check: `policy=none` graphs with PN roles = `0`

## Stage 3 Training

The first Stage 3 attempt exposed a performance bug: `AquaGraphDataset` rebuilt
`SentenceTransformer` once per graph while computing task embeddings. This caused
repeated `Loading weights` output and stalled the run. The adapter now caches the
default sentence embedding model. Regression test:
`tests/test_aqua_adapter_embedding_cache.py`.

Stage 3-only retrain reused the already generated data and did not rerun LLM data
generation.

- Best epoch: `98/100`
- Best validation loss: `2.1568`
- Best checkpoint: `output/aqua_pn_router_contract_model_20260708-030015/ef_best_model.pth`

## Evaluation A: Generated PN Only

Command policy:

- `--prompt_node_policy none`
- `--prompt_node_topology_policy canonicalize_generated`

Result:

- Accuracy: `17/20 = 85.00%`
- Cost: `$0.634350`
- Prompt tokens: `51204`
- Completion tokens: `25222`
- Detail file: `aqua_sync20_pn_router_contract_trained_results.jsonl`

Graph/output structure:

- PN graphs: `11/20`
- Role counts: `PN_Memory=11`, `PN_Verifier=11`, `PN_Router=11`
- Binding statuses: `EXACT_MATCH=8`, `NO_EXACT_OPTION=2`, `EQUIVALENT_FORM=1`
- Supported-option counts: `A=2`, `C=3`, `D=4`, `E=1`, `NONE=1`

Wrong rows:

| Task | Gold | Baseline Pred | Router-Trained Pred | Status |
| --- | --- | --- | --- | --- |
| `task_152` | `C` | `E` | `E` | still wrong |
| `task_199` | `A` | `C` | `C` | still wrong |
| `task_172` | `E` | `C` | `A` | still wrong; wrong label changed |

Verdict: generated PN structure changed the graph distribution but did not improve
the solved set. It tied the baseline with higher cost.

## Evaluation B: Forced PN For Every Graph

Command policy:

- `--prompt_node_policy none`
- `--prompt_node_topology_policy canonicalize_or_insert`

Result:

- Accuracy: `14/20 = 70.00%`
- Cost: `$0.785095`
- Prompt tokens: `66350`
- Completion tokens: `30223`
- Detail file: `aqua_sync20_pn_router_contract_trained_forced_results.jsonl`

Graph/output structure:

- PN graphs: `20/20`
- Role counts: `PN_Memory=20`, `PN_Verifier=20`, `PN_Router=20`
- Binding statuses: `EXACT_MATCH=17`, `NO_EXACT_OPTION=3`
- Supported-option counts: `A=5`, `B=3`, `C=5`, `D=3`, `E=2`, `NONE=2`

New harms vs baseline:

| Task | Gold | Baseline Pred | Forced-PN Pred |
| --- | --- | --- | --- |
| `task_61` | `D` | `D` | `E` |
| `task_95` | `A` | `A` | `B` |
| `task_132` | `B` | `B` | `C` |

Verdict: forcing virtual nodes into every graph is not safe. It suppresses useful
direct-agent evidence and reduces sync20 accuracy by `15` points.

## Result-To-Claim Verdict

- `claim_supported`: `no`
- `confidence`: high for the sync20 conclusion
- `integrity_status`: provisional; `.aris/evidence_precheck.json` reports helper
  unavailable, but local result files and summaries exist.

The result does not support the claim that PromptNode/RouterContract exceeds
ARG-Designer on AQuA sync20. It supports a negative finding: virtual nodes require
selective, evidence-calibrated routing; adding or forcing PN nodes alone is not a
publishable accuracy mechanism.

## Implication For The Paper Design

Only adding virtual nodes is insufficient for SCI Q2. A defensible next method must
change the learning objective or graph-selection mechanism, not just insert PN roles.
Recommended next direction:

1. Add a clean/noisy option-binding audit split for AQuA.
2. Train a selective PN gate that predicts when router evidence should override direct
   agent evidence.
3. Report clean-row accuracy, noisy-row harm rate, cost, and calibration.
4. Move the main accuracy claim to a larger AQuA subset and at least one cleaner
   transfer benchmark.
