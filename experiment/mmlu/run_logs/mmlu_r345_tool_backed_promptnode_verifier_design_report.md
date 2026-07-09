# R345 Tool-Backed PromptNode Verifier Design

**Claim boundary**: R345 is a no-API design step after R343 showed prompt-only answer-bearing verifiers followed ARG errors. The new nodes are general executable PromptNodes with PromptEdge contracts, not task-specific answer patches.

| PromptNode | Trigger | Evidence Contract |
|---|---|---|
| `PN_CoordinateTransformer` | Coordinate geometry item with points, vertices, reflection, rotation, translation, or line symmetry. | Parse coordinate pairs, apply the named transformation, and forward only if a transformed point exactly matches one visible option. |
| `PN_FiniteAbelianGroupEnumerator` | Finite abelian group counting item with order, exponent/property, and answer options as small integers. | Enumerate integer partitions/classification invariants under the visible constraint, then match the count to an option. |
| `PN_FiniteFieldDerivativeAnalyzer` | Polynomial-over-finite-field item asking derivative/nullity/range/rank dimensions. | Analyze derivative coefficients modulo field characteristic and compare the resulting dimensions with each option. |
| `PN_RedoxBalanceLinearSolver` | Chemistry reaction item with ionic species, reaction arrow, coefficient ratios, or redox balancing. | Solve element and charge conservation equations and forward only if the balanced coefficients verify exactly one option. |

## PromptEdge Contracts

- `read_visible_problem_only`
- `write_machine_checkable_evidence`
- `forward_exact_single_option_match_only`
- `reject_if_unparsed_or_inconsistent`
- `reject_if_multiple_options_or_no_option_match`
- `record_tool_family_and_lifecycle_action`

- Next required run: `R346_tool_backed_promptnode_local_preflight`
