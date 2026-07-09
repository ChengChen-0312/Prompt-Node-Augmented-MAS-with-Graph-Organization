# R055 PromptNode Graph-Policy Generation Audit

**Claim boundary**: Graph-generation audit only. This samples ARGDesigner's graph generator and checks whether PromptNode roles appear before execution; it does not evaluate AQuA answer accuracy.

- Model dir: `experiment/aqua/output/aqua_pn_graph_policy_r054_smoke`
- Model file: `ef_best_model.pth`
- Finetune data: `experiment/FinetuneData_AQuA_PN_GraphPolicy_R053`
- Sample tasks: `8`
- Samples per task: `8`
- Sampled graphs: `64`
- PromptNode graphs: `0`
- PromptNode graph rate: `0.0000`
- PromptNode nodes: `0`
- Average PromptNode nodes per graph: `0.0000`
- DAG graphs: `64`
- DAG rate: `1.0000`
- Node range: `4-6`
- Edge range: `3-5`

## Role Counts

- `Math Solver`: `78`
- `Inspector`: `71`
- `Programming Expert`: `68`
- `Mathematical Analyst`: `56`

## Interpretation

This audit checks whether the trained graph generator itself emits PromptNode roles before any MAS execution or final answer aggregation. A low PromptNode graph rate means the finetune path is valid but the generator still has not learned the user's intended virtual-node insertion behavior strongly enough.
