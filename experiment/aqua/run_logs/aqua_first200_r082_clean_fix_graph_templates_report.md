# R082 Clean-Fix PromptNode Graph Template Export

**Claim boundary**: R082 exports a clean-fix PromptNode graph template library for future candidate generation. It is not an answer-accuracy result.

- Input rows: `experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl`
- Output templates: `experiment/aqua/aqua_first200_r082_clean_fix_graph_templates.jsonl`
- Source rows: `800`
- Positive rows: `76`
- Unique templates: `17`
- Templates with PromptNode specs: `17`
- Templates with edge permissions: `17`
- Forbidden-field violations: `0`

| Rank | Support | Nodes | Edges | PromptNode specs | Candidate-method support |
| ---: | ---: | ---: | ---: | ---: | --- |
| `1` | `35` | `5` | `5` | `3` | `candidate=34, conservative=1` |
| `2` | `5` | `5` | `5` | `3` | `candidate=4, conservative=1` |
| `3` | `5` | `5` | `5` | `3` | `candidate=4, conservative=1` |
| `4` | `4` | `5` | `5` | `3` | `candidate=4` |
| `5` | `4` | `6` | `7` | `3` | `candidate=4` |
| `6` | `4` | `6` | `7` | `3` | `candidate=4` |
| `7` | `3` | `6` | `7` | `3` | `candidate=3` |
| `8` | `3` | `6` | `7` | `3` | `candidate=3` |
| `9` | `3` | `6` | `7` | `3` | `candidate=3` |
| `10` | `2` | `6` | `7` | `3` | `candidate=2` |

## Interpretation

R082 turns the R077 clean-fix-preserve graph targets into a template library that can seed the next candidate generation experiment. This closes the bookkeeping gap exposed by R081: future tail34 candidates must carry explicit PromptNode roles/specs like R058, but they should use graph patterns distilled from clean-fix targets rather than dense R058 generation.
