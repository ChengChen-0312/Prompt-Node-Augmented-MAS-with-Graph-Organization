# R189 MMLU PromptEdge Projection Audit

**Claim boundary**: No-API graph projection audit only. This supports a hybrid constrained-decoder claim, not a fully learned edge-linking claim and not an answer accuracy claim.

## Result

- Tasks audited: `50`
- Raw contract-ready graphs: `2`
- Projected contract-ready graphs: `50`
- Raw PN-chain graphs: `2`
- Projected PN-chain graphs: `50`
- Raw DAG graphs: `50`
- Projected DAG graphs: `50`
- Projection audit pass: `True`

## Paper Boundary

May claim structural projection yields execution-ready PromptEdge graphs; must not claim learned edge policy without an ablation separating raw learned graph from projection.

## Next

R190 goal audit should decide whether a tiny API smoke is justified under a hybrid constrained-decoder claim.
