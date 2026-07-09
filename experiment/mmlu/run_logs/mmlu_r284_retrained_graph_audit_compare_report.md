# R284 Retrained MMLU Graph Audit Compare

**Claim boundary**: No-API generated-graph audit only. This supports structural integration checks for retrained checkpoints, not answer accuracy or transfer superiority.

| Checkpoint | Train roles | PN roles in train | Tasks | Any PN | Contract ready | Mean nodes | Mean edges |
|---|---:|---|---:|---:|---:|---:|---:|
| ARG R282 | `6` | `[]` | `24` | `0.00` | `0.00` | `4.79` | `3.79` |
| PromptNode R283 | `9` | `['PN_Memory', 'PN_Router', 'PN_Verifier']` | `24` | `1.00` | `0.04` | `7.75` | `9.58` |

## Claim Gate

- Structural claim supported: `False`
- Accuracy claim supported: `False`
- Transfer superiority claim supported: `False`
- API evaluation authorized next: `False`
- Next goal audit due: `R285`

## Interpretation

R284 only verifies whether retrained checkpoints produce the intended graph families. It deliberately does not use answer labels or API calls.
