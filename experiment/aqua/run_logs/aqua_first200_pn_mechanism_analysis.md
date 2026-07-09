# AQuA First200 PromptNode Mechanism Analysis

**Date**: 2026-07-08
**Slices**: first100 + next100 from `task_split_aqua.json`
**LLM**: `gpt-4o-2024-08-06`
**Baseline checkpoint**: `output/aqua_sync20_model_20260707-230509`
**PromptNode checkpoint**: `output/aqua_pn_router_contract_model_20260708-030015`
**Purpose**: Explain where PromptNode helps, where it hurts, and what claim the current evidence supports.

## Raw Data Table

| Method | Accuracy | Clean | Noisy/Ambiguous | Delta vs ARG | Cost | Prompt Tokens | Completion Tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ARG baseline | `165/200` | `152/167` | `13/33` | reference | `$4.955370` | `370359` | `206905` |
| PN router-contract | `159/200` | `148/167` | `11/33` | `-6` | `$7.065200` | `551167` | `287291` |
| PN candidate selection | `161/200` | `149/167` | `12/33` | `-4` | `$7.799600` | `652942` | `302326` |
| PN conservative router | `161/200` | `149/167` | `12/33` | `-4` | `$7.043475` | `545907` | `287596` |
| PN calibrated utility | `164/200` | `150/167` | `14/33` | `-1` | `$6.891590` | `505474` | `290948` |
| PN result ensemble | `170/200` | `154/167` | `16/33` | `+5` | result aggregation | n/a | n/a |

The split contains `167` clean rows and `33` noisy/ambiguous rows according to the option-binding audit.

## Fix/Harm Against ARG Baseline

| Method | Fixes | Harms | Clean Fixes | Clean Harms | Noisy Fixes | Noisy Harms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PN router-contract | `9` | `15` | `5` | `9` | `4` | `6` |
| PN candidate selection | `5` | `9` | `1` | `4` | `4` | `5` |
| PN conservative router | `8` | `12` | `5` | `8` | `3` | `4` |
| PN calibrated utility | `9` | `10` | `3` | `5` | `6` | `5` |
| PN result ensemble | `9` | `4` | `3` | `1` | `6` | `3` |

Ensemble changed rows:

Summary: ensemble fixes/harms are `9/4` against the ARG baseline.

| Type | Task IDs |
| --- | --- |
| Fixes | `task_135`, `task_122`, `task_146`, `task_106`, `task_136`, `task_162`, `task_232`, `task_67`, `task_207` |
| Harms | `task_0`, `task_198`, `task_184`, `task_69` |

## PromptNode Coverage

| Method | Selected Graphs With PN | Any Candidate Graph With PN | Avg Candidate Count | Avg Nodes | Avg Edges |
| --- | ---: | ---: | ---: | ---: | ---: |
| PN router-contract | `129/200` | `129/200` | `1.0` | `4.285` | `4.195` |
| PN candidate selection | `194/200` | `195/200` | `4.0` | `5.250` | `5.540` |
| PN conservative router | `129/200` | `129/200` | `1.0` | `4.285` | `4.195` |
| PN calibrated utility | `129/200` | `129/200` | `1.0` | `4.285` | `4.195` |

PN coverage alone does not explain accuracy. Candidate selection inserted or selected virtual-node graphs on nearly all rows (`194/200`) but still underperformed ARG baseline (`161/200` vs `165/200`). The issue is not lack of PromptNode activation; it is unreliable utility selection.

## Complementarity Analysis

Using the five executed systems (`baseline`, `router`, `candidate`, `conservative`, `calibrated`) as an oracle:

| Quantity | Count |
| --- | ---: |
| Solved by at least one system | `180/200` |
| Clean rows solved by at least one system | `159/167` |
| Baseline-wrong rows fixed by at least one PN variant | `15` |
| Baseline-correct rows harmed by at least one PN variant | `27` |
| Rows all systems miss | `20` |

