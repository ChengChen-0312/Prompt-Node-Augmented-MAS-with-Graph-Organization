# R239 Claim Matrix And Paper Plan Update

**Claim boundary**: planning and claim-boundary update only. No API, no new accuracy claim, and no SCI-Q2 readiness claim.

## Updated Claim Matrix

| Claim | Status | Evidence |
|---|---|---|
| Prompt-level router beats controls | Not supported | R233: proposed `1/4`, node-only `1/4`, abstain `1/4`, always `1/4`; R234: proposed matches always/node-only `4/4` |
| Prompt-level router is robust | Not supported | R234: clean harm on `task_95` |
| Conservative abstention policy removes the R233 clean harm | Supported offline | R237 R233 subset: `2/4` vs baseline `1/4`, fix/harm `1/0` |
| Conservative abstention policy improves first200 offline replay | Supported offline | R236: `170/200` vs baseline `165/200`, fix/harm `5/0`, clean fix/harm `1/0` |
| Conservative abstention policy improves frozen_eval replay | Supported offline, small | R237: frozen_eval `29/34` vs `28/34`, fix/harm `1/0` |
| Conservative policy beats matched controls in live API | Not supported | R238 only exports manifests; no live conservative API run |
| Current package is SCI-Q2 ready | Not supported | Still needs held-out/live evaluation, broader transfer, lifecycle evidence, and citation audit |

## Paper Plan Impact

The method should no longer be framed as "ask an LLM router to choose from feature names." R233 shows that fails. The stronger story is:

1. PromptNodes/PromptEdges expose graph-organization evidence before execution.
2. A train-time or explicit graph-policy selector decides when that evidence may alter ARG.
3. The selector has an abstention boundary to protect clean ARG-correct cases.
4. PromptEdge text remains a mechanism to test, not an assumed source of gain.

## Next

R240 must audit whether R236-R239 justify a small future conservative-policy API diagnostic. The default remains no broad API until offline evidence is clean and controls are executable.
