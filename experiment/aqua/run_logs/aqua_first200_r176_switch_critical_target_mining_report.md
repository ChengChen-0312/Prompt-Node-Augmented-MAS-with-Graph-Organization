# R176 Switch-Critical Target Mining Audit

**Claim boundary**: R176 is a no-API target-mining audit. Weak high-margin tie rows are diagnostic expansion candidates only; they are not claimable learned override labels without additional validation.

- R112 switch rows: `11`
- R166 switch rows: `4`
- Gap class counts: `{'confirmed_switch_critical': 4, 'low_confidence_promptnode_candidate': 4, 'no_promptnode_candidate': 1, 'weak_high_margin_tie_candidate': 2}`
- Confirmed switch-critical rows: `4`
- Weak high-margin tie rows: `2`
- Expanded pool if weak included: `6`
- Expanded pool by slice: `{'aqua_100': 3, 'aqua_next100': 3}`
- Expanded pool still insufficient: `True`

| Task | Slice | Gap class | Claimable override | Weak expansion | Candidate rows |
| --- | --- | --- | --- | --- | ---: |
| `task_152` | `aqua_100` | `no_promptnode_candidate` | `False` | `False` | `4` |
| `task_172` | `aqua_100` | `confirmed_switch_critical` | `True` | `False` | `4` |
| `task_95` | `aqua_100` | `low_confidence_promptnode_candidate` | `False` | `False` | `4` |
| `task_135` | `aqua_100` | `weak_high_margin_tie_candidate` | `False` | `True` | `4` |
| `task_122` | `aqua_100` | `confirmed_switch_critical` | `True` | `False` | `4` |
| `task_149` | `aqua_100` | `low_confidence_promptnode_candidate` | `False` | `False` | `4` |
| `task_176` | `aqua_next100` | `confirmed_switch_critical` | `True` | `False` | `4` |
| `task_184` | `aqua_next100` | `low_confidence_promptnode_candidate` | `False` | `False` | `4` |
| `task_197` | `aqua_next100` | `low_confidence_promptnode_candidate` | `False` | `False` | `4` |
| `task_67` | `aqua_next100` | `weak_high_margin_tie_candidate` | `False` | `True` | `4` |
| `task_207` | `aqua_next100` | `confirmed_switch_critical` | `True` | `False` | `4` |

## Interpretation

R112 contains more potential switch decisions than R166, but the existing non-leaky graph-policy traces only provide four confirmed switch-critical PromptNode/PromptEdge targets. Two additional rows are high-margin multi-view ties and may be useful as weak curriculum examples, but treating them as confirmed override labels would overstate the evidence. Even with weak rows included, the override pool remains too small for a learned override-head claim.
