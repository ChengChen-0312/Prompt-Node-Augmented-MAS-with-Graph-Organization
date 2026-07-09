# R055 PromptNode Graph-Policy Generation Audit

**Claim boundary**: Graph-generation audit only. This samples ARGDesigner's graph generator and checks whether PromptNode roles appear before execution; it does not evaluate AQuA answer accuracy.

- Model dir: `experiment/aqua/output/aqua_pn_graph_policy_r055_full`
- Model file: `ef_best_model.pth`
- Finetune data: `experiment/FinetuneData_AQuA_PN_GraphPolicy_R053`
- Sample tasks: `16`
- Samples per task: `8`
- Sampled graphs: `128`
- PromptNode graphs: `128`
- PromptNode graph rate: `1.0000`
- PromptNode nodes: `420`
- Average PromptNode nodes per graph: `3.2812`
- DAG graphs: `128`
- DAG rate: `1.0000`
- Node range: `4-6`
- Edge range: `4-8`

## Role Counts

- `PN_Router`: `168`
- `Math Solver`: `146`
- `PN_Memory`: `130`
- `PN_Verifier`: `122`
- `Inspector`: `15`
- `Programming Expert`: `11`
- `Mathematical Analyst`: `3`

## Interpretation

This audit checks whether the trained graph generator itself emits PromptNode roles before any MAS execution or final answer aggregation. A low PromptNode graph rate means the finetune path is valid but the generator still has not learned the user's intended virtual-node insertion behavior strongly enough.
