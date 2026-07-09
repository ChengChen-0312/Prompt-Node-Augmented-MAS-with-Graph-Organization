from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r434_front_matter_initial_draft_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r434_front_matter_initial_draft_report.md"

FORBIDDEN_PHRASES = [
    "broad nonmath improvement",
    "universal multiple-choice improvement",
    "submission-ready",
    "exact MMLU STEM cost",
    "external audit passed",
]

REFERENCED_SECTIONS = [
    "paper/sections/0_abstract.tex",
    "paper/sections/1_introduction.tex",
    "paper/sections/3_method.tex",
    "paper/sections/4_experimental_setup.tex",
    "paper/sections/5_results.tex",
    "paper/sections/6_case_studies.tex",
    "paper/sections/7_limitations.tex",
    "paper/sections/8_conclusion.tex",
]


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _abstract_text() -> str:
    return (
        "Large-language-model multi-agent systems are highly sensitive to how agents communicate, "
        "which evidence they may reuse, and when a tentative answer should be forwarded. We introduce "
        "PromptNode-Augmented multi-agent graphs, a graph-organization method that treats virtual "
        "functional nodes as first-class elements rather than post-hoc answer patches. PromptNodes "
        "carry typed identities such as memory, instruction verification, tool-resource checking, "
        "and adversarial verification; PromptEdges specify read, write, and forward permissions; and "
        "lifecycle actions update, compress, prune, merge, or upgrade graph state during reasoning. "
        "Using ARG-Designer as the main baseline and preserving its model setting as closely as "
        "possible, the current evidence supports a scoped improvement claim. On the audited AQuA "
        "tail split, the PromptNode graph obtains 31/31 against ARG's 28/31. On MMLU STEM transfer, "
        "it obtains 95/97 against 88/97. A targeted DefinitionChallenge non-STEM run improves 21/24 "
        "to 22/24 with fix/harm/wrong-forward 1/0/0, while a broader mixed non-STEM split remains "
        "no-harm rather than positive at 41/48 versus 41/48. These results suggest that typed "
        "virtual nodes and permissioned prompt edges can improve robust reasoning when claims are "
        "bounded by label audits, cost accounting, and transfer diagnostics."
    )


def _introduction_text() -> str:
    return r"""\section{Introduction}
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
"""


def _conclusion_text() -> str:
    return r"""\section{Conclusion}
\label{sec:conclusion}

We presented PromptNode-Augmented MAS, a way to extend ARG-style multi-agent graphs with typed virtual nodes and permissioned PromptEdges. The strongest current evidence is scoped but useful: audited AQuA tail accuracy improves from 28/31 to 31/31, MMLU STEM improves from 88/97 to 95/97, and a targeted DefinitionChallenge split improves from 21/24 to 22/24 without harms. The broader mixed non-STEM split remains a no-harm result, which keeps the paper's claim boundary honest.

The next technical step is to convert the current evidence into a fully audited manuscript: citation-checked related work, externally reviewed experiment integrity, exact or clearly estimated cost accounting, and larger non-STEM transfer before making any broad generalization. Within that boundary, PromptNodes offer a concrete path for making MAS graph policies more interpretable: every repair, prune, merge, or forward decision can be tied to a graph element rather than hidden inside an unstructured prompt.
"""


def _main_tex() -> str:
    inputs = []
    for path in REFERENCED_SECTIONS:
        tex_path = Path(path).with_suffix("").as_posix().removeprefix("paper/")
        if path.endswith("0_abstract.tex"):
            inputs.extend([r"\begin{abstract}", rf"\input{{{tex_path}}}", r"\end{abstract}", ""])
        else:
            inputs.append(rf"\input{{{tex_path}}}")
    return "\n".join(
        [
            r"\documentclass[11pt]{article}",
            r"\usepackage[margin=1in]{geometry}",
            r"\usepackage{amsmath,amssymb,amsthm}",
            r"\usepackage{booktabs}",
            r"\usepackage{enumitem}",
            r"\usepackage{hyperref}",
            r"\usepackage{xcolor}",
            r"\input{math_commands}",
            "",
            r"\title{PromptNode-Augmented Multi-Agent Graphs for Robust Reasoning}",
            r"\author{Anonymous Authors}",
            r"\date{}",
            "",
            r"\begin{document}",
            r"\maketitle",
            "",
            *inputs,
            "",
            r"\end{document}",
            "",
        ]
    )


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text))


def _scan_forbidden(paths: List[str]) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for path in paths:
        target = _repo_path(path)
        if not target.exists():
            continue
        for line_no, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
            for phrase in FORBIDDEN_PHRASES:
                if phrase in line:
                    hits.append({"file": path, "line": line_no, "phrase": phrase})
    return hits


def _maybe_backup_targets() -> str | None:
    targets = [
        _repo_path("paper/main.tex"),
        _repo_path("paper/sections/0_abstract.tex"),
        _repo_path("paper/sections/1_introduction.tex"),
        _repo_path("paper/sections/8_conclusion.tex"),
    ]
    if not any(path.exists() for path in targets):
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = _repo_path(f"paper-backup-r434-{stamp}")
    suffix = 1
    while backup.exists():
        backup = _repo_path(f"paper-backup-r434-{stamp}-{suffix}")
        suffix += 1
    shutil.copytree(_repo_path("paper"), backup)
    return str(backup.relative_to(REPO_ROOT))


def build_summary(backup: str | None) -> Dict[str, Any]:
    abstract = _abstract_text()
    hits = _scan_forbidden(["paper/main.tex", *REFERENCED_SECTIONS])
    return {
        "run_id": "R434",
        "title": "Front matter initial draft",
        "claim_boundary": (
            "R434 drafts abstract, introduction, and conclusion from audited local evidence. "
            "Related work remains pending citation audit."
        ),
        "no_api": True,
        "broad_api": False,
        "created_sections": [
            "paper/sections/0_abstract.tex",
            "paper/sections/1_introduction.tex",
            "paper/sections/8_conclusion.tex",
        ],
        "referenced_sections": REFERENCED_SECTIONS,
        "abstract_word_count": _word_count(abstract),
        "related_work_status": "pending_citation_audit",
        "remaining_forbidden_hits": hits,
        "backup_created": backup,
        "complete_paper_draft": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R435_related_work_bibtex_audit_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R434 Front Matter Initial Draft",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Abstract word count: `{summary['abstract_word_count']}`",
        f"- Related work status: `{summary['related_work_status']}`",
        f"- Complete paper draft: `{summary['complete_paper_draft']}`",
        "",
        "## Created Sections",
        "",
    ]
    rows.extend(f"- `{path}`" for path in summary["created_sections"])
    rows.extend(["", "## Remaining Forbidden Hits", ""])
    if summary["remaining_forbidden_hits"]:
        rows.extend(f"- `{hit['file']}:{hit['line']}` `{hit['phrase']}`" for hit in summary["remaining_forbidden_hits"])
    else:
        rows.append("- none")
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_front_matter_draft(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    backup = _maybe_backup_targets()
    _write_text("paper/sections/0_abstract.tex", _abstract_text() + "\n")
    _write_text("paper/sections/1_introduction.tex", _introduction_text())
    _write_text("paper/sections/8_conclusion.tex", _conclusion_text())
    _write_text("paper/main.tex", _main_tex())
    summary = build_summary(backup)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draft safe front matter for the bounded PromptNode paper.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_front_matter_draft(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
