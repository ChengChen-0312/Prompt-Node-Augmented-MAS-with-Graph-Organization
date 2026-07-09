# R445 External Audit Payload: paper_claim_audit

This payload is prepared for a fresh external reviewer. It has not been submitted by Codex.

## Audit Prompt

# R441 External Paper Claim Audit Prompt

Audit every number and comparison in the paper against the raw/result JSON files. Do not use executor summaries as evidence except as file lists.

## Files To Inspect

- `paper/main.tex`
- `paper/sections/0_abstract.tex`
- `paper/sections/1_introduction.tex`
- `paper/sections/2_related_work.tex`
- `paper/sections/3_method.tex`
- `paper/sections/4_experimental_setup.tex`
- `paper/sections/5_results.tex`
- `paper/sections/6_case_studies.tex`
- `paper/sections/7_limitations.tex`
- `paper/sections/8_conclusion.tex`
- `paper/references.bib`
- `experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json`
- `experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json`
- `experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json`
- `experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json`
- `experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json`
- `experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json`
- `experiment/mmlu/res_logs/mmlu_r440_paper_claim_number_static_audit_summary.json`

## Required Output

Return PASS/WARN/FAIL with file:line evidence and concrete fixes.

## Attached File Contents

### `paper/main.tex`

```tex
\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{booktabs}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{xcolor}
\input{math_commands}

\title{PromptNode-Augmented Multi-Agent Graphs for Robust Reasoning}
\author{Anonymous Authors}
\date{}

\begin{document}
\maketitle

\begin{abstract}
\input{sections/0_abstract}
\end{abstract}

\input{sections/1_introduction}
\input{sections/2_related_work}
\input{sections/3_method}
\input{sections/4_experimental_setup}
\input{sections/5_results}
\input{sections/6_case_studies}
\input{sections/7_limitations}
\input{sections/8_conclusion}

\bibliographystyle{plain}
\bibliography{references}

\end{document}

```

### `paper/sections/0_abstract.tex`

```tex
Large-language-model multi-agent systems are highly sensitive to how agents communicate, which evidence they may reuse, and when a tentative answer should be forwarded. We introduce PromptNode-Augmented multi-agent graphs, a graph-organization method that treats virtual functional nodes as first-class elements rather than post-hoc answer patches. PromptNodes carry typed identities such as memory, instruction verification, tool-resource checking, and adversarial verification; PromptEdges specify read, write, and forward permissions; and lifecycle actions update, compress, prune, merge, or upgrade graph state during reasoning. Using ARG-Designer as the main baseline and preserving its model setting as closely as possible, the current evidence supports a scoped improvement claim. On the audited AQuA tail split, the PromptNode graph obtains 31/31 against ARG's 28/31. On MMLU STEM transfer, it obtains 95/97 against 88/97. A targeted DefinitionChallenge non-STEM run improves 21/24 to 22/24 with fix/harm/wrong-forward 1/0/0, while a broader mixed non-STEM split remains no-harm rather than positive at 41/48 versus 41/48. These results suggest that typed virtual nodes and permissioned prompt edges can improve robust reasoning when claims are bounded by label audits, cost accounting, and transfer diagnostics.

```

### `paper/sections/1_introduction.tex`

```tex
\section{Introduction}
\label{sec:introduction}

LLM-based multi-agent systems turn reasoning into a communication problem. A correct intermediate insight can be lost if it is sent to the wrong agent, repeated too late, or merged with a higher-confidence but wrong consensus. Conversely, an erroneous argument can spread through the graph and dominate the final answer. This makes graph organization a first-order design choice rather than an implementation detail.

ARG-Designer is a strong baseline because it treats multi-agent design as graph generation, allowing the system to learn which ordinary agents and edges should be present. Our work asks a different question: whether the graph should also contain virtual functional nodes that do not act like ordinary solvers, but instead manage instruction binding, memory transfer, verification, option elimination, contradiction checks, and answer forwarding. The user-facing intuition is simple. A PromptNode is not a late answer patch. It is a typed graph element with permissions and lifecycle state.

We propose PromptNode-Augmented MAS, where virtual nodes and PromptEdges are inserted into the communication graph before aggregation. A PromptNode has an identity, a structured state, and allowed lifecycle actions. A PromptEdge controls what a downstream node may read, what it may write, and whether its candidate answer can be forwarded. This design makes prompt content part of graph organization: a prompt can live inside a node, but it can also appear as an edge contract that constrains how evidence moves.

The current paper supports four bounded contributions:
\begin{enumerate}
    \item We define PromptNodes and PromptEdges as first-class graph elements for MAS reasoning, including typed identities, read/write/forward permissions, and lifecycle actions.
    \item We show a positive audited result on AQuA tail reasoning under ARG-Designer-matched settings: 31/31 on the audit-clean slice versus 28/31 for ARG.
    \item We show transfer to MMLU STEM with 95/97 versus 88/97 for ARG, while keeping the cost row explicitly marked as a probe estimate rather than original exact accounting.
    \item We report a bounded non-STEM picture: a broader mixed split is no-harm at 41/48 versus 41/48, while a targeted DefinitionChallenge split improves 21/24 to 22/24 with no harms.
\end{enumerate}

These claims are intentionally narrower than a generic claim that virtual nodes always improve multi-agent reasoning. The evidence so far supports graph-organization gains on audited mathematical and STEM reasoning, plus a targeted concept-definition transfer result. It does not support a broad non-STEM improvement claim. This boundary is important for a credible SCI-Q2 submission: the method must be presented as a reproducible graph-policy design with explicit failure modes, not as a dataset-specific trick.

```

### `paper/sections/2_related_work.tex`

