# R298 MMLU ARG Wrong-Case Label Audit

**Scope**: Audit the two R292 ARG wrong cases on MMLU transfer100 first24 before using them as method targets.

## Cases

| Task | Dataset label | ARG prediction | Audit verdict |
|---|---:|---:|---|
| `MMLU-high_school_statistics_test-32` | `D` | `B` | Label appears correct after MMLU option compression. The source AP Statistics item is five-choice, where `None of the above` is option `E`; MMLU removes the original `D` and maps `None of the above` to `D`. |
| `MMLU-high_school_physics_test-67` | `A` | `C` | Label appears wrong. Public AP Physics source gives `C` for the same question, and Ohm's law supports increased voltage plus decreased resistance. |

## Clean Rescore

Treating `MMLU-high_school_physics_test-67` as label-noisy with clean answer `C`:

| Run | Official | Audit-clean |
|---|---:|---:|
| `R292_ARG` | `22/24` | `23/24` |
| `R291_PN_all` | `20/24` | `21/24` |
| `R296_PN_specialist` | `20/24` | `21/24` |

## Implication

MMLU first24 is harder than it looked for the proposed method: after label audit, ARG is effectively `23/24`, while the current PromptNode variants remain `21/24`. The next method should not target the noisy physics item. It should target `MMLU-high_school_statistics_test-32` only if PromptNode evidence can justify `D` without task-specific patches, and it must preserve ARG on all already-correct clean cases.

## Sources

- AP Physics public explanation: `https://www.crackap.com/ap/physics-1/question-45-answer-and-explanation.html`
- AP Statistics public explanation: `https://www.crackap.com/ap/statistics/question-331.html`
