# R359 Learned Graph-Policy Source Invariance Audit

**Claim boundary**: R359 audits the R358 offline model for source-run shortcut learning. It blocks fresh evaluation until source-specific features are removed or neutralized.

- Source-run risk detected: `True`
- Risky top features: `['source_run=R352']`

## Course Correction

- Remove source_run and source-specific proxy features before fresh evaluation.
- Retrain using only task-shape, candidate-evidence, PromptNode, PromptEdge, and lifecycle features.
- Report R358 perfect offline score only as a failed shortcut-learning audit, not as method evidence.

- Next required run: `R360_source_invariant_graph_policy_retraining`
