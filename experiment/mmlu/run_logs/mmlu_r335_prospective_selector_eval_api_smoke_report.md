# R335 Prospective Selector Eval API Smoke

**Claim boundary**: R335 is a bounded API smoke only. It cannot support a paper claim by itself.

- Tasks: `6`
- Records/API calls: `18`
- API executed: `18`

## By Variant

| Variant | Correct | Records | Accuracy | Fixes | Harms |
|---|---:|---:|---:|---:|---:|
| `arg_baseline_direct` | `4` | `6` | `0.6666666666666666` | `0` | `0` |
| `cost_matched_plain_requery` | `2` | `6` | `0.3333333333333333` | `0` | `2` |
| `selector_promptnode_promptedge_policy` | `4` | `6` | `0.6666666666666666` | `0` | `0` |

- Next required run: `R336_prospective_selector_eval_smoke_analysis`
