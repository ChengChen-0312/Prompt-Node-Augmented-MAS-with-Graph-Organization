# R351 Fresh Coverage PromptNode Expansion Design

**Claim boundary**: R351 expands PromptNode coverage after R349 showed zero fresh coverage. The R349 split is now treated as a coverage-development set, not as a main-claim evaluation set.

| PromptNode | Trigger | Evidence Contract |
|---|---|---|
| `PN_NumericWordProblemSolver` | Arithmetic, counting, probability, combinatorics, divisibility, and simple equation word problems. | Build a small symbolic/numeric model from visible quantities and match exactly one option. |
| `PN_PhysicsFormulaEvaluator` | Capacitor energy, friction stopping distance, idealized kinematics, mole/pressure ratios, and common formula substitution tasks. | Select and execute a named formula only when all variables are visible and exactly one option matches. |
| `PN_ChemistryConceptAndStoichiometryTool` | Element symbols, mole fractions, periodic-table facts, reaction balancing, and electron-configuration concepts. | Forward only when a deterministic lookup, mole computation, or conservation equation verifies one option. |
| `PN_PassageEntailmentVerifier` | History, law, or ethics items with an explicit quoted passage or case facts. | Use only passage/fact entailment; forward only if the option is directly supported and alternatives contradict the visible text. |
| `PN_DefinitionFallacyVerifier` | Definition-heavy items about fallacies, named theories, rules, or canonical terms. | Use a compact curated definition table; forward only on exact definition match, otherwise write warning-only evidence. |
| `PN_ClozeSemanticConsistencyVerifier` | Fill-in-the-blank and option semantic consistency tasks. | Check grammatical and semantic consistency across all blanks; forward only when one option satisfies every slot. |
| `PN_ConsensusConflictResolver` | Any item where tool and ARG disagree or several PromptNodes produce competing candidates. | Default to KEEP_ARG unless a candidate has machine/textual evidence and no unresolved contradiction. |

- Next required run: `R352_fresh_coverage_promptnode_expansion_preflight`
