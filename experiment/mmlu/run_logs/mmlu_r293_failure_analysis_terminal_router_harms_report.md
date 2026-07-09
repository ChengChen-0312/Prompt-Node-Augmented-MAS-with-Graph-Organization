# R293 Failure Analysis: PromptNode Transfer Harms

**Claim boundary**: Offline failure analysis only. It explains observed R291 harms and does not support a transfer improvement claim.

- Matched tasks: `24`
- Fix/harm: `0/2`
- Harms with specialist role loss: `1`
- Transfer claim supported: `False`

## Harm Records

| Task | Subject | ARG | PromptNode | Truth | Specialist roles |
|---|---|---:|---:|---:|---:|
| `MMLU-college_mathematics_test-17` | `college_mathematics` | `C` | `B` | `C` | `1` -> `0` |
| `MMLU-high_school_mathematics_test-63` | `high_school_mathematics` | `D` | `B` | `D` | `1` -> `1` |

## Mechanism Hypothesis

The constrained decoder optimizes for PN chain completeness but not task-specialist coverage. On harms, selected graphs can replace Mathematician/Programmer/Knowlegable Expert evidence with Historian-heavy PN chains, causing the router to preserve a well-structured but wrong contract.

## Next

Revise graph selection/training objective to jointly require PN contract structure and specialist-role preservation before running more API.
