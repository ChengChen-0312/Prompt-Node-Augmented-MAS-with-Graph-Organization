# R178 New Target Generation Preflight

**Claim boundary**: R178 is a route preflight only. It blocks further AQuA target mining from local data and identifies MMLU PN/PE engineering prerequisites before any accuracy API.

- AQuA total rows: `254`
- AQuA first200 rows used: `200`
- AQuA tail34 rows: `34`
- Remaining after first200 equals tail34: `True`
- Extra local AQuA train rows available: `0`
- AQuA target-generation route allowed: `False`

## MMLU Route

- MMLU transfer baseline available: `True`
- MMLU transfer baseline accuracy: `0.88`
- MMLU PromptNode/PromptEdge ready: `False`

## MMLU Blockers

- evaluate_mmlu.py has no prompt_node_policy or prompt_node_topology_policy path
- mmlu_prompt_set.py role map has no PN_Memory/PN_Verifier/PN_Router roles
- mmlu_arg_base_model_r159 role mapping was trained on six MMLU roles, not PN/PE roles
- no MMLU PN/PE graph-policy target export exists yet

## Recommended Next Run

- Run: `R179`
- Type: `MMLU PN/PE engineering preflight without API`
- Step: add MMLU-safe PN role descriptions or a generic shared PN role registry
- Step: verify convert_to_pyg/TestGraph can execute MMLU PN roles
- Step: build a tiny synthetic MMLU PN/PE graph smoke with mock/no API
- Step: only after that design target export or bounded API smoke

## Interpretation

The local AQuA dataset has no remaining non-test rows after first200; the rest is exactly tail34. Further override-target mining from AQuA would contaminate the diagnostic set. The transfer path is more SCI-Q2 aligned, but MMLU currently has only an ARG baseline and lacks PN/PE graph-generation and execution plumbing. Therefore the next run should be engineering preflight, not an accuracy run.
