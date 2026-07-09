# Submission Readiness Matrix

| Item | Status | Evidence | Required Next Action |
|---|---|---|---|
| `local_manuscript_artifacts` | `ready_local` | R460 confirms appendix, artifact index, and local smoke after polish. | Keep synchronized while audits and template conversion proceed. |
| `source_package_manifest` | `ready_local` | R463 lists paper source files and exclusion patterns. | Use for future JAIR/KAIS template conversion or manual review import. |
| `external_audits` | `blocked` | R464 lists three payloads but transmission_performed=false. | Obtain explicit user authorization, then run/import experiment, claim, and citation reviews. |
| `pdf_compile` | `blocked` | R452 found no latexmk or pdflatex. | Install or locate a TeX engine, then compile and visually inspect the PDF. |
| `official_jcr_verification` | `blocked` | R467 records public planning sources only; official_jcr_verification_completed=false. | Verify JAIR/KAIS in official JCR or institutional Web of Science. |
| `journal_template_conversion` | `blocked` | R462 records JAIR/KAIS templates but template_conversion_performed=false. | Convert after external audits settle claim scope. |

- Paper claim authorized: `False`
- SCI-Q2 ready: `False`
