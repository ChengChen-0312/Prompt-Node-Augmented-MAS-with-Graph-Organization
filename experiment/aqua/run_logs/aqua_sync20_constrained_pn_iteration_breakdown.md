# Constrained PN Iteration Breakdown

Timestamp: 2026-07-08 02:52 Asia/Shanghai

## Purpose

Test whether constraining Prompt Node topology and making `PN_Verifier` perform structured target/option-binding audits can improve AQuA sync20 without answer patches or true-label leakage.

## Code Changes

Implemented:

- `canonicalize_prompt_node_topology(...)` in `experiment/aqua/prompt_node_graph.py`
  - Replaces invalid generated PN subgraphs with a canonical chain:
    `real agents -> PN_Memory -> PN_Verifier -> PN_Router`
  - Preserves real-agent roles and real-agent edges.
  - Does not read `true_answer`, task ids, or known wrong cases.

- Role-specific `PromptNode` contracts in `mas_framework/agents/prompt_node.py`
  - `PN_Memory`: evidence ledger.
  - `PN_Verifier`: `TARGET_AUDIT`, `OPTION_BINDING_AUDIT`, `NO_NEAREST_OPTION_RESCUE`.
  - `PN_Router`: suppress unsupported labels and forward verified evidence.

- `--prompt_node_topology_policy` in AQuA evaluate/finetune scripts.

- `decision_exposure_policy="terminal"` for canonicalized PN graphs.
  - This allows final decision to receive terminal/router output only when explicitly marked.
  - Default remains `all` to preserve ARG-Designer behavior.

- Backward compatibility fix in `experiment/model.py`
  - Old 4-role checkpoints now filter sampling candidates to their checkpoint `role_mapping`.
  - This prevents `KeyError: 'PN_Memory'` after the global role embedding cache grows to 7 roles.

## Verification

- Unit tests: `17` tests passed with `.venv/bin/python -m unittest discover -s tests -v`
- Compile checks passed for modified modules.
- Baseline 4-role checkpoint manual PN construction smoke passed after role-filter fix.

## Experiments

### E1: Clean PN-ARGDesigner + Canonicalize Generated PN, Final Sees All

Command used `--prompt_node_topology_policy canonicalize_generated` with the clean PN model.

- Result file: `experiment/aqua/aqua_sync20_pn_constrained_generated_results.jsonl`
- Accuracy: `17/20 = 85.00%`
- Cost: `$0.814055`
- PN graphs: `9/20`
- PN role counts: `PN_Memory=9`, `PN_Verifier=9`, `PN_Router=9`

Outcome:

- Tied baseline accuracy but higher cost.
- `task_199`: changed from wrong `E` to wrong `C`.
- `task_172`: changed from wrong `C` to wrong `A`.
- No wrong-to-right improvement.

### E2: Clean PN-ARGDesigner + Canonicalize Generated PN, Final Sees Router Only

Command used terminal decision exposure for canonicalized PN graphs.

- Result file: `experiment/aqua/aqua_sync20_pn_constrained_terminal_results.jsonl`
- Accuracy: `16/20 = 80.00%`
- Cost: `$0.757805`

Outcome:

- Worse than baseline.
- Wrong tasks: `task_152`, `task_199`, `task_172`, `task_132`
- `task_132` became right-to-wrong, likely because the final decision lost useful original evidence or due LLM nondeterminism.

### E3: Baseline ARG + Structured Manual PN, Final Sees All

Command used the original ARG baseline model with manual `memory_verifier_router` insertion and no topology terminal exposure.

- Result file: `experiment/aqua/aqua_sync20_pn_structured_manual_all_results.jsonl`
- Accuracy: `17/20 = 85.00%`
- Cost: `$1.017260`

Outcome:

- Tied baseline accuracy with much higher cost.
- Changed only `task_152`, from wrong `E` to wrong `D`.
- No wrong-to-right improvement.

## Diagnosis

This iteration improved structural validity but not accuracy.

The key observation from `task_199`:

- `PN_Verifier` correctly identified `NO_EXACT_OPTION` and suppressed unsupported labels.
- `PN_Router` correctly reported that no option was verified.
- If final sees all original agent outputs, it bypasses the router and picks a label anyway.
- If final sees only the router, it loses useful raw reasoning and may still pick a wrong option from weak evidence.

This means v2 is still missing a paper-worthy mechanism:

- The router needs a stronger output contract that either preserves verified candidates with enough reasoning for FinalRefer, or explicitly produces a calibrated uncertainty/abstention signal.
- Training data should be generated with the same terminal/router exposure if terminal exposure is used at evaluation.
- AQuA sync20 contains likely label/option-noise cases; a verifier that rejects unsupported labels may improve mathematical faithfulness while not improving dataset-label accuracy.

## Next Method Direction

Do not claim improvement from this iteration.

Next candidate method:

1. Train-time router supervision:
   - save only PN graphs where the router output and final answer agree with the dataset label;
   - track wrong-to-right and right-to-wrong flips;
   - avoid using the test set for this filtering.

2. Router output should include a compact answer contract:
   - `SUPPORTED_OPTION: A-E or NONE`
   - `BINDING_STATUS: EXACT_MATCH / EQUIVALENT_FORM / NO_EXACT_OPTION / UNSUPPORTED_LABEL`
   - `FINAL_EVIDENCE_SUMMARY`

3. Add a final decision prompt that is not a post-hoc patch:
   - It should consume router contracts as normal terminal graph evidence.
   - It must not branch on task ids or known bad examples.

4. Before claiming SCI-level improvement:
   - run AQuA beyond sync20;
   - audit label noise;
   - include cost-adjusted accuracy and structural-validity ablations.

