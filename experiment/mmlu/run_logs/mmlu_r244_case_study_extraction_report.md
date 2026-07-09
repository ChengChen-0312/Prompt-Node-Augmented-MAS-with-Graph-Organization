# R244 Conservative Policy Case Studies

**Claim boundary**: Case-study extraction only; no API, no superiority claim, and no SCI-Q2 readiness claim.

Selected case ids: `{'frozen_fix': 'task_250', 'train_fix': 'task_135', 'abstain_protected_clean': 'task_95', 'no_fix_objective_wrong': 'task_152'}`

### frozen_fix

- Task: `task_250` / split `frozen_eval` / clean `clean`
- Baseline/objective/selected/true: `A` / `E` / `E` / `E`
- Switch: `True`; fix/harm: `True` / `False`
- Feature score/majority: `3` / `2`
- Audit: `exact`, `none`
- Question: The population of a city is 5265526. If there are 4169516 adults in the city, how many children are there in the city? Choices: A)1095961 B)1065961 C)1085961 D)1097961 E)1096061

### train_fix

- Task: `task_135` / split `train` / clean `noisy`
- Baseline/objective/selected/true: `NONE` / `D` / `D` / `D`
- Switch: `True`; fix/harm: `True` / `False`
- Feature score/majority: `11` / `0`
- Audit: `contradictory`, `arithmetic_error`
- Question: If there are 5,000 voters out of which 20% are not eligible to vote and there are two candidates contesting. The winning candidate won by 15% of the votes. What is the total number of votes he got ? Choices: A)3267 B)2678 C)2797 D)2300 E)2781

### abstain_protected_clean

- Task: `task_95` / split `train` / clean `clean`
- Baseline/objective/selected/true: `A` / `B` / `A` / `A`
- Switch: `False`; fix/harm: `False` / `False`
- Feature score/majority: `3` / `3`
- Audit: `exact`, `none`
- Question: A number of friends decided to go on a picnic and planned to spend Rs. 96 on eatables. Four of them, however, did not turn up. As a consequence, the remaining ones had to contribute Rs. 4 extra, each. The number of those who attended the picnic was Choices: A)8 B)12 C)16 D)24 E)25

### no_fix_objective_wrong

- Task: `task_152` / split `train` / clean `noisy`
- Baseline/objective/selected/true: `NONE` / `E` / `E` / `C`
- Switch: `True`; fix/harm: `False` / `False`
- Feature score/majority: `3` / `0`
- Audit: `contradictory`, `arithmetic_error`
- Question: If Jill needed to buy 10 bottles of soda for a party in which 8 people attended, how many bottles of soda will she need to buy for a party in which 12 people are attending? Choices: A)6 B)8 C)10 D)12 E)14

## Interpretation

These cases support paper discussion but not a result claim. They show where the fitted abstention policy helps, where it protects a clean ARG-correct case, and where neither baseline nor objective evidence is sufficient.

## Verification

| Test | Result |
|---|---:|
| `tests.test_r244_case_study_extraction` | `1/1` |
| `tests.test_r243_control_comparison` | `1/1` |
