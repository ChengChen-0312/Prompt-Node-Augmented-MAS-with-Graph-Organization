# R339 Selector Non-Switch Failure Analysis

**Claim boundary**: R339 explains why R337 tied ARG: the selector never switched because the prospective candidate generator produced no answer-bearing candidates. This analysis blocks more API expansion until candidate generation is fixed.

- Selector action counts: `{'KEEP_ARG': 24}`
- Selector switches: `0`
- Baseline wrong tasks: `4`
- Answer-bearing candidates: `0`
- Candidate type counts: `{'instruction_ambiguity_verifier': 3, 'none': 21}`
- Root causes: `['no_answer_bearing_candidates', 'over_conservative_switch_contract', 'candidate_library_does_not_cover_prospective_stem_errors']`
- Next required run: `R340_answer_bearing_candidate_generator_design`
