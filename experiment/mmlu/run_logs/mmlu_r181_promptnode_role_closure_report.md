# R181 MMLU PromptNode Role Closure

**Claim boundary**: engineering closure only. No API evaluation, no MMLU accuracy claim, and no claim that the old MMLU ARG checkpoint can generate PN roles.

## What Changed

- Added `PN_Memory`, `PN_Verifier`, and `PN_Router` descriptions to `mas_framework/prompt/mmlu_prompt_set.py`.
- Added the same PN roles to `experiment/mmlu/mmlu_prompt_set.py` so MMLU training/evaluation role constraints can see them.
- Updated `PromptNode` to accept the optional `constraint` argument passed by MMLU `TestGraph`.
- Added constructor tests proving a MMLU graph with `PN_Memory -> PN_Verifier -> PN_Router` builds without running API calls.

## Verification

- `python -m unittest tests.test_r181_mmlu_promptnode_roles -v`: `2/2` passed.
- Adjacent AQuA selector/policy tests: `9/9` passed.

## Remaining Blockers

- The old MMLU checkpoint still has six non-PN roles, so it cannot generate PN roles without retraining.
- MMLU evaluator still lacks a PN/PE topology adapter or policy flag.
- No non-leaky MMLU PN/PE target export manifest exists.
- PromptNode router contracts still mention A-E labels; for MMLU they should become option-label aware before transfer evaluation.

## Next

R182 should add a MMLU PN/PE topology adapter or export path and option-label-aware PromptNode contract tests, still without API.