```tex
\section{Related Work}
\label{sec:related}

\paragraph{Automated multi-agent graph design.}
Recent MAS research increasingly treats communication topology as a learnable object. ARG-Designer formulates multi-agent topology construction as autoregressive graph generation and is therefore the closest baseline for this paper \cite{li2026argdesigner}. GoAgent moves from node-centric topology generation to group-level communication units \cite{chen2026goagent}, while Graph-of-Agents selects and connects agents through graph-based message passing and pooling \cite{yun2026goa}. MAS2 studies a recursive self-generating, self-configuring, and self-rectifying MAS paradigm \cite{wang2026mas2}. PromptNode-Augmented MAS differs in the unit of graph design: instead of only adding, deleting, or connecting ordinary solver agents, it inserts typed virtual functional nodes and permissioned PromptEdges into the graph.

\paragraph{Communication pruning, cost, and robustness.}
Another line of work improves MAS efficiency by removing redundant or harmful communication. AgentDropout dynamically eliminates agents and communication edges for token-efficient collaboration \cite{wang2025agentdropout}. AgentPrune prunes redundant messages in the spatial-temporal communication graph and reports large cost reductions in LLM-based MAS settings \cite{zhang2025agentprune}. EIB-Learner analyzes information propagation effects and balances error suppression with useful insight preservation through topology design \cite{shen2025eiblearner}. These methods motivate our cost and no-harm reporting. Our method is complementary: it can prune candidate forwards, but its central operation is to add structured verifier, memory, option-binding, and conflict-resolution nodes that make forwarding decisions auditable.

\paragraph{Graph prompts and prompt-as-structure.}
Graph prompt learning provides a broader view of prompts as structural objects rather than only text prefixes. ProG organizes graph prompt methods and benchmarks prompts-as-graphs and prompts-as-tokens \cite{zi2024prog}. Our setting is different because the graph is an LLM-agent communication graph rather than a graph neural network input. Still, the distinction is useful: a PromptNode can hold prompt content, and a PromptEdge can also carry a prompt-like contract that controls read, write, and forward permissions.

\paragraph{Positioning.}
The common thread across these works is that MAS performance depends on communication structure. The gap addressed here is the lack of first-class virtual functional elements inside the graph. PromptNodes are designed to expose where verification, memory transfer, contradiction detection, and answer forwarding happen. This is why our experiments report not only accuracy, but also fix/harm, wrong-forward decisions, lifecycle traces, label audits, and cost boundaries.

```

### `paper/sections/3_method.tex`

```tex
\section{PromptNode-Augmented Multi-Agent Graphs}
\label{sec:method}

We model a multi-agent reasoning workflow as a directed communication graph whose nodes may be ordinary agents, tools, memory stores, verifiers, or typed virtual PromptNodes. A PromptNode is not a post-hoc answer patch. It is a first-class graph element with an identity, read/write permissions, a forwarding contract, and lifecycle actions. In our implementation, PromptNode identities include Memory, Instruction-Verifier, Tool-Resource, Verifier, and Agent-like roles. PromptEdges carry explicit read, write, and forward constraints: they determine what evidence a downstream node may consume, what state may be written, and whether an answer label may be forwarded to the final aggregator.

The graph policy follows a two-stage organization. First, diagnostic PromptNodes write structured evidence such as the operative instruction, option binding, definition anchors, adversarial checks, contradictions, confidence, and local memory summaries. Second, a conservative gate decides whether the candidate answer should be forwarded or pruned. The gate is trained or fixed only over graph-visible features, never over hidden labels, task identifiers, or post-hoc correctness. Lifecycle events are recorded as update, compress, prune, merge, and upgrade actions; R419 replays 121 lifecycle events from the fresh R413 DefinitionChallenge run.

For STEM tasks, PromptNodes instantiate InstructionVerifierPN, ToolResourcePN, OptionVerifierPN, and SafetyGatePN. For non-mathematical concept-definition tasks, the DefinitionChallenge path uses InstructionAmbiguityVerifierPN, ConceptDefinitionAnchorPN, OptionSemanticConsistencyVerifierPN, AdversarialVerifierPN, ContradictionDetectorPN, and ConsensusConflictResolverPN. This separation is deliberate: the method is graph organization, while the node library is task-family specific.

```

### `paper/sections/4_experimental_setup.tex`

```tex
\section{Experimental Setup}
\label{sec:setup}

We use ARG-Designer as the main baseline and preserve its model setting as closely as possible. All API-based fresh runs in the current evidence set use \texttt{gpt-4o-2024-08-06}. The main evaluated slices are: audited AQuA tail34, MMLU STEM transfer, mixed MMLU non-STEM transfer, and a fresh DefinitionChallenge subset over logical fallacies, moral disputes, and philosophy. For AQuA, known noisy items are reported through official and audit-clean columns rather than silently rewritten. For MMLU, audited label issues are excluded or reported in appendix-style sensitivity analyses.

Metrics are accuracy, fix/harm, wrong-forward count, and cost. Cost rows are sourced from direct API summaries when available. The MMLU STEM cost in the current draft is a probe-estimated cost from R424/R425, not exact original R306 accounting. All paper-facing claims remain provisional because the external integrity audit is pending.

```

### `paper/sections/5_results.tex`

