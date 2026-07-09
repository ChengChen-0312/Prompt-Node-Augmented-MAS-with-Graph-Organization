# R183 MMLU PromptNode/PromptEdge Target Export

**Claim boundary**: Data export only. No API evaluation, no accuracy claim, and no claim that the exported insertion targets improve over ARG-Designer.

## Result

- Source graphs: `403`
- Exported PN/PE target graphs: `403`
- Unique exported questions: `37`
- Transfer100 hashes checked: `100`
- Filtered exact transfer overlaps: `0`
- Failures: `0`
- Target kind: `promptedge_preserve_safe_insert`
- Override labels exported: `0`

## Leakage Boundary

- Exact question hashes were checked against transfer100.
- No tail34 or sync20 data is used.
- Transfer100 answers are not used as training labels.
- Source `.pt` files do not preserve original MMLU source metadata, so the audit is exact-question based rather than source-file/source-index based.

## Next

R184 should dry-run or train a PN-capable MMLU graph generator from this manifest after adapting the training loader to consume exported PN/PE targets.
