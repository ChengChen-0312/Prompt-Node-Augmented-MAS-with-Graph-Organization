# R199 Claim-Evidence Matrix

**Claim boundary**: evidence organization only. No API evaluation and no new accuracy claim.

| Claim | Status | Evidence | Limitation |
|---|---|---|---|
| First-class PN/PE graph structure before execution | Supported | R181-R184 | Engineering evidence only |
| PN-capable generator learns to emit PN roles | Partially supported | R188 any-PN `50/50`, role acc `45.03` | Raw edge linking weak |
| Fully learned PromptEdge linking | Not supported | R187 `1/50`, R188 `2/50` contract-ready | Needs better training/decoder |
| Hybrid constrained decoder yields execution-ready graphs | Supported as graph evidence | R189 projected `50/50` contract-ready | Must ablate projection |
| MMLU transfer accuracy improves over ARG | Not yet supported | R192 no harm, R196 diagnostic fixes `2/4` | R196 is baseline-wrong biased |
| No obvious harm in tiny smokes | Weakly supported | R192 harms `0`, R196 harms `0` | Needs random/full held-out |

## Next Evidence Needed

- R200 audit decision on the 12-task random slice.
- If run, unbiased fix/harm and cost-normalized accuracy.
- Projection ablation: raw learned graph vs projected graph.
- Negative controls: no projection, random PN, dense PN, no routing.
