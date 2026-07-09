# R451 Journal Scope Gap Matrix

**Claim boundary**: R451 maps the current manuscript claims to JAIR and KAIS scope evidence. It does not change experiments, transmit audit material, or certify submission readiness.

- Primary target: `JAIR`
- Secondary target: `KAIS`

## Scope Terms

- `JAIR`: `agents_and_multi_agent_systems`, `machine_learning`, `knowledge_representation`, `automated_reasoning`, `natural_language`
- `KAIS`: `knowledge_systems`, `advanced_information_systems`, `theoretical_foundations`, `infrastructure`, `enabling_technologies`

## Matrix

### PromptNode as first-class MAS graph organization element

- JAIR fit: `strong`
- KAIS fit: `medium`
- Current evidence: Method defines typed PromptNodes, read/write/forward PromptEdges, and lifecycle actions.
- Gap: Need clearer theoretical positioning as graph organization rather than prompt engineering.
- Action: Tighten abstract/introduction around MAS graph organization and reliability.

### Held-out improvements over ARG-Designer on AQuA and MMLU STEM

- JAIR fit: `strong`
- KAIS fit: `medium`
- Current evidence: AQuA audit-clean 31/31 vs 28/31; MMLU STEM 95/97 vs 88/97.
- Gap: External result-integrity audit pending.
- Action: Do not authorize paper claims until external experiment and paper-claim audits are imported.

### Non-math generality

- JAIR fit: `medium`
- KAIS fit: `medium`
- Current evidence: Mixed non-STEM no-harm 41/48 vs 41/48; DefinitionChallenge 22/24 vs 21/24.
- Gap: No broad positive non-math improvement is supported.
- Action: State no-harm and narrow positive DefinitionChallenge result; avoid broad nonmath improvement claims.

### Reliability through audit-clean evaluation

- JAIR fit: `strong`
- KAIS fit: `strong`
- Current evidence: AQuA and MMLU label-noise audits are recorded; appendix finalization pending.
- Gap: Appendix text needs final task-level documentation.
- Action: Finalize audit-clean appendix and sensitivity analysis before submission.

### Knowledge-system framing

- JAIR fit: `medium`
- KAIS fit: `strong`
- Current evidence: PromptNodes carry structured instructions, verifier states, and memory-like graph state.
- Gap: Current manuscript is not framed as a knowledge/information system.
- Action: Keep KAIS as backup unless rewriting around knowledge-state propagation and information-system reliability.

### Cost and deployment practicality

- JAIR fit: `medium`
- KAIS fit: `medium`
- Current evidence: Cost table includes exact or probe-estimated token/cost fields and R065/R095 comparisons.
- Gap: Some cost numbers are probe estimates, not exact original reruns.
- Action: Label cost provenance clearly and avoid overstating cost-normalized dominance.

## Claim Tightening Actions

- `no_broad_nonmath_improvement_claim`
- `label_cost_provenance_exact_vs_probe`
- `external_audit_before_claim_authorization`
- `appendix_label_noise_disclosure`
- `position_promptnodes_as_graph_organization_not_answer_patch`

## Sources

- https://www.jair.org/
- https://link.springer.com/journal/10115/aims-and-scope
- https://www.journalmetrics.org/journal/journal-of-artificial-intelligence-research
- https://www.journalmetrics.org/journal/knowledge-and-information-systems

- Paper claim authorized: `False`
- SCI-Q2 ready: `False`
- Next required run: `R452_five_run_goal_audit_and_compile_probe`
