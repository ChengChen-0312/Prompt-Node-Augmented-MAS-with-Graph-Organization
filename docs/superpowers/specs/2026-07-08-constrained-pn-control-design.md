# Constrained Prompt Node Control Design

## Problem

The first train-time PN-ARGDesigner run proved that virtual Prompt Nodes can enter training and inference graphs, but accuracy stayed at `17/20`. The failure was not plumbing. The model sampled invalid PN structures such as duplicate `PN_Router` nodes, missing Memory/Verifier chains, and `PN_Verifier` outputs that summarized evidence without enforcing option binding.

The next iteration must improve virtual-node behavior without using `true_answer`, task ids, row indices, or deterministic math patches.

## Design Choice

Use graph-level PN topology normalization plus role-specific structured PromptNode behavior.

Rejected alternatives:

- Final-answer guarded replacement only: already tested as a post-hoc path and is not the paper's main claim.
- Dataset-specific wrong-case fixes: violates the requirement to avoid fake math patches.
- Changing ARGDesigner architecture immediately: too broad before proving that constrained PN semantics help.

Recommended v2:

1. Keep ARGDesigner architecture and LLM model unchanged.
2. Normalize any generated PN subgraph into a canonical virtual-node chain:
   - real agent nodes preserve their generated roles and real-agent edges;
   - all real agent nodes write to `PN_Memory`;
   - `PN_Memory -> PN_Verifier -> PN_Router`;
   - duplicate/missing/free-form PN roles are removed before execution.
3. Add role-specific PromptNode prompts:
   - `PN_Memory` emits an evidence ledger.
   - `PN_Verifier` emits target-preservation and option-binding audit sections.
   - `PN_Router` forwards only verified evidence and suppresses unsupported labels.
4. Add CLI control separate from existing manual insertion:
   - `--prompt_node_topology_policy none`
   - `--prompt_node_topology_policy canonicalize_generated`
   - `--prompt_node_topology_policy canonicalize_or_insert`

## Data Flow

Evaluation:

`ARGDesigner.sample -> generated NetworkX graph -> topology policy -> convert_to_pyg_graph -> TestGraph -> PromptNode execution -> FinalRefer`

Finetune data generation:

`ARGDesigner.sample -> prune -> optional train-time PN insertion -> topology policy -> convert_to_pyg_graph -> TestGraph execution -> save solved PyG graph`

## Constraints

- Do not use labels or correctness information in graph normalization.
- Do not branch on `task_id`, row index, or known wrong cases.
- Do not add deterministic arithmetic solving.
- Keep `gpt-4o-2024-08-06` as the target runtime model.
- Preserve ordinary ARG-Designer baseline behavior when all new policies are `none`.

## Success Criteria

Implementation success:

- Unit tests prove invalid PN subgraphs are normalized into a single canonical chain.
- Unit tests prove no-PN graphs are unchanged by `canonicalize_generated`.
- Unit tests prove `PN_Verifier` prompts contain explicit option-binding and nearest-choice rejection instructions.
- Existing PN tests continue passing.

Experiment success:

- AQuA sync20 constrained PN eval must reach at least `18/20` to beat baseline.
- If it does not, record it as a negative iteration and do not claim improvement.