```tex
\section{Results}
\label{sec:results}

\input{tables/main_results}
\input{tables/cost_results}

\paragraph{AQuA audited tail.}
On the audit-clean AQuA tail31 slice, ARG obtains 28/31 while the PromptNode graph policy obtains 31/31. Under the conservative boundary that also removes task 114, ARG obtains 28/30 and the PromptNode variant obtains 30/30. These results support a scoped AQuA improvement claim, not a claim about all AQuA variants or noisy labels.

\paragraph{MMLU STEM transfer.}
On the MMLU STEM main97 slice, the PromptNode stack obtains 95/97 compared with 88/97 for ARG, with fix/harm 7/0 in the evidence table. The draft cost row is based on a 12-task cost probe: R425 estimates a combined main97 cost of 0.676454 for ARG direct plus PromptNode-stack style calls. This cost is marked as a probe estimate and must not be described as exact R306 accounting.

\paragraph{Non-STEM transfer.}
The broader mixed non-STEM result supports only a no-harm boundary: R396 reports ARG 41/48 and the retrained hybrid 41/48, with no harms but no positive delta. A targeted fresh DefinitionChallenge run gives a narrower positive result: R413/R414 reports ARG 21/24 versus DefinitionChallenge 22/24, with fix/harm/wrong-forward 1/0/0. The raw candidate pool alone is 21/24, so the improvement comes from graph selection rather than from a stronger plain requery candidate pool.

\paragraph{Controls and limitations of evidence.}
Plain requery is not enough to explain the positive targeted result: R316 plain requery on non-STEM40 has the same 37/40 accuracy as ARG and fix/harm 1/1. However, this does not yet establish broad transfer. The DefinitionChallenge result is a targeted nonmath result, the lifecycle trace is replayed from R413 outputs, and the external integrity audit is pending.

```

### `paper/sections/6_case_studies.tex`

```tex
\section{Mechanism Case Studies}
\label{sec:cases}

R417 extracts three reproducible mechanism cases. In \texttt{MMLU-nonstem-moral\_disputes\_test-14}, ARG predicts A, while the DefinitionChallenge graph forwards C and matches the dataset label; this is the single fresh fix in R413. The active elements are ConceptDefinitionAnchorPN, AdversarialVerifierPN, OptionBindingPromptEdge, and ConsensusConflictResolverPN.

In \texttt{MMLU-nonstem-logical\_fallacies\_test-12}, the candidate would have changed an already correct ARG answer. The gate prunes the candidate, preserving the final answer. This case should be described carefully: the row also exposes parser and contract fragility, so it is a safety-prune case rather than a pure semantic-verifier proof.

At the aggregate level, R413 shows that graph selection matters: ARG is 21/24, the candidate pool is also 21/24, and the gated graph is 22/24. The trace replay in R419 records 121 lifecycle events, including 11 forward decisions, 13 prune events, and one upgrade event for the repair case.

```

### `paper/sections/7_limitations.tex`

```tex
\section{Limitations}
\label{sec:limitations}

The current evidence supports a narrowed paper, not a fully ready for submission claim. First, the broad mixed non-STEM setting remains no-harm rather than positive. Second, the MMLU STEM cost is probe-estimated, not exact original R306 accounting. Third, R419 lifecycle traces are replay artifacts from R413 outputs, not independently instrumented runtime logs. Fourth, the external integrity audit is pending, so all draft claims must remain provisional.

These limitations shape the paper framing. The supported core is that typed PromptNodes and PromptEdges improve audited AQuA and MMLU STEM under ARG-Designer-matched settings, while targeted DefinitionChallenge graph selection provides a fresh nonmath positive result. We do not generalize the targeted nonmath result to all non-STEM multiple-choice tasks.

```

### `paper/sections/8_conclusion.tex`

```tex
\section{Conclusion}
\label{sec:conclusion}

We presented PromptNode-Augmented MAS, a way to extend ARG-style multi-agent graphs with typed virtual nodes and permissioned PromptEdges. The strongest current evidence is scoped but useful: audited AQuA tail accuracy improves from 28/31 to 31/31, MMLU STEM improves from 88/97 to 95/97, and a targeted DefinitionChallenge split improves from 21/24 to 22/24 without harms. The broader mixed non-STEM split remains a no-harm result, which keeps the paper's claim boundary honest.

The next technical step is to convert the current evidence into a fully audited manuscript: citation-checked related work, externally reviewed experiment integrity, exact or clearly estimated cost accounting, and larger non-STEM transfer before making any broad generalization. Within that boundary, PromptNodes offer a concrete path for making MAS graph policies more interpretable: every repair, prune, merge, or forward decision can be tied to a graph element rather than hidden inside an unstructured prompt.

```

### `paper/references.bib`

