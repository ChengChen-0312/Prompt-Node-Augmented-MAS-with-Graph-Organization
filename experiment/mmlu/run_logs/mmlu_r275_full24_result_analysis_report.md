# R254 MMLU Tiny Transfer Result Analysis

**Claim boundary**: Result analysis only; R253 is a tiny diagnostic and does not support SCI-Q2 readiness or transfer superiority.

## Variant Results

| Variant | Correct | Accuracy | Fix/Harm |
|---|---:|---:|---:|
| `arg_baseline_fixed` | `12`/`24` | `0.5` | `0/0` |
| `abstain_keep_arg` | `12`/`24` | `0.5` | `0/0` |
| `plain_requery` | `15`/`24` | `0.625` | `3/0` |
| `node_only_no_promptedge_text` | `13`/`24` | `0.5416666666666666` | `3/2` |
| `proposed_promptnode_promptedge` | `13`/`24` | `0.5416666666666666` | `3/2` |

## Claim Assessment

- Proposed beats ARG baseline: `True` (`1` net correct)
- Proposed beats plain requery: `False`
- Proposed beats node-only: `False`
- PromptEdge text gain supported: `False`
- Transfer superiority supported: `False`

## Interpretation

The tiny transfer diagnostic is negative for the current PN/PE prompt design: proposed PN/PE improves over fixed ARG but loses to plain requery and node-only. This supports a redesign/selector lesson, not a transfer superiority claim.
