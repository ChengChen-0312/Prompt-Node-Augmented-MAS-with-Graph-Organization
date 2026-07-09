# R167 Expanded Selective PromptNode/PromptEdge Short Finetune

**Claim boundary**: Graph-generator finetune infrastructure only. This run trains or smoke-checks ARGDesigner's graph generator on PromptNode graph-policy .pt files and does not evaluate AQuA answer accuracy.

- Base model: `experiment/aqua/output/aqua_pn_mvr_clean_model_20260708-015036`
- Finetune data: `experiment/FinetuneData_AQuA_R166_expanded_selective_promptedge`
- Output dir: `experiment/aqua/output/aqua_r166_expanded_selective_promptedge_r167_short`
- Dataset size: `76`
- Epochs: `3`
- Batch size: `4`
- Max train graphs: `76`
- PromptNode roles present: `PN_Memory, PN_Router, PN_Verifier`
- Forward finite loss: `True`
- Forward loss: `240.6745`
- Smoke only: `False`

## Interpretation

R167 short-finetunes ARGDesigner's graph generator on the R166 expanded selective PromptNode/PromptEdge `.pt` files. The run verifies training-chain compatibility and checkpoint creation only; it is not an answer-accuracy result. Because the positive `.pt` files all contain PromptNodes, follow-up evaluation must check whether the model over-generates dense PromptNode graphs before any API run.