```bib
% R436 source: https://arxiv.org/bibtex/2507.18224
% R436 audit_status: skeleton_needs_citation_audit
@misc{li2026argdesigner,
      title={Assemble Your Crew: Automatic Multi-agent Communication Topology Design via Autoregressive Graph Generation}, 
      author={Shiyuan Li and Yixin Liu and Qingsong Wen and Chengqi Zhang and Shirui Pan},
      year={2025},
      eprint={2507.18224},
      archivePrefix={arXiv},
      primaryClass={cs.MA},
      url={https://arxiv.org/abs/2507.18224}, 
}

% R436 source: https://aclanthology.org/2025.acl-long.1170.bib
% R436 audit_status: skeleton_needs_citation_audit
@inproceedings{wang2025agentdropout,
    title = "{A}gent{D}ropout: Dynamic Agent Elimination for Token-Efficient and High-Performance {LLM}-Based Multi-Agent Collaboration",
    author = "Wang, Zhexuan  and
      Wang, Yutong  and
      Liu, Xuebo  and
      Ding, Liang  and
      Zhang, Miao  and
      Liu, Jie  and
      Zhang, Min",
    editor = "Che, Wanxiang  and
      Nabende, Joyce  and
      Shutova, Ekaterina  and
      Pilehvar, Mohammad Taher",
    booktitle = "Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)",
    month = jul,
    year = "2025",
    address = "Vienna, Austria",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2025.acl-long.1170/",
    doi = "10.18653/v1/2025.acl-long.1170",
    pages = "24013--24035",
    ISBN = "979-8-89176-251-0"
}

% R436 source: https://aclanthology.org/2025.emnlp-main.623.bib
% R436 audit_status: skeleton_needs_citation_audit
@inproceedings{shen2025eiblearner,
    title = "Understanding the Information Propagation Effects of Communication Topologies in {LLM}-based Multi-Agent Systems",
    author = "Shen, Xu  and
      Liu, Yixin  and
      Dai, Yiwei  and
      Wang, Yili  and
      Miao, Rui  and
      Tan, Yue  and
      Pan, Shirui  and
      Wang, Xin",
    editor = "Christodoulopoulos, Christos  and
      Chakraborty, Tanmoy  and
      Rose, Carolyn  and
      Peng, Violet",
    booktitle = "Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing",
    month = nov,
    year = "2025",
    address = "Suzhou, China",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2025.emnlp-main.623/",
    doi = "10.18653/v1/2025.emnlp-main.623",
    pages = "12347--12361",
    ISBN = "979-8-89176-332-6"
}

% R436 source: https://dblp.org/rec/conf/iclr/ZhangYLYWWCY025.bib
% R436 audit_status: skeleton_needs_citation_audit
@inproceedings{zhang2025agentprune,
  author       = {Guibin Zhang and
                  Yanwei Yue and
                  Zhixun Li and
                  Sukwon Yun and
                  Guancheng Wan and
                  Kun Wang and
                  Dawei Cheng and
                  Jeffrey Xu Yu and
                  Tianlong Chen},
  title        = {Cut the Crap: An Economical Communication Pipeline for LLM-based Multi-Agent
                  Systems},
  booktitle    = {The Thirteenth International Conference on Learning Representations,
                  {ICLR} 2025, Singapore, April 24-28, 2025},
  publisher    = {OpenReview.net},
  year         = {2025},
  url          = {https://openreview.net/forum?id=LkzuPorQ5L},
  timestamp    = {Mon, 18 Aug 2025 14:13:39 +0200},
  biburl       = {https://dblp.org/rec/conf/iclr/ZhangYLYWWCY025.bib},
  bibsource    = {dblp computer science bibliography, https://dblp.org}
}

% R436 source: https://arxiv.org/bibtex/2604.17148
% R436 audit_status: skeleton_needs_citation_audit
@misc{yun2026goa,
      title={Graph-of-Agents: A Graph-based Framework for Multi-Agent LLM Collaboration}, 
      author={Sukwon Yun and Jie Peng and Pingzhi Li and Wendong Fan and Jie Chen and James Zou and Guohao Li and Tianlong Chen},
      year={2026},
      eprint={2604.17148},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2604.17148}, 
}

% R436 source: https://arxiv.org/bibtex/2509.24323
% R436 audit_status: skeleton_needs_citation_audit
@misc{wang2026mas2,
      title={MAS$^2$: Self-Generative, Self-Configuring, Self-Rectifying Multi-Agent Systems}, 
      author={Kun Wang and Guibin Zhang and ManKit Ye and Xinyu Deng and Dongxia Wang and Xiaobin Hu and Jinyang Guo and Yang Liu and Yufei Guo},
      year={2025},
      eprint={2509.24323},
      archivePrefix={arXiv},
      primaryClass={cs.MA},
      url={https://arxiv.org/abs/2509.24323}, 
}

% R436 source: https://arxiv.org/bibtex/2406.05346
% R436 audit_status: skeleton_needs_citation_audit
@misc{zi2024prog,
      title={ProG: A Graph Prompt Learning Benchmark}, 
      author={Chenyi Zi and Haihong Zhao and Xiangguo Sun and Yiqing Lin and Hong Cheng and Jia Li},
      year={2024},
      eprint={2406.05346},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/2406.05346}, 
}

% R436 source: https://arxiv.org/bibtex/2603.19677
% R436 audit_status: skeleton_needs_citation_audit
@misc{chen2026goagent,
      title={GoAgent: Group-of-Agents Communication Topology Generation for LLM-based Multi-Agent Systems}, 
      author={Hongjiang Chen and Xin Zheng and Yixin Liu and Pengfei Jiao and Shiyuan Li and Huan Liu and Zhidong Zhao and Ziqi Xu and Ibrahim Khalil and Shirui Pan},
      year={2026},
      eprint={2603.19677},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/2603.19677}, 
}

```

### `experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json`

```json
{
  "run_id": "R271",
  "title": "Tail34 final official/audit-clean claim table",
  "claim_boundary": "paper_table_generation_only_no_new_api",
  "variants": {
    "ARG": {
      "official": "28/34",
      "audit_clean_exclude_59_139_228": "28/31",
      "correct_task114": "29/31",
      "exclude_task114": "28/30",
      "cost": 0.93285,
      "claim_role": "baseline"
    },
    "R065": {
      "official": "31/34",
      "audit_clean_exclude_59_139_228": "31/31",
      "correct_task114": "30/31",
      "exclude_task114": "30/30",
      "cost": 5.050805,
      "claim_role": "highest official replay score, noisy task114 risk"
    },
    "R068": {
      "official": "31/34",
      "audit_clean_exclude_59_139_228": "31/31",
      "correct_task114": "30/31",
      "exclude_task114": "30/30",
      "cost": 3.597409,
      "claim_role": "cost-reduced replay retaining R065 score"
    },
    "R095": {
      "official": "30/34",
      "audit_clean_exclude_59_139_228": "30/31",
      "correct_task114": "31/31",
      "exclude_task114": "30/30",
      "cost": 5.050805,
      "claim_role": "safety-gated replay, not cost-reduced"
    },
    "R267": {
      "official": "30/34",
      "audit_clean_exclude_59_139_228": "30/31",
      "correct_task114": "31/31",
      "exclude_task114": "30/30",
      "cost": 3.597409,
      "claim_role": "cost-reduced plus safety-gated replay"
    }
  },
  "recommended_main_text_claim": "official_plus_audit_clean_scope_limited",
  "recommended_wording": "Report official and audit-clean columns side by side. Use R065/R068 for the official improvement signal and R095/R267 for the safety/audit-clean interpretation. Do not claim broad transfer superiority."
}

```

### `experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json`

