# AQuA Next100 Held-Out PN Validation

**Date**: 2026-07-08
**Dataset slice**: `task_split_aqua.json` test indices `[100:200]`
**Split file**: `task_split_aqua_next100.json`
**LLM**: `gpt-4o-2024-08-06`
**ARG baseline model**: `output/aqua_sync20_model_20260707-230509`
**PN model**: `output/aqua_pn_router_contract_model_20260708-030015`

## Runs

| Method | Total | Cost | Prompt tokens | Completion tokens |
| --- | ---: | ---: | ---: | ---: |
| ARG baseline | `82/100` | `$2.587155` | `189123` | `109436` |
| PN router-contract | `81/100` | `$3.649760` | `284248` | `148568` |
| PN candidate selection | `82/100` | `$3.968740` | `333383` | `153455` |
| PN conservative router | `79/100` | `$3.646065` | `281610` | `149201` |
| PN calibrated utility | `85/100` | `$3.548945` | `259588` | `150067` |
| PN result ensemble | `85/100` | existing result aggregation | n/a | n/a |

## Option-Binding Audit

Audit file: `aqua_next100_option_binding_audit.jsonl`

| Clean label | Count |
| --- | ---: |
| clean | 82 |
| noisy | 18 |

## Clean/Noisy Split

| Method | Total | Clean | Noisy |
| --- | ---: | ---: | ---: |
| ARG baseline | `82/100` | `75/82` | `7/18` |
| PN router-contract | `81/100` | `75/82` | `6/18` |
| PN candidate selection | `82/100` | `73/82` | `9/18` |
| PN conservative router | `79/100` | `72/82` | `7/18` |
| PN calibrated utility | `85/100` | `77/82` | `8/18` |
| PN result ensemble | `85/100` | `75/82` | `10/18` |

## Fix/Harm Against ARG Baseline

### PN Calibrated Utility

| Split | Fixes | Harms |
| --- | ---: | ---: |
| clean | 3 | 1 |
| noisy | 3 | 2 |

Changed rows:

| Type | Task | Clean label | Gold | ARG pred | PN pred |
| --- | --- | --- | --- | --- | --- |
| HARM | `task_184` | noisy | `D` | `D` | `E` |
| HARM | `task_109` | noisy | `B` | `B` | `A` |
| FIX | `task_197` | clean | `C` | `A` | `C` |
| HARM | `task_69` | clean | `C` | `C` | `A` |
| FIX | `task_162` | noisy | `A` | `None.` | `A` |
| FIX | `task_232` | noisy | `E` | `None.` | `E` |
| FIX | `task_160` | clean | `D` | `B` | `D` |
| FIX | `task_67` | clean | `B` | `A` | `B` |
| FIX | `task_207` | noisy | `C` | `None.` | `C` |

### PN Result Ensemble

| Split | Fixes | Harms |
| --- | ---: | ---: |
| clean | 1 | 1 |
| noisy | 4 | 1 |

The ensemble improves total score on next100, but its held-out gain mostly comes from noisy rows. The cleaner method signal is the calibrated PN utility run, which improves clean rows by +2 net.

## Combined First200 View

Combining the earlier AQuA100 slice with this held-out next100:

| Method | Total | Clean | Noisy |
| --- | ---: | ---: | ---: |
| ARG baseline | `165/200` | `152/167` | `13/33` |
| PN calibrated utility | `164/200` | `150/167` | `14/33` |
| PN result ensemble | `170/200` | `154/167` | `16/33` |

The result-level ensemble shows a combined total gain of +5 and clean gain of +2, but also gains +3 on noisy rows. This is a promising but not yet sufficient SCI Q2 main claim.

## Interpretation

R030 gives the strongest evidence so far that virtual-node variants can provide complementary signal beyond ARG-Designer on held-out data. However:

1. The original sync20 target remains unsolved because sync20 clean rows are saturated and the remaining errors are noisy.
2. Single-method PN calibrated utility is unstable across the first100 and next100 slices.
3. Result-level ensemble improves combined clean accuracy but also gains on noisy labels, so it needs transfer validation and stronger noise-aware reporting.

The next paper-worthy step is transfer validation on another math benchmark or a larger AQuA slice with pre-registered aggregation.

