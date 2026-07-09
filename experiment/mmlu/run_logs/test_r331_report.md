# Paper Plan

**Title**: PromptNode-Augmented Multi-Agent Graphs for Robust Reasoning
**One-sentence contribution**: We introduce PromptNodes as first-class virtual graph elements with typed identities, PromptEdges, and lifecycle actions, improving audited AQuA tail and MMLU STEM reasoning over ARG-Designer while exposing clear no-harm and training boundaries.
**Venue**: SCI_Q2_JOURNAL
**Type**: method_and_empirical_diagnostic
**Section count**: 8

## Claims-Evidence Matrix

| ID | Claim | Evidence | Status | Section |
|---|---|---|---|---|
| `C1_aqua_clean_gain` | PromptNode-guided graph organization improves ARG-Designer on the audited AQuA tail split. | R321 main table: ARG 28/31 vs PromptNode 31/31 after excluding task_59/task_139/task_228. | `supported` | §5.1 |
| `C2_mmlu_stem_gain` | The method transfers to MMLU STEM with a clean positive gain over ARG-Designer. | R321/R306: ARG 88/97 vs PromptNode 95/97; fix/harm 7/0. | `supported` | §5.2 |
| `C3_nonstem_no_harm_boundary` | Non-STEM transfer currently supports a no-harm boundary, not an improvement claim. | R312/R321: ARG 37/40 vs safety replay 37/40; fix/harm 0/0; raw non-STEM 34/40 is reported as limitation. | `supported_boundary` | §5.3 and §7 |
| `C4_promptedge_selector_safety` | PromptEdge text is a safety feature for train-time graph-policy selection. | R327: no-family selector without edge text creates 1 false forward; with edge text creates 0. | `partial_offline` | §6.2 |
| `C5_broad_general_improvement` | PromptNode universally improves multi-agent reasoning across all multiple-choice datasets. | Contradicted by raw non-STEM negative transfer; no prospective selector API evaluation yet. | `blocked` | Not claimed |

## Structure

### Abstract
- **Page budget**: 0.25 pages
- **Contents**: State the graph-organization problem, PromptNode/PromptEdge method, AQuA/MMLU gains, no-harm boundary, and honest limitation.

### Introduction
- **Page budget**: 1.5 pages
- **Contents**: Motivate MAS graph organization, explain why post-hoc answer patches are insufficient, and state the first-class virtual-node contribution.

### Related Work
- **Page budget**: 1.5 pages
- **Contents**: Organize around MAS graph optimization, agent pruning/dropout, workflow optimization, and verifier/tool-augmented reasoning. All citations require later audit.

### PromptNode-Augmented MAS
- **Page budget**: 2.0 pages
- **Contents**: Define PromptNode identity, PromptEdge read/write/forward permissions, lifecycle actions, insertion locations, and selector gate.

### Experimental Setup
- **Page budget**: 1.2 pages
- **Contents**: ARG-Designer baseline, model setting, AQuA audit-clean protocol, MMLU STEM/non-STEM transfer, cost accounting, and label-audit appendix contract.

### Results and Ablations
- **Page budget**: 2.5 pages
- **Contents**: Main results, completed negative controls, component ablations, cost-matched requery, symbolic vs non-math separation.

### Selector Dry Run and Case Studies
- **Page budget**: 1.5 pages
- **Contents**: Offline leakage-safe selector manifest, hard negatives, PromptEdge feature ablation, and four mechanism case studies.

### Limitations and Conclusion
- **Page budget**: 0.8 pages
- **Contents**: State no broad non-STEM improvement yet, selector needs prospective evaluation, and SCI-Q2 submission still needs citation/claim audits.

## Figure Plan

See `experiment/mmlu/res_logs/mmlu_r330_paper_tables_and_figures_plan_summary.json`.

## Citation Plan

All citations are placeholders until citation audit. Related work should cover ARG-Designer, MAS graph optimization, agent pruning/dropout, workflow optimization, verifier/tool-augmented reasoning, and selector/gating methods.

## Reviewer Feedback

External GPT-5.5 outline review was not run in this local pass; mark as required before paper drafting freeze.

## Next Steps

- Run R332 goal audit.
- Draft method/results sections only from supported claims.
- Run citation audit and paper claim audit before submission claims.
