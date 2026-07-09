# R316 PromptEdge And Cost Controls

**Claim boundary**: Same non-STEM40 control run. It tests promptedge text removal and direct requery cost controls; it is not a broad claim.

| Variant | Correct | Accuracy | Delta vs ARG | Fix/Harm | Switches | API executed/errors |
|---|---:|---:|---:|---:|---:|---:|
| `arg_baseline_fixed` | `37/40` | `0.925` | `0` | `0/0` | `0` | `0/0` |
| `node_only_no_promptedge_text` | `35/40` | `0.875` | `-2` | `0/2` | `3` | `40/0` |
| `plain_requery` | `37/40` | `0.925` | `0` | `1/1` | `2` | `40/0` |

- Cost: `$0.235880`
- Tokens: `22357/8273`