```json
{
  "run_id": "R321",
  "title": "Paper evidence table and selector-training gate",
  "claim_boundary": "R321 translates the current results into paper-facing tables and freezes the next training gate. It permits a selector-training preflight, but does not permit training execution yet.",
  "no_api": true,
  "broad_api": false,
  "paper_main_results": [
    {
      "slice": "AQuA_audit_clean_tail31",
      "baseline": "28/31",
      "promptnode": "31/31",
      "delta_correct": 3,
      "fix_harm": "-",
      "paper_claim": "positive_clean_improvement",
      "note": "Audit-clean after excluding task_59/task_139/task_228."
    },
    {
      "slice": "AQuA_conservative_remove_114_tail30",
      "baseline": "28/30",
      "promptnode": "30/30",
      "delta_correct": 2,
      "fix_harm": "-",
      "paper_claim": "positive_under_boundary_label_removal",
      "note": "Sensitivity check if task_114 is treated as a boundary label case."
    },
    {
      "slice": "MMLU_STEM_main97",
      "baseline": "88/97",
      "promptnode": "95/97",
      "delta_correct": 7,
      "fix_harm": "7/0",
      "paper_claim": "positive_with_completed_controls",
      "note": "R306 keeps +7 correct over ARG after negative controls and ablations."
    },
    {
      "slice": "MMLU_nonSTEM40_safety_replay",
      "baseline": "37/40",
      "promptnode": "37/40",
      "delta_correct": 0,
      "fix_harm": "0/0",
      "paper_claim": "no_harm_boundary_only",
      "note": "Warning-only semantic nodes cannot be claimed as non-STEM improvement."
    },
    {
      "slice": "MMLU_nonSTEM40_raw_warning_override",
      "baseline": "37/40",
      "promptnode": "34/40",
      "delta_correct": -3,
      "fix_harm": "0/3",
      "paper_claim": "negative_transfer_limitation",
      "note": "This row belongs in limitations or appendix, not as a main positive result."
    }
  ],
  "paper_claim_draft": "PromptNode/PromptEdge graph organization improves audited AQuA tail and MMLU STEM while preserving a no-harm boundary on non-STEM after lifecycle safety replay.",
  "paper_claim_forbidden": [
    "Do not claim universal improvement across all multi-choice tasks.",
    "Do not present warning-only non-STEM nodes as answer-improving nodes.",
    "Do not hide the raw non-STEM negative transfer row."
  ],
  "ablation_summary": {
    "completed_count": 10,
    "priority_pending": [],
    "key_controls": [
      "remove_safety_gate",
      "remove_lifecycle_prune",
      "remove_promptedge_text",
      "remove_symbolic_verifier_family",
      "cost_matched_plain_requery"
    ]
  },
  "selector_training_gate": {
    "preflight_authorized": true,
    "execute_training_authorized": false,
    "reason_execution_blocked": "A prospective train/dev/test split and leakage check must be frozen before selector training can run.",
    "allowed_training_target": "Learn a graph-policy selector for PromptNode type, PromptEdge read/write/forward permission, and lifecycle action; do not train a direct answer predictor.",
    "required_features": [
      "arg_node_state_features",
      "promptnode_type_features",
      "promptedge_text_features",
      "read_write_forward_permission_features",
      "lifecycle_action_features",
      "budget_and_cost_features",
      "agreement_conflict_features"
    ],
    "forbidden_training_signals": [
      "ground_truth_answer_text",
      "label_audited_noisy_items",
      "warning_only_promptnode_override",
      "dataset_specific_task_id_rules",
      "posthoc_wrong_item_memorization"
    ],
    "minimum_success_criteria_for_execution": {
      "heldout_positive_slice": "Beat ARG on at least one clean held-out slice.",
      "transfer_boundary": "No significant harm on a non-STEM or non-formula multiple-choice split.",
      "cost_boundary": "Do not lose to cost-matched plain requery on the claimed positive slice.",
      "claim_boundary": "Keep broad general PromptNode claim disabled unless transfer becomes positive."
    },
    "current_claim_permissions": {
      "aqua_clean_improvement_allowed": true,
      "mmlu_stem_improvement_allowed": true,
      "mmlu_nonstem_no_harm_allowed": true,
      "mmlu_nonstem_improvement_allowed": false,
      "broad_general_promptnode_claim_allowed": false,
      "training_authorized": false,
      "sci_q2_ready": false
    }
  },
  "next_required_run": "R322_selector_training_preflight",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r321_paper_evidence_table_and_training_gate_report.md"
}

```

### `experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json`

