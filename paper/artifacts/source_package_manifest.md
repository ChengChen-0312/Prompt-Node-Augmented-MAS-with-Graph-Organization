# Source Package Manifest

This manifest lists the local source files needed for journal-template conversion or manual external review.

## Include

- `paper/appendices/label_audit.tex`
- `paper/artifacts/journal_template_probe.md`
- `paper/artifacts/reproducibility_index.md`
- `paper/main.tex`
- `paper/math_commands.tex`
- `paper/references.bib`
- `paper/sections/0_abstract.tex`
- `paper/sections/1_introduction.tex`
- `paper/sections/2_related_work.tex`
- `paper/sections/3_method.tex`
- `paper/sections/4_experimental_setup.tex`
- `paper/sections/5_results.tex`
- `paper/sections/6_case_studies.tex`
- `paper/sections/7_limitations.tex`
- `paper/sections/8_conclusion.tex`
- `paper/tables/cost_results.tex`
- `paper/tables/main_results.tex`

## Exclude

- `.env`
- `*.key`
- `*api_key*`
- `run_logs/*_api_results.jsonl`
- `__pycache__`

## Packaging Notes

- Do not include API key values or local `.env` files.
- Do not treat this package as submission-ready until external audits and PDF compilation are complete.
- Keep the current article scaffold as the editable source until JAIR or KAIS template conversion is explicitly performed.
