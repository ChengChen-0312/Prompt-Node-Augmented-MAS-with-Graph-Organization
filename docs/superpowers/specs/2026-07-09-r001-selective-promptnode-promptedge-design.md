# R001-Compatible Selective PromptNode and PromptEdge Design

## Purpose

Build the next PromptNode experiment line from the original R001 ARG-Designer
setup instead of from post-hoc answer patching. The method should let the graph
generator learn when to add first-class virtual PromptNodes and how to connect
them with typed PromptEdges, while preserving ARG-Designer behavior on rows that
do not need intervention.

The paper-facing objective is SCI-Q2 aligned: improve held-out or transfer
accuracy over ARG-Designer with clean/noisy audits, fix/harm accounting, and
cost normalization. AQuA sync20 is diagnostic only because R024 shows ARG
already solves all 17 clean rows.

## Baseline Context

R001 uses `gpt-4o-2024-08-06`, ARG-Designer `FinalRefer`, and the AQuA sync20
split. It obtains `17/20` official accuracy at cost `$0.508365`. The training
path is:

1. Stage 1 cold start: collect successful complex graphs from dense graph
   templates over base tasks.
2. Stage 2 efficient graph construction: combine pruned generated graphs,
   simple successful graphs, and replay complex graphs.
3. Stage 3 fine-tuning: train ARG-Designer's graph generator over the efficient
   graph `.pt` files.
4. Evaluation: sample a small generated graph, execute agents, and aggregate
   with `FinalRefer`.

The new method must preserve this path. PromptNodes must appear in graph
training targets and generated graphs before execution, not as an answer-only
patch after final aggregation.

## R001 Error Diagnosis

R001 has three wrong sync20 rows:

| Task | Graph | Observed failure | Design implication |
| --- | --- | --- | --- |
| `task_152` | `Programming Expert -> Programming Expert -> Inspector` | Agents compute `15`; inspector says no option matches; final picks closest `E=14`; official label `C=10` is contradicted by its own arithmetic. | Add option-binding and no-exact-option suppression. Do not train toward the noisy official label. |
| `task_199` | `Programming Expert -> Math Solver` | Agents use conflicting probability interpretations; final picks closest `C=23/90`; official rationale has arithmetic/semantic errors. | Add ambiguity detection, event-definition memory, and conservative routing. |
| `task_172` | `Math Solver -> Programming Expert` | Agents compute `132`; final picks closest `C=126`; official label `E=48` is not a clean target. | Add target-preserving equation audit and no-closest-choice guard. |

These rows are useful as failure modes but not as positive accuracy targets. The
main trainable signal should come from non-test first200/tail34-compatible
clean-fix objectives and transfer validation, not from memorizing noisy sync20
labels.

## Method

### Graph Objects

The augmented graph is:

`G+ = (V_A union V_P, E_A union E_P, T_P)`

where:

- `V_A`: ordinary ARG-Designer agent nodes.
- `V_P`: first-class PromptNode virtual nodes.
- `E_A`: ordinary communication edges.
- `E_P`: typed PromptEdges with read/write/verify/repair/forward/suppress
  semantics.
- `T_P`: machine-readable PromptNode metadata: identity, permissions, budget,
  lifecycle state, and contract schema.

### PromptNode Types

Use a compact first implementation:

| Type | Role | Trigger intuition |
| --- | --- | --- |
| `PN_Memory` | Stores target quantity, option table, candidate values, formulas, direct-agent votes, and uncertainty flags. | Any multi-agent graph with conflicting values or non-option numeric outputs. |
| `PN_Verifier` | Checks target preservation, exact/equivalent option binding, unsupported labels, arithmetic consistency, and contradiction. | Non-exact option binding, formula/value mismatch, split votes. |
| `PN_Router` | Forwards only verified options or emits `NO_EXACT_OPTION`/`UNSUPPORTED`; blocks nearest-choice coercion. | Verifier emits a strong supported option or a suppress/fallback decision. |
| `PN_Repair` | Optional high-cost node that proposes exact-option repair through explicit repair fields. | Only when verifier finds a close, explainable binding gap and clean-risk guard passes. |

`PN_Repair` is not part of the first dense graph generator. It is a gated
extension for edge-prompt repair experiments so the main model does not learn
to over-repair noisy rows.

### PromptEdge Types

The current code effectively trains binary edges. This design requires a small
edge-label vocabulary:

| Edge type | Meaning |
| --- | --- |
| `agent_flow` | Ordinary ARG agent-to-agent communication. |
| `write_memory` | Real agent writes evidence into `PN_Memory`. |
| `read_memory` | Verifier reads compact memory. |
| `verify_contract` | Verifier emits structured target/option audit. |
| `forward_verified` | Router forwards a supported option contract. |
| `suppress_unsupported` | Router blocks unsupported labels or no-exact-option outputs. |
| `repair_option` | Repair node forwards an explicit repair candidate. |

