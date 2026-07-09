# R257 PromptNode/PromptEdge V2 Design

**Claim boundary**: design only. No API, no accuracy claim, and no SCI-Q2 readiness claim.

## Why V1 Failed

R253-R256 show that the current proposed PN/PE transfer prompt is not robust:

- Proposed PN/PE: `10/16`, fix/harm `3/1`
- Node-only: `11/16`, fix/harm `4/1`
- Plain requery: `12/16`, fix/harm `4/0`
- Failure modes: `plain_fix_lost_by_proposed=2`, `node_fix_lost_by_promptedge=1`, `proposed_control_harm=1`

The problem is not model capability. Plain requery can solve more items. The failure is graph-prompt overconstraint and insufficient harm gating.

## V2 Principle

PromptNodes must act as graph-organization checkpoints, not as verbose reasoning decorations. PromptEdges should carry compact contracts and permissions. The router may change ARG only after independent evidence and verifier checks justify the change.

## V2 Execution Contract

Variant name: `proposed_v2_independent_guarded_pnpe`

1. `PN_Memory` reads the item and independently proposes a candidate label without using ARG's initial choice.
2. `PN_InstructionVerifier` checks whether the candidate follows the option text, arithmetic/physics/formula constraints, and the question wording.
3. `PN_Router` sees ARG's initial choice only after the independent candidate and verifier ledger are formed.
4. Router keeps ARG unless:
   - independent candidate differs from ARG;
   - verifier marks the candidate as high confidence;
   - verifier provides at least two concrete checks; and
   - no unresolved conflict remains.
5. Lifecycle:
   - `update`: candidate has verified conflict against ARG;
   - `compress`: duplicate evidence is shortened;
   - `prune`: weak candidate or unresolved conflict is dropped;
   - `merge`: independent candidate and ARG agree;
   - `upgrade`: repeated verified pattern can be reused in future selector training.

## Edge Policy

V2 uses edge prompts as compact contracts, not long procedural reasoning:

- `item_to_memory` / `read`: solve independently; do not inspect ARG initial choice.
- `memory_to_verifier` / `write`: write candidate label plus exactly two evidence checks.
- `verifier_to_router` / `forward`: forward candidate only if checks are high confidence; otherwise forward KEEP_ARG.

## Expected Effect

This design is intended to reduce the R253 matched-control harm and avoid the R256 edge-text regression. It is not expected to beat plain requery automatically. The next diagnostic must compare it against the already executed R253 controls.

## R258 Preflight Requirements

- Use the same tiny16 probe set as R253 for paired comparison.
- Generate only the new v2 API variant plus deterministic ARG reference, unless cost allows adding fresh controls.
- Keep model `gpt-4o-2024-08-06`.
- Keep true answers, correctness, task ids, and evaluation labels out of model-visible prompts.
- Estimate cost before API; broad API remains blocked.
