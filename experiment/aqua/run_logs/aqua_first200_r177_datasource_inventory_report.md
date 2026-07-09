# R177 Data-Source Inventory

**Claim boundary**: R177 is a file inventory only; it does not create new targets and does not support an accuracy claim.

- Files scanned: `134`
- Train-eligible first200/100/next100 files: `24`
- Diagnostic-only tail34/sync20 files: `108`
- Additional non-test override source beyond first200: `False`
- Tail34 training allowed: `False`
- Sync20 training allowed: `False`

## Switch-Related Train-Eligible Sources

| Path | Rows | Tasks | Slices | Actions |
| --- | ---: | ---: | --- | --- |
| `experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl` | `200` | `200` | `{'aqua_100': 100, 'aqua_next100': 100}` | `{'fallback_to_arg': 189, 'switch_to_objective': 11}` |
| `experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_rows.jsonl` | `800` | `0` | `{'aqua_100': 400, 'aqua_next100': 400}` | `{'preserve_safe_insert': 72, 'suppress_or_fallback': 724, 'switch_critical_insert': 4}` |

## Interpretation

The repository does not contain a larger non-test switch-critical target source beyond the first200 artifacts already audited in R174/R176. Tail34 and sync20 contain useful diagnostics but should not be used to train the override head. The next viable route is to create new non-test objective/graph-policy traces under the same R001-compatible model setting, or move the PromptNode/PromptEdge branch to a transfer dataset with a fresh training/evaluation split.
