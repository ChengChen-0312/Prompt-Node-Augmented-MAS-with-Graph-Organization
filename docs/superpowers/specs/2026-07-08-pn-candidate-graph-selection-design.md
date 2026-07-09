# PN Candidate Graph Selection Design

## Goal

Use virtual Prompt Nodes to improve AQuA sync20 by selecting among multiple
ARG-Designer graph candidates before execution, rather than rewriting the final
answer after execution.

## Context

Previous R021/R022 results show:

- PN roles can be generated and executed.
- Forcing PN into every graph harms accuracy.
- Final-prompt PN lifecycle logic introduces harms and can create parser artifacts.

The next mechanism should move Prompt Node control earlier in the pipeline:
Prompt Nodes should govern graph organization, not merely answer selection.

## Approach

Extend AQuA evaluation to generate `K` graph candidates per task via
`ARGDesigner.sample(num_samples=K)`. Each raw candidate is normalized through the
same PN topology policy. A deterministic virtual PromptNode selector scores each
candidate by graph-organization features:

- role coverage: math, code, inspection, analysis
- graph connectivity and edge density
- PN lifecycle availability: memory/verifier/router presence after normalization
- redundancy risk: too many repeated roles or overly dense candidate
- execution cost proxy: nodes and edges

The selector picks the highest-scoring graph before running any LLM agents.

## Why Deterministic First

This first R023 version is a clean graph-organization test:

- no gold labels
- no task IDs
- no answer text
- no post-hoc selection based on correctness
- no extra LLM selector cost

If deterministic candidate selection beats single-sample ARG, it supports the
paper claim that virtual graph-organization signals can improve performance.
If it ties/fails, a learned or LLM-based selector can be tested next.

## Interfaces

`experiment/utils.py`:

- `generate_graph(..., num_samples=1, batch_size=1)`

`experiment/aqua/prompt_node_graph.py`:

- `score_prompt_node_candidate_graph(nx_graph) -> dict`
- `select_prompt_node_candidate_graph(graphs) -> tuple[nx_graph, list[dict]]`

`experiment/aqua/evaluate_aqua.py`:

- CLI: `--num_candidate_graphs`
- result JSON includes `candidate_graphs` and `selected_candidate_index`

## Success Gate

Run AQuA sync20 with:

- same model checkpoint as R021/R022
- same LLM: `gpt-4o-2024-08-06`
- `--num_candidate_graphs 4`
- `--prompt_node_topology_policy canonicalize_generated`

Target: `>=18/20`.

If the method only ties or fails, record the negative result and do not claim
SCI Q2 readiness.
