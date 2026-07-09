# R272 MMLU Transfer Claim Boundary

**Claim boundary**: non_aqua_transfer_completed_but_superiority_not_supported

## Transfer Results

- R254 v1 proposed: `10/16`; ARG `8/16`; plain `12/16`; node-only `11/16`
- R259 v2 proposed: `9/16`; ARG `8/16`; fix/harm `1/0`
- Transfer superiority supported: `False`
- V2 no-harm on tiny diagnostic: `True`

## Claim Revision

Use MMLU as a negative transfer and robustness boundary: current PN/PE prompts can improve over fixed ARG on tiny16 but do not beat plain requery or node-only controls. Main claims must stay on AQuA official/audit-clean evidence.

Stop after this run: `True`
