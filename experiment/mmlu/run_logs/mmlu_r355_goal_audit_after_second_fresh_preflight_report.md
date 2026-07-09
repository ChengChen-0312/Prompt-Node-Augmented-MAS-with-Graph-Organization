# R355 Goal Audit After Second Fresh Preflight

**Claim boundary**: R355 is an early goal audit after R354 showed a second fresh split with zero local-template coverage. It redirects the work toward a learned graph policy instead of more hand-written templates.

## Alignment

- `still_aligned_with_sci_q2_goal`: `True`
- `r352_dev_coverage_positive`: `True`
- `r354_fresh_coverage_zero`: `True`
- `local_template_path_failed_as_general_strategy`: `True`
- `overclaiming_blocked`: `True`

## Course Correction

- Stop hand-expanding deterministic templates as the primary path.
- Train or fit a graph-policy selector that predicts when to instantiate PromptNodes/PromptEdges from task features and candidate evidence.
- Use LLM verifier nodes only behind learned safety gates and evidence contracts.
- Treat local tools as one PromptNode family, not the whole method.

- Next required run: `R356_learned_graph_policy_promptnode_design`
