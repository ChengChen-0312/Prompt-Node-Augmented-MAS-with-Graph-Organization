# R286 Constrained PromptNode Decoding Audit

**Claim boundary**: No-API constrained decoding audit only. Candidate selection uses generated graph structure, not answer labels, and never adds nodes or edges.

- Tasks: `24`
- Candidates per task: `16`
- Candidate graphs: `384`
- Selected with any PN: `24`
- Selected with all PN roles: `23`
- Selected with PN chain: `10`
- Selected with terminal router: `24`
- Selected contract-ready: `10`
- Selected contract-ready rate: `0.417`
- Tasks with any contract-ready candidate: `10`
- API eval allowed next: `False`

## Boundary

R286 does not add, delete, or relabel graph nodes. It only selects among graphs sampled from the retrained R283 checkpoint.

## Next

Retrain or regularize the graph policy so the full PN chain appears before API evaluation.
