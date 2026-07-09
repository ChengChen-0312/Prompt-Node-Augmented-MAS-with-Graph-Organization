# R340 Answer-Bearing Candidate Generator Design

**Claim boundary**: R340 designs general answer-bearing verifier families after R339 found no switch candidates. It does not use true labels, task ids, or API calls.

| Family | Trigger | Contract |
|---|---|---|
| `option_by_option_symbolic_verifier` | Multiple-choice STEM item with formula, numeric, set, or symbolic options. | May emit candidate_label only when at least two independent option checks support the same option and no checked option contradicts it. |
| `coordinate_geometry_verifier` | Visible item mentions reflection, rotation, translation, slope, distance, polygon, or coordinate pairs. | Derive transformed coordinates from the stem and match against options. |
| `algebraic_structure_verifier` | Visible item mentions group, field, vector space, transformation, null space, quotient, ring, ideal, or polynomial over finite fields. | Construct minimal algebraic invariants and compare with options. |
| `chemistry_balancer_verifier` | Visible item contains chemical species, ions, reaction arrows, oxidation/reduction wording, or coefficient ratios. | Balance or sanity-check the visible reaction and emit an answer only when option agreement is concrete. |

- Next required run: `R341_answer_bearing_candidate_generator_preflight`
