# R445 External Audit Payload: citation_context_audit

This payload is prepared for a fresh external reviewer. It has not been submitted by Codex.

## Audit Prompt

# R441 External Citation Context Audit Prompt

Audit each related-work citation for existence, metadata correctness, and whether the cited paper supports the exact surrounding sentence.

## Files To Inspect

- `paper/references.bib`
- `paper/sections/2_related_work.tex`
- `paper/.aris/citation-audit/r438_static_contexts.json`
- `.aris/verify-papers/r436_citation_metadata.json`

## Required Output

Return PASS/WARN/FAIL with file:line evidence and concrete fixes.

## Attached File Contents

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

### `paper/.aris/citation-audit/r438_static_contexts.json`

```json
[
  {
    "key": "li2026argdesigner",
    "file": "paper/sections/2_related_work.tex",
    "line": 5,
    "context": "Recent MAS research increasingly treats communication topology as a learnable object. ARG-Designer formulates multi-agent topology construction as autoregressive graph generation and is therefore the closest baseline for this paper \\cite{li2026argdesigner}. GoAgent moves from node-centric topology generation to group-level communication units \\cite{chen2026goagent}, while Graph-of-Agents selects and connects agents through graph-based message passing and pooling \\cite{yun2026goa}. MAS2 studies a recursive self-generating, self-configuring, and self-rectifying MAS paradigm \\cite{wang2026mas2}. PromptNode-Augmented MAS differs in the unit of graph design: instead of only adding, deleting, or connecting ordinary solver agents, it inserts typed virtual functional nodes and permissioned PromptEdges into the graph.",
    "status": "static_context_extracted_external_audit_required"
  },
  {
    "key": "chen2026goagent",
    "file": "paper/sections/2_related_work.tex",
    "line": 5,
    "context": "Recent MAS research increasingly treats communication topology as a learnable object. ARG-Designer formulates multi-agent topology construction as autoregressive graph generation and is therefore the closest baseline for this paper \\cite{li2026argdesigner}. GoAgent moves from node-centric topology generation to group-level communication units \\cite{chen2026goagent}, while Graph-of-Agents selects and connects agents through graph-based message passing and pooling \\cite{yun2026goa}. MAS2 studies a recursive self-generating, self-configuring, and self-rectifying MAS paradigm \\cite{wang2026mas2}. PromptNode-Augmented MAS differs in the unit of graph design: instead of only adding, deleting, or connecting ordinary solver agents, it inserts typed virtual functional nodes and permissioned PromptEdges into the graph.",
    "status": "static_context_extracted_external_audit_required"
  },
  {
    "key": "yun2026goa",
    "file": "paper/sections/2_related_work.tex",
    "line": 5,
    "context": "Recent MAS research increasingly treats communication topology as a learnable object. ARG-Designer formulates multi-agent topology construction as autoregressive graph generation and is therefore the closest baseline for this paper \\cite{li2026argdesigner}. GoAgent moves from node-centric topology generation to group-level communication units \\cite{chen2026goagent}, while Graph-of-Agents selects and connects agents through graph-based message passing and pooling \\cite{yun2026goa}. MAS2 studies a recursive self-generating, self-configuring, and self-rectifying MAS paradigm \\cite{wang2026mas2}. PromptNode-Augmented MAS differs in the unit of graph design: instead of only adding, deleting, or connecting ordinary solver agents, it inserts typed virtual functional nodes and permissioned PromptEdges into the graph.",
    "status": "static_context_extracted_external_audit_required"
  },
  {
    "key": "wang2026mas2",
    "file": "paper/sections/2_related_work.tex",
    "line": 5,
    "context": "Recent MAS research increasingly treats communication topology as a learnable object. ARG-Designer formulates multi-agent topology construction as autoregressive graph generation and is therefore the closest baseline for this paper \\cite{li2026argdesigner}. GoAgent moves from node-centric topology generation to group-level communication units \\cite{chen2026goagent}, while Graph-of-Agents selects and connects agents through graph-based message passing and pooling \\cite{yun2026goa}. MAS2 studies a recursive self-generating, self-configuring, and self-rectifying MAS paradigm \\cite{wang2026mas2}. PromptNode-Augmented MAS differs in the unit of graph design: instead of only adding, deleting, or connecting ordinary solver agents, it inserts typed virtual functional nodes and permissioned PromptEdges into the graph.",
    "status": "static_context_extracted_external_audit_required"
  },
  {
    "key": "wang2025agentdropout",
    "file": "paper/sections/2_related_work.tex",
    "line": 8,
    "context": "Another line of work improves MAS efficiency by removing redundant or harmful communication. AgentDropout dynamically eliminates agents and communication edges for token-efficient collaboration \\cite{wang2025agentdropout}. AgentPrune prunes redundant messages in the spatial-temporal communication graph and reports large cost reductions in LLM-based MAS settings \\cite{zhang2025agentprune}. EIB-Learner analyzes information propagation effects and balances error suppression with useful insight preservation through topology design \\cite{shen2025eiblearner}. These methods motivate our cost and no-harm reporting. Our method is complementary: it can prune candidate forwards, but its central operation is to add structured verifier, memory, option-binding, and conflict-resolution nodes that make forwarding decisions auditable.",
    "status": "static_context_extracted_external_audit_required"
  },
  {
    "key": "zhang2025agentprune",
    "file": "paper/sections/2_related_work.tex",
    "line": 8,
    "context": "Another line of work improves MAS efficiency by removing redundant or harmful communication. AgentDropout dynamically eliminates agents and communication edges for token-efficient collaboration \\cite{wang2025agentdropout}. AgentPrune prunes redundant messages in the spatial-temporal communication graph and reports large cost reductions in LLM-based MAS settings \\cite{zhang2025agentprune}. EIB-Learner analyzes information propagation effects and balances error suppression with useful insight preservation through topology design \\cite{shen2025eiblearner}. These methods motivate our cost and no-harm reporting. Our method is complementary: it can prune candidate forwards, but its central operation is to add structured verifier, memory, option-binding, and conflict-resolution nodes that make forwarding decisions auditable.",
    "status": "static_context_extracted_external_audit_required"
  },
  {
    "key": "shen2025eiblearner",
    "file": "paper/sections/2_related_work.tex",
    "line": 8,
    "context": "Another line of work improves MAS efficiency by removing redundant or harmful communication. AgentDropout dynamically eliminates agents and communication edges for token-efficient collaboration \\cite{wang2025agentdropout}. AgentPrune prunes redundant messages in the spatial-temporal communication graph and reports large cost reductions in LLM-based MAS settings \\cite{zhang2025agentprune}. EIB-Learner analyzes information propagation effects and balances error suppression with useful insight preservation through topology design \\cite{shen2025eiblearner}. These methods motivate our cost and no-harm reporting. Our method is complementary: it can prune candidate forwards, but its central operation is to add structured verifier, memory, option-binding, and conflict-resolution nodes that make forwarding decisions auditable.",
    "status": "static_context_extracted_external_audit_required"
  },
  {
    "key": "zi2024prog",
    "file": "paper/sections/2_related_work.tex",
    "line": 11,
    "context": "Graph prompt learning provides a broader view of prompts as structural objects rather than only text prefixes. ProG organizes graph prompt methods and benchmarks prompts-as-graphs and prompts-as-tokens \\cite{zi2024prog}. Our setting is different because the graph is an LLM-agent communication graph rather than a graph neural network input. Still, the distinction is useful: a PromptNode can hold prompt content, and a PromptEdge can also carry a prompt-like contract that controls read, write, and forward permissions.",
    "status": "static_context_extracted_external_audit_required"
  }
]

```

