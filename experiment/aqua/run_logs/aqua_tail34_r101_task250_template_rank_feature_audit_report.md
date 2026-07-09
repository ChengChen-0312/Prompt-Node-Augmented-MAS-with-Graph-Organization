# R101 Task250 Template Rank Feature Audit

**Claim boundary**: task250 metadata feature audit; heuristic hypothesis only, not a general selector

- Matching ranks: `[2, 5]`
- Nonmatching ranks: `[1, 3, 4]`
- Heuristic: `support_count<=5 AND has_math_solver AND (has_inspector OR upstream_agent_count>=3)`
- Heuristic selected ranks: `[2, 5]`
- Heuristic precision: `2/2`
- Heuristic recall: `2/2`
- Heuristic input field violations: `0`

| Rank | Prediction | Matches E | Support | Upstream role counts | Upstream count | Heuristic selected |
| ---: | --- | --- | ---: | --- | ---: | --- |
| `1` | `A` | `False` | `35` | `{'Math Solver': 1, 'Programming Expert': 1}` | `2` | `False` |
| `2` | `E` | `True` | `5` | `{'Inspector': 1, 'Math Solver': 1}` | `2` | `True` |
| `3` | `A` | `False` | `5` | `{'Math Solver': 2}` | `2` | `False` |
| `4` | `A` | `False` | `4` | `{'Inspector': 1, 'Programming Expert': 1}` | `2` | `False` |
| `5` | `E` | `True` | `4` | `{'Math Solver': 1, 'Programming Expert': 2}` | `3` | `True` |

## Interpretation

This audit gives a label-free metadata hypothesis for why ranks 2 and 5 worked on `task_250`: low support templates that keep Math Solver and either Inspector oversight or a wider upstream-agent fan-in. This is not a general selector until it is tested on clean-safe regression tasks.
