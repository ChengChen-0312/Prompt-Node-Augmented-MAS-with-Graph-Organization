# R182 MMLU PromptEdge Topology Adapter

**Claim boundary**: engineering and test coverage only. No API evaluation, no MMLU accuracy claim, and no graph-policy training claim.

## What Changed

- Added `experiment/mmlu/promptedge_topology.py`.
- Implemented `inject_promptedge_topology`, which inserts `PN_Memory -> PN_Verifier -> PN_Router` as first-class graph nodes before execution.
- Stored PromptEdge metadata on edges, including `read`, `write`, and `forward` permissions.
- Implemented `promptedge_topology_to_pyg`, preserving `decision_exposure_policy='terminal'` and `promptedge_meta`.
- Extended PromptNode option parsing to support MMLU `Option A:` formatting.
- Made PromptNode router contracts option-label aware: MMLU now uses `A/B/C/D/NONE`, while AQuA can still use `A/B/C/D/E/NONE`.

## Verification

- `python -m unittest tests.test_r182_mmlu_promptedge_topology -v`: `3/3` passed.
- R181 plus adjacent AQuA policy tests: `11/11` passed.

## Why This Matters

This closes a design mismatch with `update2.docx`: virtual nodes are now representable before execution in MMLU, and prompts can appear as edge metadata with permissions. This is still not a performance result. It only makes the transfer route technically valid enough for target export and later retraining.

## Remaining Blockers

- No non-leaky MMLU PN/PE target export manifest exists.
- No PN-capable MMLU graph generator checkpoint has been trained.
- No MMLU transfer PromptNode/PromptEdge API smoke is authorized before the next target/export/training steps.
