# R227 Runtime Integration Contract

**Claim boundary**: contract only. No implementation inside `TestGraph`, no API evaluation, and no accuracy claim.

## Purpose

Future router-final evaluation must compare the proposed method against controls inside the same runtime accounting surface. R227 defines that surface before any model call.

## Required Inputs

- `task_id`
- raw graph and projected graph
- PromptEdge metadata and permissions
- router-final schema
- control variant
- router action
- target option label
- model-visible input

## Required Outputs

- baseline answer
- router-final answer
- control variant
- `would_switch`
- selected label
- fallback reason
- cost
- prompt/completion tokens
- leakage pass/fail

## Fallback Rules

1. If `router_action=abstain`, keep the baseline answer.
2. If `target_option_label` is not allowed, keep the baseline answer.
3. If `leakage_pass=false`, reject the row.
4. If `control_variant=cost_matched_arg_requery`, do not apply PN/PE router labels.
5. Log raw and projected graph audits for every row.

## Required Variants

- proposed router-final
- abstain-only router
- random-switch same-rate
- always-switch-to-objective
- node-only/no-PromptEdge-text
- cost-matched ARG re-query

## Decision

API remains blocked until this contract has a dry-run artifact. R228 should produce that dry-run log using the proposed and control manifests.
