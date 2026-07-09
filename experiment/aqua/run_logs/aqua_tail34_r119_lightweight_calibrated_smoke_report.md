# R119 Lightweight Calibrated Probe Smoke

**Claim boundary**: four-task prospective calibrated-probe smoke only; not broad held-out accuracy or SCI-ready claim

- Probe protocol: `calibrated_single_view_probe`
- Learned rule: `diff_and_top_score_ge_3_or_split`
- Tasks: `4`
- Selected accuracy: `2/4`
- ARG baseline accuracy: `3/4`
- Calibrated-only accuracy: `2/4`
- Delta vs ARG baseline: `-1`
- Switch tasks: `['task_250']`
- Suppressed calibrated harms: `[]`
- Fix/Harm: `0/1`
- Max PromptNode views per task: `1`
- Policy-input violations: `0`
- Cost: `$0.235285`
- Prompt tokens: `16967`
- Completion tokens: `10030`

| Task | ARG | Calibrated | Proxy action | Selected | Truth | Top score | Fix | Harm |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `task_8` | `B` | `C` | `fallback_to_arg` | `B` | `E` | `1` | `False` | `False` |
| `task_108` | `D` | `D` | `fallback_to_arg` | `D` | `D` | `2` | `False` | `False` |
| `task_188` | `D` | `D` | `fallback_to_arg` | `D` | `D` | `2` | `False` | `False` |
| `task_250` | `E` | `A` | `switch_to_objective` | `A` | `E` | `3` | `False` | `True` |

## Interpretation

R119 is the prospective smoke counterpart to R118. It runs one calibrated PromptNode view per regression task and applies the R113 non-leaky proxy rule. Passing this smoke can justify a larger measured run; it cannot by itself support a broad held-out or SCI-ready accuracy claim.
