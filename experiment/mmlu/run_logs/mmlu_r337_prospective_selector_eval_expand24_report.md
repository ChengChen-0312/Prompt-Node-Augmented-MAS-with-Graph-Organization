# R335 Prospective Selector Eval API Smoke

**Claim boundary**: R337 expands the R335 smoke to 24 held-out tasks. It remains a bounded prospective diagnostic, not a final paper claim.

- Tasks: `24`
- Records/API calls: `72`
- API executed: `True`

## By Variant

| Variant | Correct | Records | Accuracy | Fixes | Harms |
|---|---:|---:|---:|---:|---:|
| `arg_baseline_direct` | `20` | `24` | `0.8333333333333334` | `0` | `0` |
| `cost_matched_plain_requery` | `17` | `24` | `0.7083333333333334` | `0` | `3` |
| `selector_promptnode_promptedge_policy` | `20` | `24` | `0.8333333333333334` | `0` | `0` |

- Next required run: `R338_goal_audit_after_prospective_eval`
