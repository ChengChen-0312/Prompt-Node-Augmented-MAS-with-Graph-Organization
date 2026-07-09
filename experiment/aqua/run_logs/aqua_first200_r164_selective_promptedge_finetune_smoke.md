# R164 Selective PromptNode/PromptEdge Finetune Smoke

**Claim boundary**: Graph-generator finetune infrastructure only. This run trains or smoke-checks ARGDesigner's graph generator on PromptNode graph-policy .pt files and does not evaluate AQuA answer accuracy.

- Base model: `experiment/aqua/output/aqua_pn_mvr_clean_model_20260708-015036`
- Finetune data: `experiment/FinetuneData_AQuA_R163_selective_promptedge`
- Output dir: `experiment/aqua/output/aqua_r163_selective_promptedge_r164_smoke`
- Dataset size: `4`
- Epochs: `1`
- Batch size: `2`
- Max train graphs: `4`
- PromptNode roles present: `PN_Memory, PN_Router, PN_Verifier`
- Forward finite loss: `True`
- Forward loss: `270.3687`
- Smoke only: `True`

## Interpretation

R164 verifies that the R163 selective PromptNode/PromptEdge `.pt` files load through the normal AQuA graph adapter, initialize from a PromptNode-compatible ARGDesigner checkpoint, and pass through the existing graph-generator loss. This is not an answer-accuracy result. The dataset has only four selective positive graphs, so the next step should be a goal audit at R165 before any broad training or API evaluation.
