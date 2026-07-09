# R372 Goal Audit After Adversarial Probe Update

**Claim boundary**: R372 audits R367-R371. The adversarial/domain probe failed safely, and its outputs were converted into hard negatives before any broad API run.

## Alignment

- `still_aligned_with_sci_q2_goal`: `True`
- `adversarial_probe_failed_safely`: `True`
- `hard_negative_update_done`: `True`
- `history_signal_preserved`: `True`
- `overclaiming_blocked`: `True`

## Course Correction

- Retrain source-invariant gate with R369 hard negatives before another fresh API run.
- Do not integrate unconstrained domain verifiers directly.
- Keep history-passage verifier as a guarded candidate family requiring fresh validation.

- Next required run: `R373_retrain_after_r369_hard_negatives`
