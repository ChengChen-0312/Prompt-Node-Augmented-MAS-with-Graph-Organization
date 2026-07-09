# R295 Goal Audit After Specialist-Aware Decoding

**Claim boundary**: Goal audit only. No API is executed here; R294 is a no-label/no-API reselection result over saved R287 graph candidates.

- Goal alignment: `aligned_revision_ready_for_api`
- R291 correct vs R292 ARG: `20/24` vs `22/24`
- R294 contract-ready rate: `0.8333333333333334`
- R294 selected with specialist: `19`
- R294 changed from R287: `14`
- API eval allowed next: `True`
- Transfer superiority claim supported: `False`
- SCI-Q2 ready: `False`

## Decision

R294 addresses the diagnosed selector flaw at graph-selection level, but it still needs matched API replay against R292 before any transfer claim.

## Next Runs

- `R296_specialist_aware_api_replay`
- `R297_compare_r296_vs_r292`
- `R298_failure_analysis_if_negative`
- `R299_claim_matrix_update`
- `R300_goal_audit`
