# R093 R092 Forced-Template Clean/Noisy Audit Report

**Claim boundary**: clean/noisy audit of R092 full forced-template validation, not a new method

- Tasks: `34`
- Clean-label counts: `{'noisy': 6, 'clean': 28}`
- Overall: `{'baseline_solved': 28, 'forced_template_solved': 25, 'gate_solved': 27, 'fix_harm': {'fix': 1, 'harm': 2}}`
- Decision-field violations: `0`

## Buckets

### noisy

- Tasks: `6`
- ARG baseline solved: `1/6`
- Forced-template solved: `1/6`
- R088-gated solved: `2/6`
- Fix/harm vs ARG: `{'fix': 1, 'harm': 0}`
- Fix tasks: `['task_108']`
- Harm tasks: `[]`

### clean

- Tasks: `28`
- ARG baseline solved: `27/28`
- Forced-template solved: `24/28`
- R088-gated solved: `25/28`
- Fix/harm vs ARG: `{'fix': 0, 'harm': 2}`
- Fix tasks: `[]`
- Harm tasks: `['task_8', 'task_188']`

## Fix/Harm Rows

| Task | Audit label | ARG | Forced template | Gate | Gold | Rationale issue |
| --- | --- | --- | --- | --- | --- | --- |
| `task_8` | `clean` | `E` | `A` | `A` | `E` | `none` |
| `task_108` | `noisy` | `B` | `D` | `D` | `D` | `arithmetic_error` |
| `task_188` | `clean` | `D` | `C` | `C` | `D` | `none` |

## Interpretation

R092's only official fix is on a noisy row (`task_108`), while both official harms (`task_8`, `task_188`) are clean rows. This makes rank-1 forced templates plus the current exact-contract gate unsuitable as a main SCI-Q2 result. Future selectors must separate clean harms from noisy-label fixes before another full API run.
