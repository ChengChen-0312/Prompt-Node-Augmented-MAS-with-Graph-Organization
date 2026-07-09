# R080 R078 Selector on R058 Generated PromptNode Graphs

**Claim boundary**: R080 is a negative metadata-compatible replay: R058 contains explicit PromptNode graphs, but applying the R078 selector to this dense PromptNode candidate pool harms tail34. This shows metadata alone is insufficient; the generated graph candidates and selector objective must be aligned.

- Output records: `experiment/aqua/aqua_tail34_r080_r078_on_r058_metadata_results.jsonl`
- Selector accuracy: `25/34`
- ARG baseline accuracy: `28/34`
- Delta vs baseline: `-3`
- Switches: `3`
- Fix/Harm: `0/3`
- Generated PromptNode graph records: `34`
- PromptNode spec records: `34`
- Selector feature violations: `0`

## Interpretation

Unlike R079, this replay uses a tail34 candidate source that does contain explicit PromptNode graph metadata. The result is still negative: the selector switches to three dense R058 PromptNode candidates and all three are harms against the historical ARG baseline. This separates two requirements for the SCI method: expose PromptNode graph metadata, and train/generate graph candidates aligned with the clean-fix objective.
