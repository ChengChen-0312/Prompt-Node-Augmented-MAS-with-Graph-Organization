# R253 MMLU Tiny Transfer API Diagnostic

**Claim boundary**: Tiny same-model transfer diagnostic only; not a broad held-out result, transfer proof, or SCI-Q2 readiness claim.

- Records: `80`
- Evaluated records: `80`
- API required/executed/errors: `48/48/0`
- Correct: `49`
- Accuracy: `0.6125`
- Fixes/harms vs ARG baseline: `11` / `2`
- Cost: `$0.109050`
- Prompt/completion tokens: `12738/3024`

## By Variant

| Variant | Records | Correct | Accuracy | Fix/Harm | API executed/errors |
|---|---:|---:|---:|---:|---:|
| `abstain_keep_arg` | `16` | `8` | `0.5` | `0/0` | `0/0` |
| `arg_baseline_fixed` | `16` | `8` | `0.5` | `0/0` | `0/0` |
| `node_only_no_promptedge_text` | `16` | `11` | `0.6875` | `4/1` | `16/0` |
| `plain_requery` | `16` | `12` | `0.75` | `4/0` | `16/0` |
| `proposed_promptnode_promptedge` | `16` | `10` | `0.625` | `3/1` | `16/0` |

## Boundary

This diagnostic uses the R252 preflighted tiny16 set only. It can motivate the next transfer experiment, but by itself it is not a SCI-Q2 result claim.
