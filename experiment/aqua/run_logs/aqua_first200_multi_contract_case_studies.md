# AQuA First200 R035 PromptNode Clean-Fix Case Studies

**Claim boundary**: These are exploratory first200 case studies. They illustrate the R035 pure multi-contract PromptNode mechanism, but they are not held-out tail34 or transfer validation claims.

## Clean Fix Table

| Task | Slice | Audit | Gold | ARG | Ensemble | Selected | Evidence |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| task_122 | aqua_100 | clean | A | C | A | A | strong A=3, E=1 |
| task_197 | aqua_next100 | clean | C | A | A | C | direct-consensus C=2; strong A=2, C=2 |
| task_67 | aqua_next100 | clean | B | A | B | B | direct-consensus B=2; strong B=2 |

## Per-View Contract Evidence

| Task | PromptNode view contracts | Question excerpt |
| --- | --- | --- |
| task_122 | router:A/EXACT_MATCH/direct=0/match=no; candidate:A/EXACT_MATCH/direct=1/match=yes; conservative:A/EXACT_MATCH/direct=0/match=no; calibrated:E/EXACT_MATCH/direct=0/match=no | Kevin drove from A to B at a constant speed of 70 mph. Once he reached B, he turned right around with pause, and returned to A at a constant speed of 90 mph. Exactly 3 hours bef... |
| task_197 | router:C/EXACT_MATCH/direct=2/match=yes; candidate:A/EXACT_MATCH/direct=1/match=no; conservative:A/EXACT_MATCH/direct=1/match=yes; calibrated:C/EXACT_MATCH/direct=2/match=yes | In the coordinate plane, a triangle has vertices at (a,0), (b,0), and (x,y). If a>x>b>0>y, which of the following represents the area of that triangle? Choices: A)(ay−by)/2 B)(a... |
| task_67 | router:B/EQUIVALENT_FORM/direct=2/match=yes; candidate:-/WEAK/direct=1/match=no; conservative:-/WEAK/direct=2/match=no; calibrated:B/EXACT_MATCH/direct=2/match=yes | Assistants are needed to prepare for preparation. Each helper can make either 2 large cakes or 35 small cakes/hr. The kitchen is available for 3 hours and 20 large cakes & 700 s... |

## Interpretation

Observation: every listed row is clean under the option-binding audit, ARG is wrong, and R035 pure multi-contract PromptNode selection is correct.

Interpretation: these cases support the mechanism-level story that multiple virtual PromptNode views can provide safe option-binding evidence beyond the ARG baseline.

Next step: repeat this extraction on pre-registered tail34 and transfer multiple-choice math once same-model traces are available.
