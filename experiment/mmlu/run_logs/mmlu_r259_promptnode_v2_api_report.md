# R259 PromptNode/PromptEdge V2 Tiny API Diagnostic

**Claim boundary**: Tiny same-model v2 diagnostic only; not a broad held-out result, transfer proof, or SCI-Q2 readiness claim.

- Records: `32`
- API required/executed/errors: `16/16/0`
- Correct: `17`
- Fixes/harms vs ARG: `1` / `0`
- Cost: `$0.050030`

| Variant | Records | Correct | Accuracy | Fix/Harm | Switches | API executed/errors |
|---|---:|---:|---:|---:|---:|---:|
| `arg_baseline_fixed` | `16` | `8` | `0.5` | `0/0` | `0` | `0/0` |
| `proposed_v2_independent_guarded_pnpe` | `16` | `9` | `0.5625` | `1/0` | `1` | `16/0` |

## Boundary

This run executes only the R258-authorized v2 tiny16 diagnostic. It must be compared with R253 controls before any claim.
