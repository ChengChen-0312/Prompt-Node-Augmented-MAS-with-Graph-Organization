# R171 Selector-Gated PromptNode/PromptEdge Smoke

**Claim boundary**: bounded four-task selector-gated PromptNode/PromptEdge smoke only; not broad held-out accuracy, transfer evidence, or SCI-Q2 readiness

- Tasks: `4`
- Selected accuracy: `2/4`
- Internal ARG baseline accuracy: `4/4`
- PromptEdge run accuracy: `1/3`
- Delta vs ARG baseline: `-2`
- PromptEdge contract passed: `4/4`
- PromptEdge run count: `3`
- Switch tasks: `['task_8', 'task_108', 'task_250']`
- Fix/Harm: `0/2`
- Selector input violations: `0`
- Cost: `$0.224830`
- Prompt tokens: `18500`
- Completion tokens: `8822`
- Broad API allowed next: `False`
- Next required audit: `R175`

| Task | ARG | PromptEdge | Selector action | Selected | Truth | Selector score | Contract | Fix | Harm |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| `task_8` | `E` | `None` | `run_promptedge` | `None` | `E` | `2.100` | `True` | `False` | `True` |
| `task_108` | `D` | `D` | `run_promptedge` | `D` | `D` | `2.100` | `True` | `False` | `False` |
| `task_188` | `D` | `None` | `fallback_to_arg` | `D` | `D` | `-0.700` | `True` | `False` | `False` |
| `task_250` | `E` | `None` | `run_promptedge` | `None` | `E` | `2.100` | `True` | `False` | `True` |

## Interpretation

R171 executes the R170-authorized bounded smoke. The selector can see only label-free graph-policy fields and live graph observations; task ids, gold answers, correctness flags, and clean/noisy labels are not selector inputs. A PromptNode/PromptEdge view is executed only when both the R168 selector and the PromptEdge graph contract pass. This is a regression smoke, not a paper-level result.