```json
{
  "run_id": "R396",
  "title": "Larger mixed nonmath fresh analysis and goal audit",
  "claim_boundary": "R396 analyzes R395 and performs the five-iteration goal audit for R391-R395. The larger mixed nonmath run supports no-harm transfer, but not positive gain.",
  "no_api": true,
  "broad_api": false,
  "records": 48,
  "arg_correct": 41,
  "hybrid_correct": 41,
  "delta_correct": 0,
  "arg_accuracy": 0.854167,
  "hybrid_accuracy": 0.854167,
  "candidate_label_count": 43,
  "gate_forward_count": 24,
  "fixes": 0,
  "harms": 0,
  "wrong_forward_count": 3,
  "missed_fix_count": 4,
  "candidate_correct_but_blocked_count": 1,
  "fix_task_ids": [],
  "harm_task_ids": [],
  "wrong_forward_task_ids": [
    "MMLU-nonstem-moral_disputes_test-24",
    "MMLU-nonstem-logical_fallacies_test-17",
    "MMLU-nonstem-logical_fallacies_test-18"
  ],
  "missed_fix_task_ids": [
    "MMLU-nonstem-sociology_test-23",
    "MMLU-nonstem-world_religions_test-21",
    "MMLU-nonstem-philosophy_test-25",
    "MMLU-nonstem-business_ethics_test-19"
  ],
  "candidate_correct_but_blocked_task_ids": [
    "MMLU-nonstem-philosophy_test-25"
  ],
  "subject_breakdown": {
    "business_ethics": {
      "records": 6,
      "arg_correct": 5,
      "hybrid_correct": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    },
    "high_school_government_and_politics": {
      "records": 6,
      "arg_correct": 6,
      "hybrid_correct": 6,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    },
    "high_school_world_history": {
      "records": 6,
      "arg_correct": 6,
      "hybrid_correct": 6,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    },
    "logical_fallacies": {
      "records": 6,
      "arg_correct": 4,
      "hybrid_correct": 4,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 2,
      "delta": 0
    },
    "moral_disputes": {
      "records": 6,
      "arg_correct": 5,
      "hybrid_correct": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 1,
      "delta": 0
    },
    "philosophy": {
      "records": 6,
      "arg_correct": 5,
      "hybrid_correct": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    },
    "sociology": {
      "records": 6,
      "arg_correct": 5,
      "hybrid_correct": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    },
    "world_religions": {
      "records": 6,
      "arg_correct": 5,
      "hybrid_correct": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    }
  },
  "candidate_type_counts": {
    "Option": 17,
    "multiple-choice": 7,
    "option": 8,
    "option_binding_promptedge": 9,
    "single": 3,
    "single-choice": 4
  },
  "iterations_since_last_goal_check": [
    "R391",
    "R392",
    "R393",
    "R394",
    "R395"
  ],
  "goal_alignment": {
    "still_aligned_with_sci_q2_goal": true,
    "larger_mixed_no_harm": true,
    "larger_mixed_positive": false,
    "error_taxonomy_required": true,
    "overclaiming_blocked": true
  },
  "claim_permissions": {
    "larger_mixed_no_harm_claim_allowed": true,
    "positive_mixed_nonmath_claim_allowed": false,
    "error_taxonomy_allowed_next": true,
    "api_execution_allowed_now": false,
    "main_paper_claim_allowed": false,
    "sci_q2_ready": false
  },
  "api_cost": 0.26203,
  "prompt_tokens": 21086,
  "completion_tokens": 10440,
  "paper_claim_authorized": false,
  "sci_q2_ready": false,
  "next_required_run": "R397_larger_mixed_error_taxonomy",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_report.md"
}

```

### `experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json`

```json
{
  "run_id": "R414",
  "title": "DefinitionChallenge gate analysis",
  "claim_boundary": "R414 analyzes a fresh targeted nonmath split. It supports only a narrow DefinitionChallenge positive/no-harm claim; it does not support broad nonmath generalization.",
  "no_api": true,
  "broad_api": false,
  "records": 24,
  "arg_correct": 21,
  "hybrid_correct": 22,
  "candidate_correct": 21,
  "delta_correct": 1,
  "candidate_pool_delta": 0,
  "arg_accuracy": 0.875,
  "hybrid_accuracy": 0.916667,
  "candidate_accuracy": 0.875,
  "gate_forward_count": 11,
  "fixes": 1,
  "harms": 0,
  "wrong_forward_count": 0,
  "fix_task_ids": [
    "MMLU-nonstem-moral_disputes_test-14"
  ],
  "harm_task_ids": [],
  "wrong_forward_task_ids": [],
  "candidate_oracle_fix_task_ids": [
    "MMLU-nonstem-moral_disputes_test-14"
  ],
  "candidate_oracle_harm_task_ids": [
    "MMLU-nonstem-logical_fallacies_test-12"
  ],
  "selection_contribution": {
    "gate_improves_over_arg": true,
    "gate_improves_over_candidate_pool": true,
    "candidate_pool_alone_not_better_than_arg": true,
    "pruned_candidate_harms": 1,
    "pruned_candidate_harm_task_ids": [
      "MMLU-nonstem-logical_fallacies_test-12"
    ]
  },
  "subject_breakdown": {
    "logical_fallacies": {
      "records": 8,
      "arg_correct": 7,
      "candidate_correct": 6,
      "hybrid_correct": 7,
      "delta_correct": 0,
      "gate_forward_count": 2,
      "fixes": 0,
      "harms": 0,
      "wrong_forward_count": 0
    },
    "moral_disputes": {
      "records": 8,
      "arg_correct": 6,
      "candidate_correct": 7,
      "hybrid_correct": 7,
      "delta_correct": 1,
      "gate_forward_count": 4,
      "fixes": 1,
      "harms": 0,
      "wrong_forward_count": 0
    },
    "philosophy": {
      "records": 8,
      "arg_correct": 8,
      "candidate_correct": 8,
      "hybrid_correct": 8,
      "delta_correct": 0,
      "gate_forward_count": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward_count": 0
    }
  },
  "gate_block_reason_counts": {
    "low_node_agreement": 13,
    "weak_definition_anchor": 13,
    "adversarial_challenge_failed": 13,
    "small_distractor_margin": 13,
    "option_binding_contract_failed": 13,
    "weak_memory_bridge": 13
  },
  "claim_permissions": {
    "narrow_definition_challenge_claim_allowed": true,
    "broad_nonmath_claim_allowed": false,
    "main_paper_claim_allowed": false,
    "needs_external_integrity_audit": true,
    "sci_q2_ready": false
  },
  "paper_claim_authorized": false,
  "sci_q2_ready": false,
  "next_required_run": "R415_update_claim_matrix_after_nonmath_positive",
  "input_jsonl": "experiment/mmlu/run_logs/mmlu_r413_definition_challenge_gate_api_results.jsonl",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r414_definition_challenge_gate_analysis_report.md"
}

```

### `experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json`

