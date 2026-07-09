# Contract-Coverage Graph Objective Design

## Problem Anchor

The current strongest evidence is R035 multi-contract union: PromptNode graph variants improve clean AQuA first200 coverage when several `PN_Router` contracts agree. This is still partly an offline selector over completed traces. For a stronger paper method, the same signal must become a graph-selection or train-time objective that rewards PromptNode graphs for producing stable option-binding contracts.

## Goal

Create a label-free contract-coverage objective over existing AQuA PromptNode traces. The objective must rank graph variants by virtual-node evidence quality without using gold answers, clean/noisy audit labels, official rationales, task IDs, or nearest-option rescue. It should produce an analysis table showing whether the objective can guide the next generation of PN graph selection.

## Non-Goals

- Do not change AQuA predictions during this iteration.
- Do not call the LLM or rerun tail34 while quota is exhausted.
- Do not train a new ARG-Designer checkpoint yet.
- Do not use `true_answer`, audit `clean_label`, or task-specific metadata as objective inputs.

## Objective Definition

For each method trace (`router`, `candidate`, `conservative`, `calibrated`), extract the existing contract-consensus features:

- `router_option`
- `router_binding_status`
- `strong_router_contract_count`
- `direct_majority`
- `direct_majority_count`
- `direct_valid_vote_count`
- `router_matches_direct_majority`
- `router_conflicts_with_direct_majority`
- `all_router_contracts_weak`

Define a per-trace `contract_coverage_score`:

- `+4` if there is at least one strong `PN_Router` contract with a valid A-E option.
- `+3` if the router option matches the non-PN direct majority.
- `+1` for each direct majority vote, capped at `3`.
- `+1` if the trace selected/generated a graph containing PromptNode roles.
- `-4` if the strong router contract conflicts with direct majority.
- `-2` if all router contracts are weak.

This score is not an answer selector. It is a graph-quality objective: a high-scoring graph is a better candidate for producing trusted virtual-node evidence.

## Analysis Outputs

The R038 analysis should generate:

1. A JSONL file with one row per task containing ranked graph variants and score components.
2. A summary JSON with:
   - mean top score,
   - number of tasks with positive top score,
   - unique top method distribution,
   - tie count,
   - top method agreement with R035 pure multi-contract switch source,
   - selected-method answer accuracy as diagnostic only.
3. A markdown report with key findings and a paper interpretation.

## Integrity Constraints

- Objective inputs may include graph roles, agent outputs, router contracts, direct-agent votes, selected candidate graph metadata, and predicted answers for diagnostics.
- Objective inputs must not include gold labels, audit labels, or clean/noisy labels.
- Accuracy and clean/noisy splits are allowed only in the report section as post-hoc diagnostics.
- Reports must explicitly state that R038 does not establish a new accuracy claim until a graph selector is run prospectively.

## Expected Evidence Boundary

R038 should not be used to claim a new performance result. Its role is to determine whether contract coverage is a plausible training/selection target. A useful result would show that:

- R035 pure switches are associated with high-scoring PromptNode variants;
- lowering thresholds increases coverage but causes harm, matching R037;
- the score identifies which PN variants contribute evidence, so future training can optimize graph structures toward those variants.
