# R309 Negative Controls

**Claim boundary**: R309 tests whether R306 can be explained by cheap random forwarding, always-forward routing, missing safety gates, random node identity, or disabled lifecycle. It does not authorize training.

- R306 reference main97: `95/97` with `2` forwarded nodes
- Cheap control matches/beats R306: `False`
- Equal-accuracy but higher-cost controls: `['always_forward_candidate_nodes', 'no_lifecycle_prune_disabled']`

## Controls

| control | main97 | fix/harm | forwarded | cost-norm |
|---|---:|---:|---:|---:|
| no_nonmath_promptnodes | `93/97` | `0/0` | `0` | `0.9588` |
| random_forward_same_budget | `92/97` | `0/1` | `2` | `0.9293` |
| always_forward_candidate_nodes | `95/97` | `2/0` | `15` | `0.8482` |
| no_safety_gate_unsafe_forward | `83/97` | `2/12` | `15` | `0.7411` |
| random_promptnode_type_same_budget | `93/97` | `0/0` | `0` | `0.9588` |
| no_lifecycle_prune_disabled | `95/97` | `2/0` | `15` | `0.8482` |

## Next

- Replay the expanded node catalog on AQuA audit-clean tail34 and a non-STEM MMLU split.
- Keep training blocked until transfer is non-negative and ablations identify which PromptNode families contribute.
- Track cost-normalized accuracy because always-forward/no-lifecycle can tie accuracy with much higher routing cost.
