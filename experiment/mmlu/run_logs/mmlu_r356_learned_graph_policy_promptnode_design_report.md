# R356 Learned Graph-Policy PromptNode Design

**Claim boundary**: R356 redirects from hand-written template expansion to a learned graph policy. The policy treats PromptNodes and PromptEdges as first-class graph actions and requires a fresh evaluation after training.

- Policy type: `learned_graph_policy`

## Graph Actions

- `KEEP_ARG`
- `ADD_PROMPT_NODE`
- `ADD_PROMPT_EDGE`
- `UPDATE_PROMPT_NODE`
- `MERGE_PROMPT_NODES`
- `PRUNE_PROMPT_NODE`
- `FORWARD_CANDIDATE`

## PromptNode Families

- `MemoryBridge`
- `InstructionAmbiguityVerifier`
- `OptionSemanticConsistencyVerifier`
- `ContradictionDetector`
- `ToolResourceVerifier`
- `PassageEntailmentVerifier`
- `DefinitionFallacyVerifier`
- `ConsensusConflictResolver`
- `SafetyGate`

- Next required run: `R357_learned_graph_policy_training_manifest`
