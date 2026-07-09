# R065-Distilled Low-Cost Selector Design

## Goal

Reduce the cost of the R065 AQuA tail34 objective-guided PromptNode result while preserving its clean-safe fix pattern and turning it into a more stable selector story for the SCI-Q2 paper.

## Current Evidence

R065 is the strongest AQuA accuracy signal: `31/34` versus ARG `28/34`, fix/harm `3/0`, clean `28/28`, clean fix/harm `1/0`. Its weakness is cost: the full multi-view teacher costs about `$5.050805`, roughly `5.41x` ARG.

Existing reductions are useful but incomplete:

- R068 selective replay keeps `31/34` and reduces cost to `$3.597409`, but it is still replay and still `3.86x` ARG.
- R069 fresh integrated selective run reaches `29/34`, fix/harm `3/0`, cost `$3.908995`.
- R072 fresh cascade reaches `29/34`, fix/harm `2/0`, cost `$2.826040`.
- R147 frozen-selector replay reaches `30/34`, but is not a fresh integrated run.

## Design

Treat R065/R068 as the expensive teacher and train or fit a cheaper student gate. The student must decide when to trigger PromptNode views and when to keep ARG. The student cannot use true answers, correctness, audit labels, or task-id-specific rules.

The first implementation is no-API:

1. Build a paper-ready evidence table for R065/R068/R069/R072/R147.
2. Export a distillation feature table from existing AQuA traces.
3. Fit small interpretable gate candidates from label-free features:
   - ARG direct majority count.
   - direct-vote missing/split flags.
   - ARG invalid or `None`.
   - objective top score.
   - objective differs from ARG.
   - availability of PromptNode objective signal.
4. Evaluate candidate gates offline against the R065 teacher and ARG fallback.
5. Report accuracy, fix/harm, clean fix/harm, trigger count, estimated cost, and cost-normalized gain.

## Success Criteria

The student gate is considered worth a fresh API preflight only if, offline:

- selected accuracy is at least `30/34`;
- fix/harm is no worse than `2/0`;
- clean harm is `0`;
- triggered PromptNode tasks are at most `14/34`;
- estimated cost is below `$2.50`;
- the gate is described by a compact rule or a small sklearn model with feature importances.

## Non-Goals

- Do not claim R065 alone is SCI-Q2-ready.
- Do not claim PromptEdge text is the source of gain.
- Do not run broad API during this phase.
- Do not train on tail34 labels as supervision. Tail34 can be used only for frozen evaluation or teacher-agreement analysis.

## Outputs

- `experiment/aqua/run_logs/aqua_r262_paper_ready_result_tables.md`
- `experiment/aqua/res_logs/aqua_r262_paper_ready_result_tables_summary.json`
- `experiment/aqua/aqua_r263_r065_distillation_feature_table.jsonl`
- `experiment/aqua/run_logs/aqua_r263_r065_distillation_report.md`
- `experiment/aqua/res_logs/aqua_r263_r065_distillation_summary.json`

## Review

The design is intentionally conservative: it creates a low-cost selector candidate and a paper table without new API. If R263 fails the success criteria, the paper should keep R065 as a costly teacher result and report the failed distillation as a limitation.
