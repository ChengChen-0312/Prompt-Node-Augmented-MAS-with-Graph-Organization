# R081 Tail34 PromptNode Metadata Audit

**Claim boundary**: positive tail34 sources lack explicit PromptNode graph metadata, while the dense metadata-compatible R058 source is negative. This audit shows the next candidate pool must combine positive clean-fix behavior with first-class PromptNode graph metadata.

- Output rows: `experiment/aqua/aqua_tail34_r081_promptnode_metadata_audit_rows.jsonl`
- Sources audited: `8`
- Positive accuracy sources: `5`
- Positive sources with PromptNode roles: `0`
- Dense metadata negative sources: `1`

| Source | Records | Records with graph | Records with PN roles | PN variant graphs | Positive accuracy source |
| --- | ---: | ---: | ---: | ---: | ---: |
| `R058_dense_generated_pn` | `34` | `34` | `34` | `34/34` | `False` |
| `R064_router_view` | `34` | `34` | `0` | `0/34` | `True` |
| `R064_candidate_view` | `34` | `34` | `0` | `0/34` | `False` |
| `R064_conservative_view` | `34` | `34` | `0` | `0/34` | `False` |
| `R064_calibrated_view` | `34` | `34` | `0` | `0/34` | `True` |
| `R069_fresh_integrated_multiview` | `34` | `25` | `0` | `0/100` | `True` |
| `R072_fresh_cascade` | `34` | `26` | `0` | `0/58` | `True` |
| `R074_fresh_surgical_cascade` | `34` | `13` | `0` | `0/28` | `True` |

## Interpretation

R081 explains why R078 cannot yet become the main SCI method. The tail34 sources with positive accuracy signal (R064/R069/R072/R074) do not expose explicit PromptNode roles in their generated graphs. The only audited tail34 source with PromptNode roles on every record is R058, and R080 shows that source harms accuracy. The next experiment must generate clean-fix-aligned PromptNode graph candidates, not simply rescore the existing positive traces or reuse dense R058 candidates.
