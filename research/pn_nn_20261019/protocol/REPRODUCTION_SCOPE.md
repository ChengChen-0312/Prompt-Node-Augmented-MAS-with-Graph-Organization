# Reproduction scope

## Included and runnable offline

- Scalar calculations from the saved GPT-4o task-pair rows and request summaries.
- Reconstruction of the primary shared-start table.
- The Qwen LCB231 paired comparison, its 693 selected labels, and its 1,101 request
  metadata rows, including shared-prefix token attribution.
- Integrity verification of the files in this directory.

Saved final labels are inputs to these checks. The checks do not independently
verify a judge, reconstruct a model reply, or establish that all archived requests
would receive the same answer on another machine.

## Source inspection

`code/source_for_inspection/` retains 19 selected implementation files, with user
roots replaced in the earlier review copy by `archive://project` or `LOCAL_HOME`.
The `.py.txt` extension prevents accidental launching. The copying operation does
not change the frozen code and does not make the dependency chain complete.

The GPT-4o snapshot is `gpt-4o-2024-08-06`, temperature 0.2. The archived LCB output
limit is 2,000 tokens; USACO/TACO/OJBench use 16,384. LCB's 96 continuation tasks are
a subset of 97 tasks without an accepted initial candidate; the two denominators
are recorded separately. Later continuation packs and earlier LCB comparisons must
not be silently combined.

The completed local model is recorded as `mlx-community/Qwen3.8-27B-4bit`, using
MLX on Apple M4 Max, temperature 0.2, with thinking disabled. Before any LCB request,
the output limit was changed from 2,000 to 16,384 for all three initial drafts and
both continuation arms. `protocol.py.txt` preserves the earlier default;
`records/qwen_lcb231/output_budget_revision.json` and the runner's revision path
record the effective setting. The change is not concealed by editing the old source.

The Reflexion files contain the separately completed comparison's saved results;
its single new initial program differs from PN's three archived initial programs.
It is a system comparison, not a shared-initial comparison. Its protocol and
resource records remain separate.

## Not yet supplied as an external end-to-end reproduction

1. Complete original shared-initial replies and all subsequent model reply archives.
2. Dataset access under the original provider terms, exact public-only task
   projections, and the isolated final-test sources.
3. The complete dynamic-import dependency chain, sandbox/executor installations,
   provider gateway configuration, and local model installation.
4. A portable environment lock and a fresh-machine generation-to-scoring run.

No frozen experiment is reopened to fill these gaps. A future port must use a new
output directory and its own authorization, retain test isolation, and state any
changes to prompts, extraction, selection, or execution. This release does not
provide a command to resume an old model run.

## Costs

Shared initials were generated once. Per-method cost attributes the common prefix
once to each method; summing those two attributed totals would double-count the
prefix. Cached input tokens are part of input tokens, not an extra category.
Historical LCB costs describe the saved selected runs, not a new reconciliation of
all previous interrupted requests. The local model has no API charge, but consumes
compute time and tokens; hardware and energy costs were not priced.

## Publication check

Only stored-number calculations and file/syntax checks were performed for this
release. No model calls, candidate executions, scoring, or experiment changes were
made. The public manifest and verification receipts specify the inspected files.
