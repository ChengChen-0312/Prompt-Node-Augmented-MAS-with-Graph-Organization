# AQuA First200 PromptNode Graph-Policy PyG Export

**Claim boundary**: ARGDesigner-compatible PyG finetune files generated from positive label-free PromptNode graph-policy targets. Files contain graph roles/edges and task text, not gold answers, predictions, router options, audit labels, or correctness fields.

- Output directory: `experiment/FinetuneData_AQuA_PN_GraphPolicy_R053`
- Manifest JSONL: `experiment/aqua/aqua_first200_graph_policy_pt_manifest.jsonl`
- Source policy rows: `800`
- Exported `.pt` files: `76`
- Skipped non-positive rows: `724`
- PromptNode `.pt` files: `76`
- PromptNode spec `.pt` files: `76`
- PromptNode edge-permission `.pt` files: `76`
- Positive PromptNode role counts: `PN_Memory=76, PN_Router=76, PN_Verifier=76`
- Unique positive graph signatures: `17`
- Outcome-field violations: `0`

## Why This Matters

R053 turns R052's node/edge policy rows into the actual `.pt` graph files consumed by `AquaGraphDataset(pretrain=False)`. This closes the interface gap between the paper idea and the ARG-Designer training pipeline: PromptNodes are now available as train-time graph nodes and edges.

This export still does not report answer accuracy. It prepares a compatible finetune directory for the next step: train or fine-tune the ARG-Designer graph generator, then run same-model AQuA tail34 or transfer validation.
