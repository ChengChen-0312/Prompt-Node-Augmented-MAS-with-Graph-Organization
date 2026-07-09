# R175 Five-Iteration SCI-Q2 Goal Audit

**Claim boundary**: Goal audit only. Direction is aligned with SCI-Q2 method development, but answer-accuracy superiority over ARG is not proven and broad API remains blocked.

- Window: `R171-R175`
- Status: `aligned_but_override_learning_blocked`
- Drift: `False`
- SCI-Q2 ready: `False`
- Broad API allowed: `False`
- Bounded accuracy API allowed: `False`
- Next audit: `R180`

## Evidence

| Run | Type | Key result | Lesson |
| --- | --- | --- | --- |
| `R171` | `bounded smoke` | selected `2/4`, baseline `4/4`, fix/harm `0/2` | selector+contract alone can switch to PN_Router abstention and harm clean rows |
| `R172` | `abstention fallback replay` | selected `4/4`, baseline `4/4`, fix/harm `0/0` | label-free abstention guard removes harm but gives no gain |
| `R173` | `action-aware selector replay` | selected `4/4`, baseline `4/4`, fix/harm `-` | preserve-safe insertion must not be treated as switch permission |
| `R174` | `two-head target audit` | insertion `76`, override `4`, override recall `0.0` | insertion head is supported, learned override head is not |

## Decision

The work remains aligned with the user goal because it preserves R001-compatible graph training, first-class PromptNode insertion, and typed PromptEdge semantics. However, the paper claim is not ready: the current evidence supports insertion learning, not robust answer override or held-out superiority over ARG.

## Allowed Next Run

- Run: `R176`
- Type: `non-api switch-critical target expansion or mining`
- Requirement: do not use gold answers, is_solved, clean/noisy labels, or task ids as selector inputs
- Requirement: separate insertion targets from override targets
- Requirement: report source of every switch-critical target
- Requirement: keep AQuA sync20 diagnostic only
- Requirement: do not run broad API before override target evidence improves
