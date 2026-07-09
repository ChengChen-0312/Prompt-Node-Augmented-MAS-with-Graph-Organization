# AQuA First200 PromptNode Graph-Policy PyG Smoke Check

**Claim boundary**: Training-interface verification only. This smoke check does not call an LLM, does not evaluate AQuA accuracy, and does not provide tail34 or transfer evidence.

## Checks

- Exported `.pt` files: `76`
- Manifest rows: `76`
- `AquaGraphDataset(pretrain=False)` sample load: `8/8` DAG graphs
- `GraphListDataset` wrapping: `8` graphs, `7` node labels, `[0]` edge labels
- ARGDesigner CPU forward precheck: batch size `2`, finite loss `True`, log-prob shape `(2,)`

## Interpretation

R053 closes the interface gap between R052's graph-policy rows and ARG-Designer's training code. The exported PromptNode graphs can be loaded through the existing AQuA adapter, wrapped by the existing graph dataset class, and passed through the current ARGDesigner loss path. This is still a preparation result, not an accuracy result.
