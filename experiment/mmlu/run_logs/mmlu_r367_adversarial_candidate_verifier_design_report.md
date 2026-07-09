# R367 Adversarial Candidate Verifier Design

**Claim boundary**: R367 designs candidate-quality improvements after R363/R365. It does not relax the R360 gate and does not authorize API execution.

| PromptNode | Purpose | Contract |
|---|---|---|
| `PN_AdversarialCandidateVerifier` | Try to falsify a high-confidence single candidate before it can override ARG. | Write contradiction evidence; forward block signal if an independent contradiction is found. |
| `PN_ChemPhysicsVerifier` | Generate candidates for chemistry and physics missed-fix clusters using formula, conservation, and concept checks. | Forward only with explicit equation/concept evidence and candidate_label. |
| `PN_PassageHistoryEntailmentVerifier` | Generate candidates for history/passage missed-fix tasks using visible quote entailment. | Forward only when the option is directly supported by quoted or visible source text. |
| `PN_AbstractMathCounterexampleVerifier` | Challenge abstract math candidates with counterexamples, theorem condition checks, and option-by-option negation. | Block candidate if theorem assumptions are misstated or a counterexample supports another option. |

## PromptEdges

- `challenge_candidate_before_forward`
- `write_adversarial_contradiction`
- `block_forward_on_independent_contradiction`
- `route_domain_missed_fix_to_specialized_verifier`
- `merge_candidate_and_adversarial_evidence_before_gate`

- Next required run: `R368_adversarial_verifier_preflight`
