# R256 MMLU Transfer Failure Mechanism Analysis

**Claim boundary**: No-API failure analysis only; supports redesign decisions, not accuracy claims.

- Tasks: `16`
- Interesting cases: `6`
- Mode counts: `{'all_api_fix': 2, 'graph_prompt_regression_vs_plain': 2, 'no_interesting_delta': 10, 'node_fix_lost_by_promptedge': 1, 'plain_fix_lost_by_proposed': 2, 'promptnode_family_control_harm': 1, 'proposed_control_harm': 1, 'proposed_over_plain_fix': 1}`

## Key Cases

### MMLU-abstract_algebra_test-53

- Role: `arg_error`; ARG/true: `A` / `C`
- Tags: `['all_api_fix']`
- Plain/node/proposed: `C` / `C` / `C`

### MMLU-college_chemistry_test-62

- Role: `arg_error`; ARG/true: `A` / `B`
- Tags: `['all_api_fix']`
- Plain/node/proposed: `B` / `B` / `B`

### MMLU-college_mathematics_test-17

- Role: `matched_control`; ARG/true: `C` / `C`
- Tags: `['graph_prompt_regression_vs_plain', 'promptnode_family_control_harm', 'proposed_control_harm']`
- Plain/node/proposed: `C` / `B` / `A`

### MMLU-college_mathematics_test-26

- Role: `arg_error`; ARG/true: `C` / `D`
- Tags: `['node_fix_lost_by_promptedge', 'plain_fix_lost_by_proposed']`
- Plain/node/proposed: `D` / `D` / `C`

### MMLU-conceptual_physics_test-41

- Role: `arg_error`; ARG/true: `B` / `D`
- Tags: `['graph_prompt_regression_vs_plain', 'plain_fix_lost_by_proposed']`
- Plain/node/proposed: `D` / `A` / `A`

### MMLU-elementary_mathematics_test-222

- Role: `arg_error`; ARG/true: `A` / `D`
- Tags: `['proposed_over_plain_fix']`
- Plain/node/proposed: `A` / `D` / `D`

## V2 Constraints

- Do not treat PromptEdge text as intrinsically beneficial; R254 shows node-only beats proposed.
- Add a selector gate: use PN/PE only when it improves over plain reasoning signals or preserves controls.
- Reduce over-conditioning on ARG initial choice and edge procedure when plain requery already solves the item.
- Add a harm guard for matched-control cases before switching away from ARG.

## Interpretation

The main failure is not lack of model capability: plain requery fixes more items than proposed PN/PE. The next method should add a selector and safer edge policy instead of adding more edge text.
