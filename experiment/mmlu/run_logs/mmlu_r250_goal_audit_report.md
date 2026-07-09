# R250 Five-Iteration SCI-Q2 Goal Audit

**Claim boundary**: audit only. No API, no superiority claim, and no SCI-Q2 readiness claim.

## Audit Window

| Run | Outcome |
|---|---|
| R246 | Selected no-API route for transfer and lifecycle evidence |
| R247 | Annotated PromptNode lifecycle actions from decisions and source metadata |
| R248 | Built MMLU transfer feature table with label/feature separation |
| R249 | Updated result-to-claim matrix and `PAPER_PLAN.md` |

## Goal Check

No drift was detected. The work remains aligned with the SCI-Q2 goal: ARG-Designer is still the baseline, `gpt-4o-2024-08-06` remains the target model setting, PromptNode is treated as a first-class graph primitive, and claims are separated from unsupported mechanisms.

The current evidence is still not submission-ready. AQuA has useful offline/frozen evidence, but live held-out PN/PE selector evaluation and transfer evidence are still missing. MMLU now has a leakage-safe probe table, not a transfer improvement result.

## Decision

Status: `aligned_continue_tiny_transfer_probe_preflight`

Broad API remains blocked. A tiny API run can be considered only after a preflight manifest selects balanced MMLU error/control probes from R248 and verifies that model-visible inputs exclude true answers and evaluation labels.

## Authorized Next

- R251: select a balanced MMLU transfer probe set from R248 errors and controls, no API.
- R252: build dry-run prompt/graph manifests for baseline, node-only, proposed PN/PE, and abstain controls, no API.
- R253: if R252 passes leakage and cost checks, run a tiny same-model API diagnostic only on the approved probe set.
- R254: analyze tiny transfer results with fix/harm, controls, and cost.
- R255: next mandatory goal audit.

## Forbidden

- No broad API.
- No SCI-Q2 readiness claim.
- No PromptEdge-text gain claim.
- No MMLU transfer improvement claim until R253/R254 or later produces answer-level evidence.
