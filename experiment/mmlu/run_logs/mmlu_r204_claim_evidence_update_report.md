# R204 Claim-Evidence Update

**Claim boundary**: evidence organization only. No API evaluation and no new accuracy claim.

## Updated Claims

| Claim | Updated Status | Evidence |
|---|---|---|
| Projected PromptEdge improves MMLU transfer accuracy | Not supported by random12 | R202 baseline `11/12`, projected `11/12` |
| Low harm risk on small MMLU slices | Weakly supported | R192 harm `0/4`, R196 harm `0/4`, R202 harm `0/12` |
| Hybrid projection is structurally necessary | Supported as graph evidence | R202 raw ready `0/12`, projected ready `12/12` |
| MMLU is ready as SCI-Q2 main result | Not supported | No random gain; learned edge-linking weak |

## Research Direction

Keep AQuA R065 as the strongest current accuracy signal. MMLU currently functions as robustness/safety and negative evidence. The next method iteration should improve learned edge ordering or router-final design before spending more API.
