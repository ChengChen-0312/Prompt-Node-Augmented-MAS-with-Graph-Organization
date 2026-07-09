# R167 Expanded Selective PromptNode/PromptEdge Generation Audit

**Claim boundary**: Graph-generation audit only. This samples ARGDesigner's graph generator and checks whether PromptNode roles appear before execution; it does not evaluate AQuA answer accuracy.

- Model dir: `experiment/aqua/output/aqua_r166_expanded_selective_promptedge_r167_short`
- Model file: `ef_best_model.pth`
- Finetune data: `experiment/FinetuneData_AQuA_R166_expanded_selective_promptedge`
- Sample tasks: `8`
- Samples per task: `8`
- Sampled graphs: `64`
- PromptNode graphs: `64`
- PromptNode graph rate: `1.0000`
- PromptNode nodes: `249`
- Average PromptNode nodes per graph: `3.8906`
- DAG graphs: `64`
- DAG rate: `1.0000`
- Node range: `4-6`
- Edge range: `3-10`

## Role Counts

- `PN_Router`: `93`
- `PN_Memory`: `79`
- `PN_Verifier`: `77`
- `Math Solver`: `59`
- `Programming Expert`: `36`
- `Inspector`: `5`
- `Mathematical Analyst`: `3`

## Interpretation

This audit checks whether the trained graph generator itself emits PromptNode roles before any MAS execution or final answer aggregation. R167 emits PromptNodes in `64/64` sampled graphs, so the train-time virtual-node mechanism is active. The remaining risk is over-generation: a `1.0000` PromptNode graph rate is not selective enough by itself, so follow-up work must add a learned fallback/selector boundary before any broad API evaluation.
