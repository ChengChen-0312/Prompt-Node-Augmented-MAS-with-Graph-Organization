# R311 MMLU Non-STEM Guarded PromptNode Transfer

**Claim boundary**: Same-model non-STEM transfer diagnostic. It can support no-harm evidence, not SCI-Q2 readiness by itself.

- ARG baseline: `37/40`
- Proposed guarded PromptNode: `34/40`
- Delta vs ARG: `-3`
- Fix/harm vs ARG: `0/3`
- No harm: `False`
- Cost: `$0.205470`
- Prompt/completion tokens: `22371/6241`

| Variant | Records | Correct | Accuracy | Fix/Harm | Switches | API executed/errors |
|---|---:|---:|---:|---:|---:|---:|
| `arg_baseline_fixed` | `40` | `37` | `0.925` | `0/0` | `0` | `0/0` |
| `proposed_nonstem_promptnode_promptedge` | `40` | `34` | `0.85` | `0/3` | `5` | `40/0` |

## Boundary

Use this as transfer/no-harm evidence only after R312 claim audit and ablations.
