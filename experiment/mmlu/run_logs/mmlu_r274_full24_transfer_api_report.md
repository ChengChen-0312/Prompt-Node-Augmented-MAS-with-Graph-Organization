# R274 MMLU Full24 Transfer API Diagnostic

**Claim boundary**: Full24 same-model diagnostic only; selector replay and claim audit required before transfer claims.

- Records: `120`
- Evaluated records: `120`
- API required/executed/errors: `72/72/0`
- Correct: `65`
- Accuracy: `0.5416666666666666`
- Fixes/harms vs ARG baseline: `9` / `4`
- Cost: `$0.163695`
- Prompt/completion tokens: `19122/4539`

## By Variant

| Variant | Records | Correct | Accuracy | Fix/Harm | API executed/errors |
|---|---:|---:|---:|---:|---:|
| `abstain_keep_arg` | `24` | `12` | `0.5` | `0/0` | `0/0` |
| `arg_baseline_fixed` | `24` | `12` | `0.5` | `0/0` | `0/0` |
| `node_only_no_promptedge_text` | `24` | `13` | `0.5416666666666666` | `3/2` | `24/0` |
| `plain_requery` | `24` | `15` | `0.625` | `3/0` | `24/0` |
| `proposed_promptnode_promptedge` | `24` | `13` | `0.5416666666666666` | `3/2` | `24/0` |

## Boundary

This is a same-model full24 diagnostic. It is broader than tiny16 but still not a definitive SCI-Q2 transfer result until selector replay and claim audit are complete.
