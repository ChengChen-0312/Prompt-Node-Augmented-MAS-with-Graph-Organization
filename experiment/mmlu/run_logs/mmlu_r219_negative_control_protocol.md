# R219 Router-Final Negative-Control Protocol

**Claim boundary**: protocol only. No API evaluation and no accuracy claim.

## Input

R218 mini-manifest:

- records: `67`
- train records: `33`
- frozen eval records: `34`
- switch labels: `13`

## Negative Controls

| Control | Purpose |
|---|---|
| `abstain_only_router` | tests whether answer-changing labels add value |
| `random_switch_labels_same_rate` | controls for random switching at the same rate |
| `shuffled_promptedge_order` | tests whether PN/PE order matters |
| `node_only_no_promptedge_text` | tests whether virtual nodes alone explain gains |
| `edge_text_only_no_router_target` | tests prompt-as-edge without learned router labels |
| `always_switch_to_objective` | tests over-aggressive switching |
| `cost_matched_arg_requery` | controls for spending extra model calls/tokens |

## Cost Protocol

API remains blocked until R220.

If R220 later permits a tiny diagnostic:

- max tasks: `4`
- max cost: `$0.45`
- same model: `gpt-4o-2024-08-06`
- logs required: raw/projected graph, PromptEdge metadata, router schema, costs/tokens
- compare against cost-matched ARG re-query, not only original ARG

## Claim Gate

No paper claim is allowed unless all are true:

- proposed router-final beats abstain-only and random-switch controls;
- no clean/control harms;
- cost-normalized result beats cost-matched ARG re-query;
- leakage scan passes;
- held-out/random evaluation improves over ARG.

## Decision

`api_blocked_until_R220_and_control_implementation`
