# R441 External Citation Context Audit Prompt

Audit each related-work citation for existence, metadata correctness, and whether the cited paper supports the exact surrounding sentence.

## Files To Inspect

- `paper/references.bib`
- `paper/sections/2_related_work.tex`
- `paper/.aris/citation-audit/r438_static_contexts.json`
- `.aris/verify-papers/r436_citation_metadata.json`

## Required Output

Return PASS/WARN/FAIL with file:line evidence and concrete fixes.