Rows all systems miss:

`task_152`, `task_199`, `task_172`, `task_112`, `task_245`, `task_159`, `task_124`, `task_64`, `task_104`, `task_32`, `task_149`, `task_176`, `task_238`, `task_126`, `task_187`, `task_193`, `task_169`, `task_20`, `task_117`, `task_178`

This supports a narrow but important mechanism claim: virtual-node variants contain complementary evidence that can solve rows missed by ARG-Designer. The current system does not yet reliably select that evidence without causing harms.

## Paired Significance Check

Two-sided exact McNemar/binomial checks against ARG baseline:

| Method | Fixes | Harms | p-value |
| --- | ---: | ---: | ---: |
| PN router-contract | `9` | `15` | `0.3075` |
| PN candidate selection | `5` | `9` | `0.4240` |
| PN conservative router | `8` | `12` | `0.5034` |
| PN calibrated utility | `9` | `10` | `1.0000` |
| PN result ensemble | `9` | `4` | `0.2668` |

The result-level ensemble has the best direction (`+5/200`) but is not statistically strong on first200 alone. It is evidence of complementarity, not a finalized SCI-level main result.

## Interpretation

1. ARG-Designer's high sync20 score is largely explained by clean-row saturation. On sync20, the baseline solves `17/17` audited clean rows; the remaining three rows are noisy/ambiguous option-binding cases. Exceeding `17/20` on that exact slice would require matching noisy labels, which is not a defensible math-improvement claim.
2. Train-time PromptNode is structurally valid and active. The model produces PN graphs in `129/200` to `194/200` rows depending on the variant, so the negative single-method results are not caused by absent virtual nodes.
3. PromptNode evidence is useful but poorly gated. Across variants, at least one PN system fixes `15` baseline-wrong rows, including `7` clean rows beyond baseline's clean coverage. However, at least one PN system also harms `27` baseline-correct rows.
4. The result-level ensemble partially recovers the useful PN signal (`170/200`, clean `154/167`) while reducing harms to four rows. Because this aggregation was developed after earlier runs, it should be treated as a promising mechanism result requiring pre-registered validation.
5. Cost is currently a weakness. Single PN variants cost about `$6.89-$7.80` on first200 versus `$4.96` for ARG baseline.

## Result-To-Claim Verdict

- **claim_supported**: partial
- **what_results_support**: PromptNode virtual nodes provide complementary evidence beyond ARG-Designer on AQuA first200. A label-free ensemble over baseline and PN variants improves total accuracy from `165/200` to `170/200` and clean accuracy from `152/167` to `154/167`.
- **what_results_do_not_support**: The evidence does not support the original claim that a single PromptNode-ARGDesigner model exceeds ARG-Designer on AQuA sync20. It also does not yet support a statistically strong or cost-efficient SCI Q2 main claim.
- **missing_evidence**: Tail34 pre-registered validation is blocked by `gpt-4o-2024-08-06` quota. Transfer validation requires a multiple-choice benchmark with a comparable checkpoint or a carefully redesigned numeric-answer PN final.
- **recommended_claim_revision**: "PromptNode virtual nodes expose complementary verification and option-binding signals, but require a learned utility selector to convert that signal into stable accuracy gains."

## Suggested Next Experiments

1. Run the fixed tail34 protocol once the same-model API quota is restored. This is the immediate pre-registered validation for the first200 ensemble signal.
2. Train a utility selector using only non-test or newly collected calibration traces. Inputs should include PN binding status, direct-agent agreement, PN/direct conflict, graph score, role coverage, candidate count, and evidence length. The selector must output use-PN, use-direct, or abstain.
3. Add a budget-aware variant that prunes PN execution when direct agents already have strong agreement, because current PN runs cost substantially more than ARG baseline.
4. For transfer, prefer another multiple-choice math benchmark first. Numeric GSM8K/SVAMP transfer should be deferred until there is a numeric PromptNode contract and numeric final-answer gate.
