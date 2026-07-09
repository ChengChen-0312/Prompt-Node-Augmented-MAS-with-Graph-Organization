# R454 Reproducibility Artifact Index

**Claim boundary**: R454 writes a local artifact index for reproducibility. It does not read, expose, or validate API key values.

- Artifact index: `paper/artifacts/reproducibility_index.md`
- Primary result files: `6`
- API key values redacted: `True`

## Verification Commands

- `python -m unittest tests.test_r440_paper_claim_number_static_audit`
- `python -m unittest tests.test_r447_local_smoke_after_tables`
- `python -m unittest tests.test_r452_five_run_goal_audit_and_compile_probe`
- `python -m unittest tests.test_r453_appendix_noise_audit_pack`
- `python -m unittest tests.test_r454_reproducibility_artifact_index`

- Paper claim authorized: `False`
- SCI-Q2 ready: `False`
- Next required run: `R455_full_local_smoke_after_appendix_artifact`
