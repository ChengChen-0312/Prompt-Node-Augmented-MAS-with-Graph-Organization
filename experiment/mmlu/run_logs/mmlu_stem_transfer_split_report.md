# MMLU STEM Transfer Split

**Claim boundary**: Data-preparation only. This split does not contain any ARG or PromptNode accuracy claim until same-model evaluation traces are generated.

- Total tasks: `100`
- Subject count: `15`
- Option labels: `A, B, C, D`
- Max per subject: `12`
- Limit: `100`

| Subject | Count |
| --- | ---: |
| `abstract_algebra` | `4` |
| `college_mathematics` | `10` |
| `high_school_mathematics` | `12` |
| `elementary_mathematics` | `12` |
| `high_school_statistics` | `8` |
| `college_physics` | `2` |
| `high_school_physics` | `4` |
| `college_chemistry` | `8` |
| `high_school_chemistry` | `7` |
| `college_computer_science` | `4` |
| `high_school_computer_science` | `2` |
| `machine_learning` | `8` |
| `electrical_engineering` | `4` |
| `astronomy` | `3` |
| `conceptual_physics` | `12` |

Next step: run ARG-Designer and PromptNode variants on this fixed split with `gpt-4o-2024-08-06` after quota is restored, then audit option-binding before turning any result into a paper claim.
