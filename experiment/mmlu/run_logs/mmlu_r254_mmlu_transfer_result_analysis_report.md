# R254 MMLU Tiny Transfer Result Analysis

**Claim boundary**: Result analysis only; R253 is a tiny diagnostic and does not support SCI-Q2 readiness or transfer superiority.

## Variant Results

| Variant | Correct | Accuracy | Fix/Harm |
|---|---:|---:|---:|
| `arg_baseline_fixed` | `8`/`16` | `0.5` | `0/0` |
| `abstain_keep_arg` | `8`/`16` | `0.5` | `0/0` |
| `plain_requery` | `12`/`16` | `0.75` | `4/0` |
| `node_only_no_promptedge_text` | `11`/`16` | `0.6875` | `4/1` |
| `proposed_promptnode_promptedge` | `10`/`16` | `0.625` | `3/1` |

## Claim Assessment

- Proposed beats ARG baseline: `True` (`2` net correct)
- Proposed beats plain requery: `False`
- Proposed beats node-only: `False`
- PromptEdge text gain supported: `False`
- Transfer superiority supported: `False`

## Interpretation

The tiny transfer diagnostic is negative for the current PN/PE prompt design: proposed PN/PE improves over fixed ARG but loses to plain requery and node-only. This supports a redesign/selector lesson, not a transfer superiority claim.