### `.aris/verify-papers/r436_citation_metadata.json`

```json
[
  {
    "id": "arg_designer",
    "bib_key": "li2026argdesigner",
    "title": "Assemble Your Crew: Automatic Multi-agent Communication Topology Design via Autoregressive Graph Generation",
    "source_url": "https://arxiv.org/bibtex/2507.18224",
    "source_type": "arxiv_metadata",
    "arxiv_id": "2507.18224",
    "status": "fetched_needs_citation_audit"
  },
  {
    "id": "agent_dropout",
    "bib_key": "wang2025agentdropout",
    "title": "AgentDropout: Dynamic Agent Elimination for Token-Efficient and High-Performance LLM-Based Multi-Agent Collaboration",
    "source_url": "https://aclanthology.org/2025.acl-long.1170.bib",
    "source_type": "preferred_published_metadata",
    "arxiv_id": "2503.18891",
    "status": "fetched_needs_citation_audit"
  },
  {
    "id": "eib_learner",
    "bib_key": "shen2025eiblearner",
    "title": "Understanding the Information Propagation Effects of Communication Topologies in LLM-based Multi-Agent Systems",
    "source_url": "https://aclanthology.org/2025.emnlp-main.623.bib",
    "source_type": "preferred_published_metadata",
    "arxiv_id": "2505.23352",
    "status": "fetched_needs_citation_audit"
  },
  {
    "id": "agent_prune",
    "bib_key": "zhang2025agentprune",
    "title": "Cut the Crap: An Economical Communication Pipeline for LLM-Based Multi-Agent Systems",
    "source_url": "https://dblp.org/rec/conf/iclr/ZhangYLYWWCY025.bib",
    "source_type": "preferred_published_metadata",
    "arxiv_id": "2410.02506",
    "status": "fetched_needs_citation_audit"
  },
  {
    "id": "goa",
    "bib_key": "yun2026goa",
    "title": "Graph-of-Agents: A Graph-based Framework for Multi-Agent LLM Collaboration",
    "source_url": "https://arxiv.org/bibtex/2604.17148",
    "source_type": "arxiv_metadata",
    "arxiv_id": "2604.17148",
    "status": "fetched_needs_citation_audit"
  },
  {
    "id": "mas2",
    "bib_key": "wang2026mas2",
    "title": "MAS2: Self-Generative, Self-Configuring, Self-Rectifying Multi-Agent Systems",
    "source_url": "https://arxiv.org/bibtex/2509.24323",
    "source_type": "arxiv_metadata",
    "arxiv_id": "2509.24323",
    "status": "fetched_needs_citation_audit"
  },
  {
    "id": "prog",
    "bib_key": "zi2024prog",
    "title": "ProG: A Graph Prompt Learning Benchmark",
    "source_url": "https://arxiv.org/bibtex/2406.05346",
    "source_type": "arxiv_metadata",
    "arxiv_id": "2406.05346",
    "status": "fetched_needs_citation_audit"
  },
  {
    "id": "goagent",
    "bib_key": "chen2026goagent",
    "title": "GoAgent: Group-of-Agents Communication Topology Generation for LLM-based Multi-Agent Systems",
    "source_url": "https://arxiv.org/bibtex/2603.19677",
    "source_type": "arxiv_metadata",
    "arxiv_id": "2603.19677",
    "status": "fetched_needs_citation_audit"
  }
]

```
