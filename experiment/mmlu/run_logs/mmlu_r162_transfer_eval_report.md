# R162 MMLU ARG Transfer Evaluation

**Claim boundary**: same-model ARG-Designer checkpoint transfer evaluation on MMLU STEM transfer100 only; this run establishes a migration/robustness baseline and does not evaluate the PromptNode/PromptEdge method, AQuA sync20 accuracy, or SCI-Q2 readiness

## Raw Result

- Dataset: `mmlu`
- LLM: `gpt-4o-2024-08-06`
- Model path: `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/mmlu/output/mmlu_arg_base_model_r159ef_best`
- Decision method: `FinalRefer`
- Total tasks: `100`
- Correct: `88`
- Pass@1: `0.8800`
- Accuracy: `88.0%`
- Cost: `$3.042140`
- Prompt tokens: `301696`
- Completion tokens: `102244`

## Integrity

- Checkpoint loaded: `True`
- Same model as ARG-Designer setting: `True`
- Errors detected: `[]`
- Log final accuracy display: `0.88%`
- Log display interpretation: `display_bug_ratio_0.88_equals_88.0_percent`

## Subject Results

| Subject | Raw accuracy | Percent |
| --- | ---: | ---: |
| `college_mathematics` | `7/10` | `70.0%` |
| `college_chemistry` | `6/8` | `75.0%` |
| `high_school_statistics` | `6/8` | `75.0%` |
| `abstract_algebra` | `3/4` | `75.0%` |
| `high_school_physics` | `3/4` | `75.0%` |
| `machine_learning` | `7/8` | `87.5%` |
| `conceptual_physics` | `11/12` | `91.7%` |
| `elementary_mathematics` | `11/12` | `91.7%` |
| `high_school_mathematics` | `12/12` | `100.0%` |
| `high_school_chemistry` | `7/7` | `100.0%` |
| `college_computer_science` | `4/4` | `100.0%` |
| `electrical_engineering` | `4/4` | `100.0%` |
| `astronomy` | `3/3` | `100.0%` |
| `college_physics` | `2/2` | `100.0%` |
| `high_school_computer_science` | `2/2` | `100.0%` |

## Claim Gate

- MMLU transfer accuracy claim supported: `True`
- PromptNode result: `False`
- PromptNode accuracy claim supported: `False`
- AQuA accuracy claim supported: `False`
- Robustness claim supported: `False`
- SCI-Q2 ready: `False`
- Next protocol: `r163_promptnode_promptedge_transfer_or_aqua_matched_comparison`
- Next goal audit due: `R165`

## Interpretation

R162 establishes a same-LLM ARG-Designer checkpoint transfer baseline on MMLU STEM transfer100. The result is strong but uneven across subjects, so the next method iteration should test first-class PromptNode plus PromptEdge control on the same budget and report per-subject deltas instead of only a single aggregate score.
