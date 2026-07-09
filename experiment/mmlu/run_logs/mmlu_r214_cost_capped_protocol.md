# R214 Cost-Capped Router-Final Protocol

**Claim boundary**: protocol only. No API evaluation and no accuracy claim.

## Decision

API is **not eligible now**.

R211-R213 passed the schema, leakage, and logging gates, but the current router-final labels are still `abstain/NONE`. Running another API smoke now would mostly repeat the projected PN/PE path with better logs. It would not test a real answer-changing router-final method.

## Prerequisites Before Any API

- R215 goal audit must pass.
- Runtime evaluator must include an answer-changing router-final decision stage or target labels beyond `abstain/NONE`.
- R213 logging contract must remain intact.
- Leakage scan must pass for all model-visible router-final features.
- User-approved cost cap must be explicit.

## Candidate Tiny Diagnostic Protocol

This protocol is diagnostic only, not a paper-level claim.

| Field | Value |
|---|---|
| Max tasks | `4` |
| Model | `gpt-4o-2024-08-06` |
| Baseline | R162 MMLU ARG baseline |
| Cost cap | `$0.45` |
| Selection | mixed diagnostic |
| Baseline-wrong tasks | `MMLU-high_school_statistics_test-32`, `MMLU-high_school_physics_test-67` |
| Baseline-correct controls | 2 fixed-seed random transfer100 tasks excluding R192/R196/R202 tasks |

## Required Logs

- raw graph
- projected graph
- PromptEdge metadata
- PromptEdge permissions
- router-final schema
- raw/projected graph audits
- cost and token counts

## Success Criteria

- `harms == 0` on baseline-correct controls.
- At least one diagnostic fix on baseline-wrong tasks if an answer-changing router is active.
- Leakage scan passes on logs and model-visible fields.
- Cost stays at or below `$0.45`.

## Failure Criteria

- Any control harm.
- Missing graph/router logs.
- Leakage violation.
- Cost cap exceeded.
- Router remains abstain-only and produces no new evidence.

## Next

R215 is mandatory before any API. If R215 confirms the router-final path is still abstain-only, the next step should be target redesign, not API.