```json
{
  "run_id": "R419",
  "title": "Lifecycle trace replay",
  "claim_boundary": "R419 replays existing R413 outputs into lifecycle events. It supports case-study visualization, not new accuracy claims.",
  "no_api": true,
  "broad_api": false,
  "source_jsonl": "experiment/mmlu/run_logs/mmlu_r413_definition_challenge_gate_api_results.jsonl",
  "source_records": 24,
  "events": 121,
  "event_counts": {
    "PromptEdgeForward": 11,
    "PromptNodeCompress": 24,
    "PromptNodeMerge": 24,
    "PromptNodePrune": 13,
    "PromptNodeUpdate": 24,
    "PromptNodeUpgrade": 1,
    "PromptNodeWrite": 24
  },
  "forwarded_tasks": 11,
  "pruned_tasks": 13,
  "upgrade_task_ids": [
    "MMLU-nonstem-moral_disputes_test-14"
  ],
  "forward_task_ids": [
    "MMLU-nonstem-logical_fallacies_test-13",
    "MMLU-nonstem-logical_fallacies_test-23",
    "MMLU-nonstem-moral_disputes_test-12",
    "MMLU-nonstem-moral_disputes_test-13",
    "MMLU-nonstem-moral_disputes_test-14",
    "MMLU-nonstem-moral_disputes_test-15",
    "MMLU-nonstem-philosophy_test-15",
    "MMLU-nonstem-philosophy_test-16",
    "MMLU-nonstem-philosophy_test-27",
    "MMLU-nonstem-philosophy_test-28",
    "MMLU-nonstem-philosophy_test-29"
  ],
  "prune_task_ids": [
    "MMLU-nonstem-logical_fallacies_test-12",
    "MMLU-nonstem-logical_fallacies_test-14",
    "MMLU-nonstem-logical_fallacies_test-15",
    "MMLU-nonstem-logical_fallacies_test-16",
    "MMLU-nonstem-logical_fallacies_test-24",
    "MMLU-nonstem-logical_fallacies_test-25",
    "MMLU-nonstem-moral_disputes_test-16",
    "MMLU-nonstem-moral_disputes_test-27",
    "MMLU-nonstem-moral_disputes_test-28",
    "MMLU-nonstem-moral_disputes_test-29",
    "MMLU-nonstem-philosophy_test-12",
    "MMLU-nonstem-philosophy_test-13",
    "MMLU-nonstem-philosophy_test-14"
  ],
  "case_study_trace_available": true,
  "paper_claim_authorized": false,
  "sci_q2_ready": false,
  "next_required_run": "R420_paper_asset_table_refresh",
  "trace_jsonl": "experiment/mmlu/run_logs/mmlu_r419_lifecycle_trace_events.jsonl",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r419_lifecycle_trace_replay_report.md"
}

```

### `experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json`

```json
{
  "run_id": "R426",
  "title": "Update cost table with STEM probe and goal audit",
  "claim_boundary": "R426 replaces the missing MMLU STEM cost row with a probe estimate. This improves draft completeness but does not make submission cost evidence exact or audited.",
  "no_api": true,
  "broad_api": false,
  "cost_rows": [
    {
      "id": "AQuA_ARG_baseline",
      "slice": "AQuA_tail34_official",
      "score": "28/34",
      "accuracy": 0.823529,
      "cost": 0.93285,
      "cost_per_task": 0.027437,
      "correct_per_cost": 30.015544,
      "accuracy_per_cost": 0.88281,
      "prompt_tokens": null,
      "completion_tokens": null,
      "fix_harm_wrong": "n/a",
      "source": "experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json",
      "role": "ARG baseline",
      "note": "AQuA replay cost from R271.",
      "cost_evidence": "direct_or_existing_summary"
    },
    {
      "id": "AQuA_R068_cost_reduced",
      "slice": "AQuA_tail34_official",
      "score": "31/34",
      "accuracy": 0.911765,
      "cost": 3.597409,
      "cost_per_task": 0.105806,
      "correct_per_cost": 8.617313,
      "accuracy_per_cost": 0.25345,
      "prompt_tokens": null,
      "completion_tokens": null,
      "fix_harm_wrong": "n/a",
      "source": "experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json",
      "role": "cost-reduced PromptNode replay",
      "note": "Retains R065 official score with lower multi-view cost.",
      "cost_evidence": "direct_or_existing_summary"
    },
    {
      "id": "AQuA_R267_safety_cost",
      "slice": "AQuA_tail34_audit_boundary",
      "score": "31/31",
      "accuracy": 1.0,
      "cost": 3.597409,
      "cost_per_task": 0.116045,
      "correct_per_cost": 8.617313,
      "accuracy_per_cost": 0.277978,
      "prompt_tokens": null,
      "completion_tokens": null,
      "fix_harm_wrong": "n/a",
      "source": "experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json",
      "role": "cost-reduced plus safety-gated replay",
      "note": "Audit-boundary interpretation; not the highest official score.",
      "cost_evidence": "direct_or_existing_summary"
    },
    {
      "id": "MMLU_STEM_R306_probe_estimate",
      "slice": "MMLU_STEM_main97",
      "score": "95/97",
      "accuracy": 0.979381,
      "cost": 0.676454,
      "cost_per_task": 0.006974,
      "correct_per_cost": 140.438226,
      "accuracy_per_cost": 1.447816,
      "prompt_tokens": null,
      "completion_tokens": null,
      "fix_harm_wrong": "2/0/n/a",
      "source": "experiment/mmlu/res_logs/mmlu_r425_analyze_mmlu_stem_cost_probe_summary.json",
      "role": "MMLU STEM positive result with probe-estimated cost",
      "note": "Cost is extrapolated from R424 12-task probe; not exact R306 accounting.",
      "cost_evidence": "probe_estimate_not_exact"
    },
    {
      "id": "MMLU_DefinitionChallenge_R413",
      "slice": "MMLU_definition_challenge_fresh24",
      "score": "22/24",
      "accuracy": 0.916667,
      "cost": 0.220095,
      "cost_per_task": 0.009171,
      "correct_per_cost": 99.956837,
      "accuracy_per_cost": 4.16487,
      "prompt_tokens": 13092,
      "completion_tokens": 10309,
      "fix_harm_wrong": "1/0/0",
      "source": "experiment/mmlu/res_logs/mmlu_r413_definition_challenge_gate_api_execution_summary.json",
      "role": "fresh targeted nonmath PromptNode/PromptEdge gate",
      "note": "Cost includes both ARG direct baseline and DefinitionChallenge candidate calls.",
      "cost_evidence": "direct_or_existing_summary"
    },
    {
      "id": "MMLU_plain_requery_R316",
      "slice": "MMLU_nonSTEM40_plain_requery_control",
      "score": "37/40",
      "accuracy": 0.925,
      "cost": 0.11794,
      "cost_per_task": 0.002949,
      "correct_per_cost": 313.71884,
      "accuracy_per_cost": 7.842971,
      "prompt_tokens": null,
      "completion_tokens": null,
      "fix_harm_wrong": "1/1/n/a",
      "source": "experiment/mmlu/res_logs/mmlu_r316_promptedge_cost_controls_summary.json",
      "role": "cost-matched plain requery control",
      "note": "Approximate half of R316 total API cost, because node-only and plain-requery each made 40 API calls.",
      "cost_evidence": "direct_or_existing_summary"
    }
  ],
  "missing_cost_evidence": [
    "independent_integrity_audit_missing"
  ],
  "cost_table_complete_for_draft": true,
  "cost_table_complete_for_submission": false,
  "iterations_since_last_goal_check": [
    "R422",
    "R423",
    "R424",
    "R425",
    "R426"
  ],
  "goal_alignment": {
    "still_aligned_with_sci_q2_goal": true,
    "arg_designer_remains_main_baseline": true,
    "promptnode_first_class_boundary_preserved": true,
    "mmlu_stem_cost_gap_reduced": true,
    "estimate_not_misrepresented_as_exact": true,
    "external_audit_still_required": true,
    "overclaiming_blocked": true
  },
  "claim_permissions": {
    "cost_table_for_draft_allowed": true,
    "cost_table_for_submission_allowed": false,
    "main_paper_claim_allowed": false,
    "sci_q2_ready": false
  },
  "paper_claim_authorized": false,
  "sci_q2_ready": false,
  "next_required_run": "R427_external_integrity_audit_refresh",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_report.md"
}

```

