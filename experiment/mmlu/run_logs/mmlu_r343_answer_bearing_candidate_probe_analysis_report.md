# R343 Answer-Bearing Candidate Probe Failure Analysis

**Claim boundary**: R343 analyzes the executed R342 four-task mechanism probe only. It blocks same-design prompt-only answer-bearing verifier expansion because every candidate followed the wrong ARG baseline.

- Records: `4`
- API executed: `4`
- Candidate labels: `4`
- Candidate correct: `0`
- Candidate repairs: `0`
- Followed wrong baseline: `4`
- Root causes: `['answer_bearing_candidates_not_reliable', 'verifier_candidates_follow_wrong_baseline', 'weak_or_non_executable_evidence', 'prompt_only_answer_verifiers_not_sufficient']`

## Task Rows

- `MMLU-high_school_mathematics_test-0` `coordinate_geometry_verifier`: baseline `A`, candidate `A`, gold `D`, evidence `1`
- `MMLU-college_mathematics_test-1` `algebraic_structure_verifier`: baseline `B`, candidate `B`, gold `D`, evidence `0`
- `MMLU-college_mathematics_test-2` `algebraic_structure_verifier`: baseline `B`, candidate `B`, gold `D`, evidence `1`
- `MMLU-college_chemistry_test-3` `chemistry_balancer_verifier`: baseline `A`, candidate `A`, gold `B`, evidence `1`

- Next required run: `R344_goal_audit_after_candidate_generator_probe`
