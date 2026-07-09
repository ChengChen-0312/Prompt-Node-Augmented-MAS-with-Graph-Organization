# R248 MMLU Transfer Feature Table

**Claim boundary**: No-API transfer feature table only. It identifies label-free probe features and ARG error candidates; it does not claim PromptNode/PromptEdge transfer accuracy improvement.

- Rows: `100`
- ARG errors / correct controls: `12` / `88`
- Probe priorities: `{'arg_error_transfer_probe': 12, 'control_correct_transfer_probe': 88}`
- Error subjects: `{'abstract_algebra': 1, 'college_chemistry': 2, 'college_mathematics': 3, 'conceptual_physics': 1, 'elementary_mathematics': 1, 'high_school_physics': 1, 'high_school_statistics': 2, 'machine_learning': 1}`
- Contract rates raw/projected: `0.04` / `1.0`

## Boundary

This table is a transfer-probe scaffold. It keeps labels out of model-visible features and should be used to select MMLU error/control probes before any API run.
