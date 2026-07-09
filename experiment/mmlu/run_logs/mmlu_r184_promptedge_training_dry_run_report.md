# R184 MMLU PN-Capable Training Dry-Run

**Claim boundary**: Training-path dry-run only. No API evaluation, no trained checkpoint claim, and no PromptNode/PromptEdge accuracy claim.

## Materialization

- Materialized graphs: `403`
- Unique questions: `37`
- Output dir: `experiment/PromptEdgeData_mmlu_r183`

## Forward Dry-Run

- Dataset graphs loaded: `24`
- Role mapping size: `9`
- PN roles present: `['PN_Memory', 'PN_Router', 'PN_Verifier']`
- Finite forward loss: `True`
- Forward loss: `41.3041`
- Role accuracy: `0.00`
- Sample generation ok: `True`

## Compatibility

- Old MMLU ARG checkpoint role mapping size: `6`
- Direct finetune compatible with PN role mapping: `False`
- Requires PN-capable pretrain or expanded checkpoint: `True`

## Next

Run a short PN-capable pretraining job from the materialized PromptEdge data, then audit generated graphs before any MMLU transfer API smoke.
