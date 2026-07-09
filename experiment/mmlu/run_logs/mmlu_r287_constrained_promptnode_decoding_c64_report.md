# R286 Constrained PromptNode Decoding Audit

**Claim boundary**: No-API constrained decoding audit only. Candidate selection uses generated graph structure, not answer labels, and never adds nodes or edges.

- Tasks: `24`
- Candidates per task: `64`
- Candidate graphs: `1536`
- Selected with any PN: `24`
- Selected with all PN roles: `24`
- Selected with PN chain: `20`
- Selected with terminal router: `24`
- Selected contract-ready: `20`
- Selected contract-ready rate: `0.833`
- Tasks with any contract-ready candidate: `20`
- API eval allowed next: `True`

## Boundary

R286 does not add, delete, or relabel graph nodes. It only selects among graphs sampled from the retrained R283 checkpoint.

## Next

Run checkpoint-level API smoke on selected constrained graphs.
