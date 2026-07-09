# R147 Tail34 Frozen-Selector Replay and Expansion Protocol

**Claim boundary**: full-tail34 frozen-selector replay using R059 ARG baseline plus R146 switch API results; not a fresh integrated full run, transfer result, robustness proof, or SCI-readiness claim

- Full tail34 replay only: `True`
- No new API run: `True`
- Fresh integrated full run: `False`
- Baseline accuracy: `28/34`
- Selected accuracy: `30/34`
- Switch tasks: `['task_108', 'task_250']`
- Fallback task count: `32`
- PN graph evidence on switches: `2/2`
- Switch update2 metadata: `2/2`
- Fix/harm: `2/0`
- Clean fix/harm: `1/0`
- Noisy fix/harm: `1/0`
- Uses tail34 training source: `False`
- Baseline cost: `$0.932850`
- Incremental PromptNode cost: `$0.070710`
- Selected estimated cost: `$1.003560`
- Cost ratio vs baseline: `1.0758`
- Baseline correct per dollar: `30.015544`
- Selected correct per dollar: `29.893579`
- R146 smoke gate passed: `True`
- Broad API allowed next: `False`
- Next protocol: `r148_tail34_replay_statistical_audit_and_transfer_preflight`

| Task | Label | Source | Baseline | Selected | Truth | Fix | Harm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `task_114` | `noisy` | `r059_arg_fallback` | `C` | `C` | `D` | `False` | `False` |
| `task_56` | `clean` | `r059_arg_fallback` | `A` | `A` | `A` | `False` | `False` |
| `task_107` | `clean` | `r059_arg_fallback` | `B` | `B` | `B` | `False` | `False` |
| `task_240` | `clean` | `r059_arg_fallback` | `B` | `B` | `B` | `False` | `False` |
| `task_179` | `clean` | `r059_arg_fallback` | `B` | `B` | `B` | `False` | `False` |
| `task_166` | `clean` | `r059_arg_fallback` | `C` | `C` | `C` | `False` | `False` |
| `task_183` | `clean` | `r059_arg_fallback` | `D` | `D` | `D` | `False` | `False` |
| `task_50` | `clean` | `r059_arg_fallback` | `C` | `C` | `C` | `False` | `False` |
| `task_143` | `clean` | `r059_arg_fallback` | `E` | `E` | `E` | `False` | `False` |
| `task_251` | `clean` | `r059_arg_fallback` | `A` | `A` | `A` | `False` | `False` |
| `task_154` | `clean` | `r059_arg_fallback` | `C` | `C` | `C` | `False` | `False` |
| `task_129` | `clean` | `r059_arg_fallback` | `D` | `D` | `D` | `False` | `False` |
| `task_59` | `noisy` | `r059_arg_fallback` | `B` | `B` | `C` | `False` | `False` |
| `task_55` | `clean` | `r059_arg_fallback` | `A` | `A` | `A` | `False` | `False` |
| `task_23` | `clean` | `r059_arg_fallback` | `A` | `A` | `A` | `False` | `False` |
| `task_7` | `clean` | `r059_arg_fallback` | `C` | `C` | `C` | `False` | `False` |
| `task_8` | `clean` | `r059_arg_fallback` | `E` | `E` | `E` | `False` | `False` |
| `task_108` | `noisy` | `r146_calibrated_promptnode_switch` | `B` | `D` | `D` | `True` | `False` |
| `task_151` | `clean` | `r059_arg_fallback` | `E` | `E` | `E` | `False` | `False` |
| `task_22` | `clean` | `r059_arg_fallback` | `E` | `E` | `E` | `False` | `False` |
| `task_139` | `noisy` | `r059_arg_fallback` | `D` | `D` | `E` | `False` | `False` |
| `task_228` | `noisy` | `r059_arg_fallback` | `C` | `C` | `B` | `False` | `False` |
| `task_250` | `clean` | `r146_calibrated_promptnode_switch` | `A` | `E` | `E` | `True` | `False` |
| `task_173` | `clean` | `r059_arg_fallback` | `C` | `C` | `C` | `False` | `False` |
| `task_26` | `clean` | `r059_arg_fallback` | `C` | `C` | `C` | `False` | `False` |
| `task_188` | `clean` | `r059_arg_fallback` | `D` | `D` | `D` | `False` | `False` |
| `task_35` | `clean` | `r059_arg_fallback` | `A` | `A` | `A` | `False` | `False` |
| `task_57` | `clean` | `r059_arg_fallback` | `D` | `D` | `D` | `False` | `False` |
| `task_62` | `clean` | `r059_arg_fallback` | `B` | `B` | `B` | `False` | `False` |
| `task_70` | `clean` | `r059_arg_fallback` | `C` | `C` | `C` | `False` | `False` |
| `task_189` | `clean` | `r059_arg_fallback` | `B` | `B` | `B` | `False` | `False` |
| `task_6` | `noisy` | `r059_arg_fallback` | `D` | `D` | `D` | `False` | `False` |
| `task_28` | `clean` | `r059_arg_fallback` | `B` | `B` | `B` | `False` | `False` |
| `task_163` | `clean` | `r059_arg_fallback` | `D` | `D` | `D` | `False` | `False` |

## Interpretation

R147 gives the first full-tail34 replay for the frozen selector: ARG fallback is retained on 32 tasks, and the two pre-registered switch tasks use R146 calibrated PromptNode outputs. This supports a replay-level tail34 improvement boundary (`30/34` vs `28/34`) but still requires statistical audit, transfer preflight, and eventually broader validation before paper-level claims.
