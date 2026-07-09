# R290 Goal Audit After R289

**Claim boundary**: Goal/result audit only. R289 is compared to the existing R162 ARG transfer records on matched task_ids; R282 retrained ARG baseline is still required.

- Goal alignment: `aligned_negative_transfer_result`
- R287 selected contract-ready rate: `0.8333333333333334`
- Matched tasks vs R162: `24`
- R289 correct: `19/24`
- R162 matched correct: `22/24`
- Fix/harm vs R162: `0/3`
- Transfer superiority claim supported: `False`
- SCI-Q2 ready: `False`

## Harm Task IDs

- `MMLU-college_computer_science_test-2`
- `MMLU-high_school_computer_science_test-75`
- `MMLU-high_school_mathematics_test-63`

## Wrong Task IDs

- `MMLU-high_school_statistics_test-32`
- `MMLU-college_computer_science_test-2`
- `MMLU-high_school_computer_science_test-75`
- `MMLU-high_school_mathematics_test-63`
- `MMLU-high_school_physics_test-67`

## Decision

Do not claim MMLU transfer improvement. The graph structure gate improved, but terminal-only router replay underperforms the existing ARG transfer baseline on matched tasks.

## Next Runs

- `R291_all_exposure_replay`
- `R292_r282_arg_retrain_first24_api_baseline`
- `R293_failure_analysis_terminal_router_harms`
- `R294_decision_policy_revision`
- `R295_goal_audit`
