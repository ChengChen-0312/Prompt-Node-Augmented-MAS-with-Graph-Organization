# R398 Nonmath Contrastive Verifier Design

**Claim boundary**: R398 is a design step derived from R397 error taxonomy. It adds general-purpose nonmath PromptNodes and PromptEdges, but does not execute API or support a result claim.

## PromptNodes

- `PN_ContrastiveOptionVerifier`: Require the candidate answer to defeat the nearest plausible distractor before forwarding.
- `PN_ConceptDefinitionAnchor`: Anchor the decision in a concise concept or definition before binding an option.
- `PN_AbstentionRecoveryVerifier`: Retry only abstentions by comparing options semantically; it must still leave candidate_label empty if no option is supported.
- `PN_ConsensusConflictResolver`: Block candidate forwarding when the contrastive verifier cannot separate top two options.

## PromptEdges

- `PE_RejectNearestDistractor`: Forward only if the rationale names one plausible distractor and rejects it with a visible reason.
- `PE_DefinitionAnchorBinding`: Forward only if a short concept/definition anchor is present.
- `PE_EvidenceSpecificityGate`: Downweight generic rationales that do not quote or paraphrase a task-specific clue.
- `PE_AbstentionRecoveryRoute`: Route empty candidate_label cases to the abstention recovery verifier; never use gold labels.

- Next required run: `R399_contrastive_verifier_targeted_preflight`
