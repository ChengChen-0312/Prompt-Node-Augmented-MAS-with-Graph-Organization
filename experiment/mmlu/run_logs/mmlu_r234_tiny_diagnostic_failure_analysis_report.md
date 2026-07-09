# R234 Tiny Diagnostic Failure Analysis

**Claim boundary**: Failure analysis only; no new API, no superiority claim, and no SCI-Q2 readiness claim.

## Summary

- Tasks: `4`
- Failure modes: `{'baseline_and_objective_wrong': 2, 'objective_correct_router_followed': 1, 'objective_wrong_router_harmed_baseline': 1}`
- Clean labels: `{'clean': 1, 'noisy': 3}`
- Proposed fixes/harms: `1/1`
- Proposed matches always-switch: `4/4`
- Proposed matches node-only: `4/4`
- Baseline correct tasks: `1`
- Objective correct tasks: `1`

## Per-Task Breakdown

| Task | Clean | Baseline | Objective | Proposed | Mode | Fix/Harm |
|---|---|---:|---:|---:|---|---:|
| `task_135` | `noisy` | `NONE` | `D` | `D` | `objective_correct_router_followed` | `1/0` |
| `task_152` | `noisy` | `NONE` | `E` | `E` | `baseline_and_objective_wrong` | `0/0` |
| `task_172` | `noisy` | `C` | `A` | `A` | `baseline_and_objective_wrong` | `0/0` |
| `task_95` | `clean` | `A` | `B` | `B` | `objective_wrong_router_harmed_baseline` | `0/1` |

## Verification

| Test | Result |
|---|---:|
| `tests.test_r234_tiny_diagnostic_failure_analysis` | `4/4` |
| `tests.test_r233_tiny_api_diagnostic_executor` | `6/6` |

## Interpretation

The current prompt-level router is not learning an abstention boundary. It follows the objective prediction on every API-routed task, matching the always-switch control and the node-only control. This explains the balanced `1/1` fix/harm pattern and blocks any expansion of this prompt as a robust SCI-Q2 result.

The next method iteration should train or distill an abstention policy that uses conflict and support features to suppress objective switches when the baseline has strong direct support, instead of asking the LLM router to infer that boundary from feature names.
