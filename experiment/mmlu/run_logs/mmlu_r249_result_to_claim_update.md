# R249 Result-to-Claim Update

**Claim boundary**: claim-matrix update only. No API, no new accuracy claim, and no SCI-Q2 readiness claim.

## Updated Claim Status

| Claim | Status | Evidence |
|---|---|---|
| A fitted label-free selector can learn when virtual evidence should alter ARG | Supported offline, small frozen split | R242 train `28/33` vs `23/33`; frozen_eval `29/34` vs `28/34`; features exclude labels |
| Conservative selector improves AQuA replay without clean harm | Supported offline | R236 first200 `170/200` vs `165/200`, fix/harm `5/0`; R237 all `57/67` vs `51/67`, fix/harm `6/0` |
| Conservative selector beats simple controls | Partially supported offline | R243 beats abstain/random and lowers harm vs always; does not beat node-only |
| PromptEdge text independently causes the current gain | Not supported | R243 node-only/no-PromptEdge-text equals proposed `57/67` |
| PromptNode lifecycle is represented in evidence | Supported as annotation only | R247 `75` annotations: update/prune/merge/compress/upgrade; edge actions read/forward/write |
| MMLU transfer can be probed without label leakage | Supported as protocol only | R248 `100` rows, `12` ARG errors, `88` controls; features exclude true answers |
| MMLU transfer accuracy improves with PN/PE | Not supported | R202 tied baseline `11/12`; R248 is only a probe table |
| Current package is SCI-Q2 ready | Not supported | Still lacks live held-out PN/PE selector evaluation, transfer improvement, cost-matched controls, and citation audit |

## Paper Plan Impact

The paper should frame the method as a constrained PromptNode/PromptEdge graph policy with a learned or fitted abstention boundary. The current evidence does not justify saying that edge prompt text is the source of the gain. It also does not justify saying that the method transfers to MMLU; R248 only prepares a leakage-safe transfer probe.

## Next

R250 must run the mandatory five-iteration goal audit. If aligned, the next experiment should choose a tiny MMLU transfer probe or live graph-policy preflight, not broad API evaluation.
