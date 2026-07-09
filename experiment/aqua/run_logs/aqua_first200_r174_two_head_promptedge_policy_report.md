# R174 Two-Head PromptNode/PromptEdge Policy Audit

**Claim boundary**: R174 is a no-API target audit. It separates PromptNode/PromptEdge insertion from answer override. Insertion-head target agreement is not answer accuracy; override-head claims are blocked when switch-critical positives are too sparse.

- Source rows: `800`
- Action counts: `{'preserve_safe_insert': 72, 'suppress_or_fallback': 724, 'switch_critical_insert': 4}`
- Insertion positives: `76`
- Override positives: `4`
- Insert observe-only: `72`
- Insert switch-allowed: `4`

## Head Metrics

| Head | Positives | Eval positives | Eval precision | Eval recall | Eval F1 | Data insufficient | Claim supported |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Insertion | `76` | `35` | `0.971` | `0.971` | `0.971` | `False` | `True` |
| Override learned | `4` | `2` | `0.000` | `0.000` | `0.000` | `True` | `False` |
| Override rule | `4` | `all` | `1.000` | `1.000` | `1.000` | `diagnostic` | `False` |

## Interpretation

The insertion head has enough positive rows to learn when first-class PromptNodes and PromptEdges should be generated. The override head does not: only four switch-critical rows exist in R166, split two/two across train/eval, and the learned head has no claimable positive recall. This explains why R171/R172 could make the graph path run but could not robustly beat ARG. The next data iteration must create more non-leaky switch-critical targets before any broad API evaluation.
