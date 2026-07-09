# R120 Goal Audit After R116-R120

**Claim boundary**: five-iteration goal audit and correction, not an accuracy result

## Window

- R116: baseline-only trigger audit
- R117: lightweight objective-trace protocol
- R118: offline calibrated single-view probe replay
- R119: prospective calibrated single-view smoke
- R120: goal audit and correction

## Verdict

Status: `aligned_after_correction`

The work is still aligned with the SCI-Q2 goal because R116-R119 did not overclaim. However, R119 detects a real drift risk: the search for lower cost moved toward a single-view shortcut that no longer reliably expresses the user's update2 design of first-class PromptNode graph nodes.

## Evidence

- R119 selected accuracy: `2/4`
- R119 internal ARG accuracy: `3/4`
- R119 calibrated-only accuracy: `2/4`
- R119 fix/harm: `0/1`
- R119 clean fix/harm: `0/1`
- R119 clean harm tasks: `task_250`
- R119 PromptNode graph hits: `0/4`
- R119 strong router-contract rows: `0/4`
- R119 policy-input violations: `0`
- R119 cost: `$0.235285`

## Drift Detected

The drift is not "using PromptNode too much"; it is using too little PromptNode evidence. In R119, the calibrated single-view records did not expose explicit PromptNode graph evidence or strong router contracts, so the proxy rule switched on `task_250` using direct-vote support rather than robust virtual-node evidence. That violates the intended SCI-Q2 method story if promoted to a main path.

## Correction

- Demote `calibrated_single_view_probe` to a negative control.
- Do not run broad tail34 or transfer with this single-view policy.
- Require explicit PromptNode graph evidence or strong router-contract evidence before a switch can be considered.
- Prefer guarded two-view agreement or a train-time graph-policy selector over one-view direct-vote support.
- Re-run the same four-task smoke before any broader API run.

## Next Step

R121 should freeze a `guarded_two_view_or_graph_policy_probe_smoke` protocol. The gate must block switches when the only evidence is calibrated direct-vote support, and it must preserve clean-harm safety on `task_250` under fresh-run volatility.
