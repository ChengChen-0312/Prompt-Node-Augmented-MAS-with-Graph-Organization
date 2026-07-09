# R226 Cost-Matched ARG Re-query Protocol

**Claim boundary**: Cost-matched ARG protocol only; no API and no accuracy claim.

## Budget

- Cost cap: `$0.450000`
- ARG cost/task estimate: `$0.030421`
- Max tasks: `4`
- Allowed re-queries: `4`
- Estimated total cost: `$0.121684`

## Boundary

This only materializes the cost-matched ARG baseline protocol. It does not spend API budget.

## Verification

| Test | Result |
|---|---:|
| `tests.test_r226_cost_matched_arg_protocol` | `2/2` |

## Interpretation

R226 closes the planning gap that future router-final diagnostics need a cost-matched ARG comparator. It still does not authorize API; it only defines the comparator budget and task list.
