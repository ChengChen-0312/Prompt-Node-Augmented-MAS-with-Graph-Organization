# AQuA sync20 ARG-Designer Breakdown

## Run Summary

- LLM: `gpt-4o-2024-08-06`
- ARG-Designer model dir: `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/aqua/output/aqua_sync20_model_20260707-230509`
- Split: 20 train = 8 cold-start/base + 12 fine-tune candidates; evaluation limited to first 20 test items
- Eval: 17/20 = 85.00%
- Cost/tokens: $0.508365; prompt 36723; completion 21650

## Training Data That Drove the Gain

- Stage 1 `D_exp`: 21 successful complex graphs from `FullConnected-4`, `Mesh-4`, and `FullConnected-3` over 8 base tasks. Each complex topology solved 7/8.
- Stage 2 `D_eff`: 77 efficient graphs = 9 pruned generated graphs + 62 simple successful graphs + 6 replay complex graphs.
- Simple topology success on the 12 fine-tune tasks: `Chain-2` 11/12, `Star-3` 11/12, `Layered-4` 10/12, `Star-4` 10/12, `Chain-4` 10/12, `Chain-3` 10/12.
- Interpretation: the model first learns correctness from dense graphs, then is fine-tuned toward sparse graphs that still answer correctly. At inference it usually emits 2-3 node graphs, cutting unnecessary communication.

## Generated Graph Statistics on Eval20

- Average nodes: 2.15; average edges: 1.15
- Shape counts: `2n/1e`=17, `3n/2e`=3
- Role counts: `Inspector`=3, `Math Solver`=14, `Mathematical Analyst`=8, `Programming Expert`=18

## Per-Task Graph and Outcome

| task | ok | true | pred | graph | roles | edges |
|---|---:|---:|---:|---|---|---|
| task_204 | Y | C | C | 2n/1e | Programming Expert -> Math Solver | 0->1 |
| task_61 | Y | D | D | 2n/1e | Programming Expert -> Math Solver | 0->1 |
| task_152 | N | C | E | 3n/2e | Programming Expert -> Programming Expert -> Inspector | 0->1;1->2 |
| task_199 | N | A | C | 2n/1e | Programming Expert -> Math Solver | 0->1 |
| task_172 | N | E | C | 2n/1e | Math Solver -> Programming Expert | 0->1 |
| task_177 | Y | D | D | 2n/1e | Programming Expert -> Inspector | 0->1 |
| task_95 | Y | A | A | 3n/2e | Math Solver -> Mathematical Analyst -> Mathematical Analyst | 0->1;0->2 |
| task_60 | Y | E | E | 2n/1e | Programming Expert -> Math Solver | 0->1 |
| task_138 | Y | C | C | 2n/1e | Programming Expert -> Inspector | 0->1 |
| task_181 | Y | A | A | 2n/1e | Programming Expert -> Programming Expert | 0->1 |
| task_253 | Y | A | A | 3n/2e | Math Solver -> Mathematical Analyst -> Mathematical Analyst | 0->1;1->2 |
| task_222 | Y | D | D | 2n/1e | Programming Expert -> Math Solver | 0->1 |
| task_21 | Y | A | A | 2n/1e | Programming Expert -> Math Solver | 0->1 |
| task_111 | Y | D | D | 2n/1e | Math Solver -> Programming Expert | 0->1 |
| task_211 | Y | A | A | 2n/1e | Programming Expert -> Mathematical Analyst | 0->1 |
| task_15 | Y | A | A | 2n/1e | Programming Expert -> Math Solver | 0->1 |
| task_66 | Y | C | C | 2n/1e | Math Solver -> Mathematical Analyst | 0->1 |
| task_132 | Y | B | B | 2n/1e | Mathematical Analyst -> Math Solver | 0->1 |
| task_105 | Y | B | B | 2n/1e | Math Solver -> Mathematical Analyst | 0->1 |
| task_252 | Y | B | B | 2n/1e | Programming Expert -> Programming Expert | 0->1 |

## Incorrect Cases

### task_152 true=C pred=E

Question: If Jill needed to buy 10 bottles of soda for a party in which 8 people attended, how many bottles of soda will she need to buy for a party in which 12 people are attending? Choices: A)6 B)8 C)10 D)12 E)14

Generated graph: roles `Programming Expert -> Programming Expert -> Inspector`, edges `0->1; 1->2`

Final decision excerpt: The answer is E.

- Agent 0 `Programming Expert` preds []: the answer is 15.0
- Agent 1 `Programming Expert` preds [0]: the answer is 15
- Agent 2 `Inspector` preds [1]: The answer is not present in the provided choices.

### task_199 true=A pred=C

Question: Three friends Alan, Roger and Peter attempt to answer a question on an exam. Alan randomly guesses the answer, giving him a 1/5 probability of guessing correctly. Roger cheats by looking at the paper of the student in front of him, giving him a 2/3 probability of answering correctly. And Peter dutifully performs the calculations, then marks the answer, giving him a 5/6 probability of a correct answer. What is the ...

Generated graph: roles `Programming Expert -> Math Solver`, edges `0->1`

Final decision excerpt: The answer is C

- Agent 0 `Programming Expert` preds []: the answer is 0.23333333333333336
- Agent 1 `Math Solver` preds [0]: The answer is E

### task_172 true=E pred=C

Question: Allen starts from X, goes to Y. At the same time Bob starts from Y and goes towards X. Once Allen reaches Y he changes his direction and returns to X. Once Bob reaches X, he changes his direction and returns to Y. Throughout Allen travels at 54 kmph and Bob travels at 78kmph. By the time they meet for the second time, Bob covers 48 km more than Allen. Find the distance between X and Y. Choices: A)144km B)72 km C)1...

Generated graph: roles `Math Solver -> Programming Expert`, edges `0->1`

Final decision excerpt: The answer is C

- Agent 0 `Math Solver` preds []: The answer is C.
- Agent 1 `Programming Expert` preds [0]: the answer is 132.0

## Files

- Full JSONL with agent outputs: `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/aqua/aqua_sync20_eval20_results.jsonl`
- CSV task summary: `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/aqua/run_logs/aqua_sync20_eval20_breakdown.csv`
- Cold-start log: `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/aqua/run_logs/aqua_sync20_cold_start.log`
- Train/fine-tune log: `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/aqua/run_logs/aqua_sync20_finetune.log`
- Eval log: `/Users/chencheng/Downloads/论文/ARG-Designer-main/experiment/aqua/run_logs/aqua_sync20_eval20.log`
