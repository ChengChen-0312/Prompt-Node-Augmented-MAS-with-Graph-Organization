# R083 Tail34 Clean-Fix PromptNode Template Candidates

**Claim boundary**: R083 materializes R082 clean-fix PromptNode templates on AQuA tail34. It validates graph metadata coverage only; accuracy requires a subsequent forced-execution run.

- Template source: `experiment/aqua/aqua_first200_r082_clean_fix_graph_templates.jsonl`
- Task split: `experiment/aqua/task_split_aqua_tail34.json`
- Output candidates: `experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl`
- Tail34 tasks: `34`
- Template source count: `17`
- Top-K per task: `5`
- Total materialized candidates: `170`
- Selected templates with full PromptNode specs: `5`
- Selected templates with edge permissions: `5`
- Forbidden-field violations: `0`

| Rank | Support | Nodes | Edges | Signature |
| ---: | ---: | ---: | ---: | --- |
| `1` | `35` | `5` | `5` | `Math Solver|PN_Memory|PN_Router|PN_Verifier|Programming Expert::0->1,0->2,1->2,2->3,3->4` |
| `2` | `5` | `5` | `5` | `Inspector|Math Solver|PN_Memory|PN_Router|PN_Verifier::0->1,0->2,1->2,2->3,3->4` |
| `3` | `5` | `5` | `5` | `Math Solver|PN_Memory|PN_Router|PN_Verifier::0->1,0->2,1->2,2->3,3->4` |
| `4` | `4` | `5` | `5` | `Inspector|PN_Memory|PN_Router|PN_Verifier|Programming Expert::0->1,0->2,1->2,2->3,3->4` |
| `5` | `4` | `6` | `7` | `Math Solver|PN_Memory|PN_Router|PN_Verifier|Programming Expert::0->1,0->2,0->3,1->3,2->3,3->4,4->5` |

## Interpretation

R083 closes the metadata gap exposed by R081 without claiming an accuracy gain: every tail34 task now has clean-fix-derived PromptNode graph candidates with first-class node identities, permissions, budgets, and lifecycle actions. The next accuracy-bearing step is to add a forced-template execution hook and run a small smoke before a full tail34 evaluation.