The graph generator should learn both node identity and edge type. If full
edge-type generation is too invasive for the first run, export typed PromptEdge
metadata and keep the ARG edge tensor binary as a compatibility layer, then use
metadata during execution and reporting. The paper should mark this as
metadata-conditioned execution unless edge labels are actually trained.

### Selective Activation

The method should not force PromptNodes into every graph. Dense PromptNode
generation already failed in R055/R058. The selector/generator should prefer
no-PromptNode graphs unless label-free risk features justify insertion.

Allowed risk features:

- Direct-agent candidate values do not exactly match options.
- Direct-agent votes split or contain invalid labels.
- Formula/value extraction disagrees across agents.
- A candidate option is supported by only one weak chain.
- A graph has high option-binding risk under label-free objective features.

Forbidden training or selection features:

- Gold answer.
- `is_solved`.
- Audit label.
- Clean/noisy label.
- Task id.
- Any historical per-task correctness flag exposed to the selector.

### Training Target Construction

Keep the R001 pipeline and add a fourth graph-policy distillation branch:

1. Build non-test graph-policy rows from first200-style candidate traces and
   clean-fix objectives.
2. Export positive targets containing canonical PromptNode/PromptEdge structures
   only when the label-free objective has sufficient margin.
3. Export suppress/fallback targets for ambiguous, low-margin, or risky rows.
4. Convert positive and suppress targets into ARGDesigner-compatible `.pt`
   files:
   - positive rows include `PN_Memory -> PN_Verifier -> PN_Router` and typed
     edge metadata;
   - suppress rows keep ordinary ARG graphs or include a non-executed suppress
     marker depending on compatibility.
5. Fine-tune from the R001-compatible checkpoint with the same model setting.

The key difference from R055 is that the generator should learn selective
PromptNode insertion and PromptEdge routing, not dense always-on PromptNodes.

### Execution Contract

At inference:

1. Generate a graph with the trained model.
2. Execute ordinary ARG nodes as before.
3. If PromptNodes are present, execute them according to typed edges:
   - write direct outputs to memory;
   - verify target and option binding;
   - route only exact/equivalent supported options;
   - suppress unsupported or no-exact-option outputs;
   - optionally run repair only when explicit repair fields and confidence
     guards pass.
4. Final aggregation must not choose a nearest option when the router emits
   `NO_EXACT_OPTION`.

### Evaluation

Do not claim success from sync20. Use it as a diagnostic regression set:

- sync20 target: preserve `17/20`, no clean harm, lower or bounded cost where
  possible.
- tail34 target: exceed ARG baseline with clean fix/harm `>= 1/0`.
- transfer target: compare ARG and PromptNode variants on MMLU STEM transfer or
  another clean multiple-choice reasoning split under the same LLM setting.

Every main result must report:

- official accuracy;
- clean/noisy split;
- fix/harm;
- clean fix/harm;
- token cost and cost-normalized accuracy;
- PromptNode insertion rate;
- PromptEdge type distribution;
- no-forbidden-field audit.

### Ablations

Required negative controls:

- original ARG baseline;
- dense PromptNode generation;
- selective PromptNode without typed PromptEdges;
- typed PromptEdges without repair;
- no router suppression;
- random PromptNode insertion at matched node budget;
- metadata-only PromptEdges when edge labels are not trained.

### Iteration Discipline

Experiment numbering resumes at R163. Every five runs must include a goal audit:

- R165 audits R161-R165;
- R170 audits R166-R170;
- continue the same pattern until the user stops the work.

The audit checks whether the work still targets SCI-Q2 evidence, avoids sync20
noise overclaiming, preserves update2 first-class PromptNode semantics, and
keeps PromptEdges as graph communication objects rather than prompt suffixes.

## Deliverables

1. R163 design/implementation artifact for selective PromptNode/PromptEdge
   graph-policy export.
2. R164 training or smoke run that proves the R001-compatible training path
   accepts the new targets.
3. R165 goal audit before broad API spending.
4. A result-to-claim update that distinguishes:
   - train-time graph-generation evidence;
   - fresh answer accuracy;
   - replay/proxy evidence;
   - negative controls.

## Spec Self-Review

- Placeholder scan: no `TBD`, `TODO`, or unspecified behavior remains.
- Internal consistency: sync20 is diagnostic only; held-out and transfer are
  required for paper claims.
- Scope check: this spec covers one implementation line: R001-compatible
  selective PromptNode/PromptEdge graph-policy training.
- Ambiguity check: if typed edge labels cannot be trained immediately, metadata
  execution must be explicitly reported as metadata-conditioned, not as learned
  edge generation.
- Repository status: the workspace directory is not a git repository, so the
  skill-required commit cannot be performed here.
