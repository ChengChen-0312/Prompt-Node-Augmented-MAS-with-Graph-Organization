# R281 MMLU ARG vs PromptNode Retrain Protocol Freeze

**Claim boundary**: Protocol freeze only; no training launched, no API call, no transfer superiority claim, and no SCI-Q2 readiness claim.

## Environment

- Platform: `macOS-26.5.1-arm64-arm-64bit-Mach-O`
- Torch: `2.8.0`
- MPS available: `True`
- CUDA available: `False`

## Checkpoints

- ARG checkpoint: `experiment/mmlu/output/mmlu_arg_base_model_r159`; exists `True`; role mapping `6`
- PromptNode checkpoint: `experiment/mmlu/output/mmlu_promptedge_pn_graph_policy_r188_e5`; exists `True`; role mapping `9`; PN roles `['PN_Memory', 'PN_Router', 'PN_Verifier']`

## Splits

- tiny16_probe_exists: `True`
- full24_probe_exists: `True`
- transfer100_exists: `True`
- mmlu_task_split_exists: `True`
- transfer_eval_results_exists: `True`

## Fairness Requirements

- same held-out full24 and transfer100 evaluation items
- same evaluation LLM gpt-4o-2024-08-06
- same decision method FinalRefer
- PromptNode roles must be present in training graph data before checkpoint training
- old ARG checkpoint cannot be directly finetuned into PN role mapping
- plain requery remains a strong control and must be reported

## Permissions

- Training authorized next: `True`
- API evaluation allowed now: `False`
- Transfer superiority claim allowed: `False`
- Next runs: `['R282_ARG_retrain', 'R283_PromptNode_retrain']`
- Next goal audit due: `R285`
