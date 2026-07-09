# R094 Baseline-Split Protected Forced-Template Gate Report

**Claim boundary**: label-free replay over R092 traces; official gain is noisy-only, not SCI main result

- Tasks: `34`
- ARG baseline solved: `28/34`
- Forced-template solved: `25/34`
- R088-gated solved: `27/34`
- Baseline-split gate solved: `29/34`
- Split gate fix/harm vs ARG: `{'fix': 1, 'harm': 0}`
- Accepted switch tasks: `['task_108']`
- Suppressed switch tasks: `['task_8', 'task_188']`
- Clean/noisy buckets: `{'noisy': {'num_tasks': 6, 'baseline_solved': 1, 'forced_template_solved': 1, 'gate_solved': 2, 'fix_harm': {'fix': 1, 'harm': 0}, 'fix_tasks': ['task_108'], 'harm_tasks': []}, 'clean': {'num_tasks': 28, 'baseline_solved': 27, 'forced_template_solved': 24, 'gate_solved': 27, 'fix_harm': {'fix': 0, 'harm': 0}, 'fix_tasks': [], 'harm_tasks': []}}`
- Decision-field violations: `0`
- Forced-template cost inherited from R092: `$1.286050`

## Switch Rows

| Task | Audit label | ARG | Forced template | Split gate | Gold | Action | Reason | Baseline valid/majority votes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `task_114` | `noisy` | `C` | `E` | `C` | `D` | `fallback_to_arg` | `r088_rejects_template` | `1`/`1` |
| `task_56` | `clean` | `A` | `E` | `A` | `A` | `fallback_to_arg` | `r088_rejects_template` | `1`/`1` |
| `task_59` | `noisy` | `B` | `E` | `B` | `C` | `fallback_to_arg` | `r088_rejects_template` | `2`/`2` |
| `task_8` | `clean` | `E` | `A` | `E` | `E` | `fallback_to_arg` | `baseline_not_split_suppresses_switch` | `1`/`1` |
| `task_108` | `noisy` | `B` | `D` | `D` | `D` | `accept_template` | `baseline_direct_split_allows_switch` | `2`/`1` |
| `task_188` | `clean` | `D` | `C` | `D` | `D` | `fallback_to_arg` | `baseline_not_split_suppresses_switch` | `2`/`2` |
| `task_6` | `noisy` | `D` | `E` | `D` | `D` | `fallback_to_arg` | `r088_rejects_template` | `2`/`1` |

## Interpretation

The baseline-split gate is label-free and suppresses the two clean harms from R092 while keeping `task_108`. However, the retained improvement is noisy-only: clean accuracy ties ARG. This is a candidate safety gate or ablation, not a final SCI-Q2 main result.
