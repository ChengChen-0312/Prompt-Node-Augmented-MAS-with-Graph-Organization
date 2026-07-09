# R151 SCI-Q2 Evidence-Gap Plan

**Claim boundary**: evidence-gap plan only; no new experiment, API run, or readiness claim

## Current Verdict

- SCI-Q2 ready: `False`
- Plan only: `True`
- No API run: `True`
- Broad API allowed next: `False`
- Next protocol: `r152_mmlu_checkpoint_resolution_or_aqua_same_method_replicate_preflight`

## Blocking Gaps

- R147 full-tail34 evidence is replay-level, not a fresh integrated full run
- R148 McNemar p=0.5 is not statistically significant
- R148 cost-normalized superiority is unsupported
- MMLU transfer is blocked by missing compatible ARG checkpoint
- AQuA next100 is family evidence, not same-method R147 significance

## Must-Run Blocks

| Block | Purpose | Run | Success Boundary |
| --- | --- | --- | --- |
| `transfer_checkpoint_resolution` | Resolve transfer blocker | Find or build a compatible MMLU ARG checkpoint, then run the fixed STEM100 split. | No transfer claim until the checkpoint exists and the run completes. |
| `same_method_aqua_replicate` | Same-method AQuA replicate | Freeze the R147 selector/method and evaluate it on a larger pre-registered split. | Use paired significance; exploratory if p >= 0.05. |
| `cost_normalized_variant_or_accounting` | Cost boundary | Either reduce incremental PromptNode cost or explicitly frame the method as accuracy-cost tradeoff. | Do not claim cost-normalized superiority unless correct-per-dollar improves. |
| `negative_control_ablations` | Negative controls | Run no-router, no-lifecycle, random PN, dense PN, and node-only/no-edge ablations. | Show PromptNode node+edge organization matters beyond answer repair. |
| `paper_claim_and_citation_audit` | Paper audit | Run claim-evidence and citation audits before drafting SCI-Q2 claims. | Every numeric claim must map to raw logs. |

## Gates

- Transfer required for SCI-Q2: `True`
- Same-method significance required: `True`
- Cost boundary required: `True`
- Same-method target: `p < 0.05 or report as exploratory only`
- Transfer split: `experiment/mmlu/mmlu_stem_transfer100.jsonl`
- Cost fallback wording: `accuracy-cost tradeoff, not cost-normalized superiority`
