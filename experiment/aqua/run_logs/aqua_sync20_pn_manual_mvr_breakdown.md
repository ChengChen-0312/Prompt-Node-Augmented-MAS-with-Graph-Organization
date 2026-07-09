# AQuA sync20 Manual Pre-Execution Prompt Node Smoke

**Date**: 2026-07-08
**System**: ARG-Designer generated graph + fixed pre-execution `PN_Memory -> PN_Verifier -> PN_Router`
**Model**: `gpt-4o-2024-08-06`
**Baseline**: ARG-Designer `17/20 = 85.00%`, cost `$0.508365`

## Result

| System | Accuracy | Cost | Prompt Tokens | Completion Tokens | Changed Predictions |
| --- | --- | --- | --- | --- | --- |
| ARG-Designer baseline | 17/20 | $0.508365 | 36723 | 21650 | - |
| Manual PN MVR | 17/20 | $0.959415 | 83343 | 36180 | 0 |

## Wrong Cases

| Task | True | ARG | Manual PN MVR | Note |
| --- | --- | --- | --- | --- |
| `task_152` | C | E | E | No correction. |
| `task_199` | A | C | C | No correction. |
| `task_172` | E | C | C | No correction. |

## Interpretation

Manual pre-execution Prompt Nodes are structurally valid but not sufficient to exceed ARG-Designer on AQuA sync20. This supports the design decision that the main method must be train-time PN-ARGDesigner, where Prompt Node roles and edges appear in the generator's training targets.

The result should be reported as a sanity / negative-control run, not as paper evidence for improvement.
