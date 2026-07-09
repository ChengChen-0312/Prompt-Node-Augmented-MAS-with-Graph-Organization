# R264 R065 Error-Targeted Strong Teacher Expansion

**Claim boundary**: Targeted strong-teacher ceiling on the three R065 errors only. This is not a deployed robust selector, not a held-out accuracy claim, and not distillation evidence by itself.

- Model: `gpt-4o-2024-08-06`
- Target tasks: `task_139, task_228, task_59`
- Records/API/errors: `12/12/0`
- Leakage pass/violations: `True` / `0`
- Estimated/API cost: `$0.129312` / `$0.002586`
- Tokens prompt/completion: `4375/3217`
- R065 accuracy: `31/34`
- Oracle teacher accuracy: `31/34` via `none`
- Non-oracle majority teacher accuracy: `31/34` via `none`
- Dataset disagreement flags: `task_139, task_228, task_59`

## Task Breakdown

| Task | Gold | R065 | Votes | Oracle fix | Majority selected | Majority fix | Dataset-disagreement flag |
|---|---:|---:|---|---:|---|---:|---:|
| `task_139` | `E` | `D` | `{'D': 4}` | `False` | `D` (teacher_majority) | `False` | `True` |
| `task_228` | `B` | `C` | `{'A': 4}` | `False` | `A` (teacher_majority) | `False` | `True` |
| `task_59` | `C` | `D` | `{'D': 4}` | `False` | `D` (teacher_majority) | `False` | `True` |

## Variant Breakdown

| Variant | Records | Correct on target errors | Accuracy | Fixes | Label counts |
|---|---:|---:|---:|---:|---|
| `pe_adversarial_countercheck` | `3` | `0` | `0.0` | `0` | `{'A': 1, 'D': 2}` |
| `pn_executable_consistency_verifier` | `3` | `0` | `0.0` | `0` | `{'A': 1, 'D': 2}` |
| `pn_option_elimination_verifier` | `3` | `0` | `0.0` | `0` | `{'A': 1, 'D': 2}` |
| `pn_state_ledger_lifecycle_verifier` | `3` | `0` | `0.0` | `0` | `{'A': 1, 'D': 2}` |

## Interpretation

If oracle_teacher_accuracy exceeds R065, distill the general verifier signal; otherwise audit label noise and do not optimize toward these labels.
