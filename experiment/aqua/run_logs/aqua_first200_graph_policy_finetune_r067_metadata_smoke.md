# R054 PromptNode Graph-Policy Finetune

**Claim boundary**: Graph-generator finetune infrastructure only. This run trains or smoke-checks ARGDesigner's graph generator on PromptNode graph-policy .pt files and does not evaluate AQuA answer accuracy.

- Base model: `experiment/aqua/output/aqua_pn_router_contract_model_20260708-030015`
- Finetune data: `experiment/FinetuneData_AQuA_PN_GraphPolicy_R053`
- Output dir: `experiment/aqua/output/aqua_pn_graph_policy_r067_metadata_smoke`
- Dataset size: `8`
- Epochs: `1`
- Batch size: `2`
- Max train graphs: `8`
- PromptNode roles present: `PN_Memory, PN_Router, PN_Verifier`
- Forward finite loss: `True`
- Forward loss: `246.7950`
- Smoke only: `True`

## Interpretation

R054 is the first direct training-path step after R053: the PromptNode graph-policy `.pt` files are loaded through the normal AQuA graph adapter, initialized from a PromptNode-compatible ARGDesigner checkpoint, and passed through the existing graph-generator loss. This is not an answer-accuracy result.
