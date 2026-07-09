# R407 Nonmath PromptNode Curriculum Design

**Claim boundary**: R407 designs a general nonmath PromptNode/PromptEdge curriculum. It is design/preflight only; it cannot support a paper result until fresh execution and learned-gate analysis pass.

- PromptNodes: `7`
- PromptEdges: `5`
- Training policy: `two_stage_candidate_then_learned_forward_gate`
- Math patch only: `False`

## PromptNodes

- `InstructionAmbiguityVerifierPN`: Extracts the operative instruction, scope words, negation, EXCEPT/NOT clauses, and required answer granularity.
- `OptionSemanticConsistencyVerifierPN`: Checks whether each option semantically satisfies the extracted instruction instead of only sounding plausible.
- `ConceptDefinitionAnchorPN`: Creates a compact local definition anchor for philosophy, moral, logic, religion, and social-science terms.
- `ContradictionDetectorPN`: Detects when a candidate rationale contradicts the option text, the stem operator, or another node's evidence.
- `AdversarialVerifierPN`: Attempts to falsify the leading candidate by defending the nearest distractor before the graph forwards an answer.
- `ConsensusConflictResolverPN`: Aggregates node evidence and forwards only when support, contradiction, and ambiguity contracts are jointly satisfied.
- `MemoryBridgePN`: Carries a compressed task-intent and definition bridge from early verifiers to late option-binding and resolver nodes.

## PromptEdges

- `OptionBindingPromptEdge`: Bind exactly one visible option label only when the rationale directly supports that option text.
- `AdversarialChallengePromptEdge`: Forward the candidate only if the adversarial challenge fails to support the nearest distractor.
- `DefinitionAnchorPromptEdge`: Every option judgment must cite or reject the local definition anchor; otherwise mark evidence weak.
- `ConflictResolutionPromptEdge`: A hard contradiction veto blocks forwarding; a soft contradiction increases the learned gate penalty.
- `MemoryBridgePromptEdge`: Read the compressed task intent and definition bridge, but never treat it as ground truth.

- Next required run: `R408_nonmath_curriculum_fresh_preflight`
