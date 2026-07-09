# R277 Transfer Claim Update

**Claim boundary**: Claim update only; no API and no new accuracy claim.

- Claim supported: `partial`
- SCI-Q2 ready: `False`
- R276 correct/fix-harm: `13` / `1/0`
- Beats ARG/plain/node/proposed: `True` / `False` / `False` / `False`

## Suggested Claim Revision

PromptEdge should be framed as a gated/prunable edge; full24 replay supports a prospective selector, not final transfer superiority.

## Next Experiments Needed

- Prospective full24 or transfer100 run with the edge-gated policy in the prompt, not post-hoc replay.
- A held-out split for selector rule selection vs evaluation to avoid tiny/full24 overfitting.
- Negative controls: always-plain, always-node, always-promptedge, random-gated edge.
