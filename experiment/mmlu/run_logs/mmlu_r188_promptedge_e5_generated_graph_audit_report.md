# R188 MMLU Generated Graph Audit

**Claim boundary**: Graph-generation audit only. No API evaluation, no answer labels used, and no accuracy claim.

## Result

- Tasks audited: `50`
- DAG graphs: `50`
- Graphs with any PN: `50`
- Graphs with all PN roles: `13`
- Graphs with PN chain: `2`
- Graphs with terminal router: `42`
- Contract-ready graphs: `2`
- Mean nodes: `7.58`
- Mean PN roles: `3.44`
- Graph audit pass: `False`

## Boundary

Only question text was used to generate task embeddings. No answer labels or API calls were used.

## Next

Use audit result to decide whether to run more graph-policy training or only a tiny API smoke.