### `experiment/mmlu/res_logs/mmlu_r440_paper_claim_number_static_audit_summary.json`

```json
{
  "run_id": "R440",
  "title": "Paper claim number static audit",
  "claim_boundary": "R440 checks paper numbers against known result files deterministically. It does not replace a fresh zero-context paper-claim audit.",
  "no_api": true,
  "broad_api": false,
  "claim_count": 20,
  "verified_claims": [
    {
      "id": "aqua_arg_clean",
      "paper_pattern": "28/31",
      "evidence_value": "28/31"
    },
    {
      "id": "aqua_pn_clean",
      "paper_pattern": "31/31",
      "evidence_value": "31/31"
    },
    {
      "id": "aqua_arg_tail30",
      "paper_pattern": "28/30",
      "evidence_value": "28/30"
    },
    {
      "id": "aqua_pn_tail30",
      "paper_pattern": "30/30",
      "evidence_value": "30/30"
    },
    {
      "id": "mmlu_stem_arg",
      "paper_pattern": "88/97",
      "evidence_value": "88/97"
    },
    {
      "id": "mmlu_stem_pn",
      "paper_pattern": "95/97",
      "evidence_value": "95/97"
    },
    {
      "id": "mmlu_stem_fix_harm",
      "paper_pattern": "7/0",
      "evidence_value": "7/0"
    },
    {
      "id": "mmlu_stem_cost",
      "paper_pattern": "0.676454",
      "evidence_value": "0.676454"
    },
    {
      "id": "mixed_arg",
      "paper_pattern": "41/48",
      "evidence_value": "41/48"
    },
    {
      "id": "mixed_hybrid",
      "paper_pattern": "41/48",
      "evidence_value": "41/48"
    },
    {
      "id": "definition_arg",
      "paper_pattern": "21/24",
      "evidence_value": "21/24"
    },
    {
      "id": "definition_hybrid",
      "paper_pattern": "22/24",
      "evidence_value": "22/24"
    },
    {
      "id": "definition_candidate",
      "paper_pattern": "21/24",
      "evidence_value": "21/24"
    },
    {
      "id": "definition_fix_harm_wrong",
      "paper_pattern": "1/0/0",
      "evidence_value": "1/0/0"
    },
    {
      "id": "plain_requery_score",
      "paper_pattern": "37/40",
      "evidence_value": "37/40"
    },
    {
      "id": "plain_requery_fix_harm",
      "paper_pattern": "1/1",
      "evidence_value": "1/1"
    },
    {
      "id": "lifecycle_events",
      "paper_pattern": "121",
      "evidence_value": "121"
    },
    {
      "id": "lifecycle_forward",
      "paper_pattern": "11 forward",
      "evidence_value": "11"
    },
    {
      "id": "lifecycle_prune",
      "paper_pattern": "13 prune",
      "evidence_value": "13"
    },
    {
      "id": "lifecycle_upgrade",
      "paper_pattern": "one upgrade",
      "evidence_value": "1"
    }
  ],
  "mismatches": [],
  "unsupported_claims": [],
  "static_number_audit_pass": true,
  "external_paper_claim_audit_required": true,
  "paper_claim_authorized": false,
  "sci_q2_ready": false,
  "next_required_run": "R441_external_audit_package_refresh",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r440_paper_claim_number_static_audit_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r440_paper_claim_number_static_audit_report.md"
}

```
