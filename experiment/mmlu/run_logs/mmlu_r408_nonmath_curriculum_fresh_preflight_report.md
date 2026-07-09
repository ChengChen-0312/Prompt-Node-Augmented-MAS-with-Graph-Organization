# R408 Nonmath Curriculum Fresh Preflight

**Claim boundary**: R408 builds a leakage-free fresh MMLU non-STEM manifest for the R407 curriculum. It does not execute API or support a paper claim.

- Subjects/tasks: `8/32`
- API records: `64`
- Planned ARG/curriculum calls: `32/32`
- Leakage pass: `True`
- Node types: `['InstructionAmbiguityVerifierPN', 'OptionSemanticConsistencyVerifierPN', 'ConceptDefinitionAnchorPN', 'ContradictionDetectorPN', 'AdversarialVerifierPN', 'ConsensusConflictResolverPN', 'MemoryBridgePN']`
- Edge types: `['OptionBindingPromptEdge', 'AdversarialChallengePromptEdge', 'DefinitionAnchorPromptEdge', 'ConflictResolutionPromptEdge', 'MemoryBridgePromptEdge']`
- Next required run: `R409_nonmath_curriculum_api_execution`
