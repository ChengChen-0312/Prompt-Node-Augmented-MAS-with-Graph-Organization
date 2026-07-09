# R079 R078 Selector Tail34 Replay

**Claim boundary**: R079 is a replay applying the R078 selector to existing tail34 graph-objective traces. It exposes the missing explicit PromptNode graph metadata boundary: current tail34 traces contain no generated graph specs, so the selector falls back to baseline and does not create a new answer-accuracy gain.

- Output records: `experiment/aqua/aqua_tail34_r079_clean_fix_selector_replay_results.jsonl`
- Overall selector accuracy: `28/34`
- Baseline accuracy: `28/34`
- Delta vs baseline: `+0`
- Switches: `0`
- Fix/Harm: `0/0`
- Selector feature violations: `0`
- Total variants: `136`
- Variants with generated graph: `0`
- Variants with explicit PromptNode graph: `0`
- Variants with PromptNode specs: `0`

## Interpretation

The R078 selector is learnable on R077 rows, but this tail34 replay shows it cannot be expected to recover the R065/R068 accuracy signal unless the evaluated traces expose the same first-class PromptNode graph metadata used during training. This strengthens the next-step requirement: generate/evaluate PromptNode graphs before execution, then apply the selector to those graph candidates.
