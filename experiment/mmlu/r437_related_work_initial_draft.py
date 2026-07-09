from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_REFERENCES_BIB = "paper/references.bib"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r437_related_work_initial_draft_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r437_related_work_initial_draft_report.md"

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
    "paper/sections/2_related_work.tex",
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


def _related_work_text() -> str:
    return r"""\section{Related Work}
\label{sec:related}

\paragraph{Automated multi-agent graph design.}
Recent MAS research increasingly treats communication topology as a learnable object. ARG-Designer formulates multi-agent topology construction as autoregressive graph generation and is therefore the closest baseline for this paper \cite{li2026argdesigner}. GoAgent moves from node-centric topology generation to group-level communication units \cite{chen2026goagent}, while Graph-of-Agents selects and connects agents through graph-based message passing and pooling \cite{yun2026goa}. MAS2 studies a recursive self-generating, self-configuring, and self-rectifying MAS paradigm \cite{wang2026mas2}. PromptNode-Augmented MAS differs in the unit of graph design: instead of only adding, deleting, or connecting ordinary solver agents, it inserts typed virtual functional nodes and permissioned PromptEdges into the graph.

\paragraph{Communication pruning, cost, and robustness.}
Another line of work improves MAS efficiency by removing redundant or harmful communication. AgentDropout dynamically eliminates agents and communication edges for token-efficient collaboration \cite{wang2025agentdropout}. AgentPrune prunes redundant messages in the spatial-temporal communication graph and reports large cost reductions in LLM-based MAS settings \cite{zhang2025agentprune}. EIB-Learner analyzes information propagation effects and balances error suppression with useful insight preservation through topology design \cite{shen2025eiblearner}. These methods motivate our cost and no-harm reporting. Our method is complementary: it can prune candidate forwards, but its central operation is to add structured verifier, memory, option-binding, and conflict-resolution nodes that make forwarding decisions auditable.

\paragraph{Graph prompts and prompt-as-structure.}
Graph prompt learning provides a broader view of prompts as structural objects rather than only text prefixes. ProG organizes graph prompt methods and benchmarks prompts-as-graphs and prompts-as-tokens \cite{zi2024prog}. Our setting is different because the graph is an LLM-agent communication graph rather than a graph neural network input. Still, the distinction is useful: a PromptNode can hold prompt content, and a PromptEdge can also carry a prompt-like contract that controls read, write, and forward permissions.

\paragraph{Positioning.}
The common thread across these works is that MAS performance depends on communication structure. The gap addressed here is the lack of first-class virtual functional elements inside the graph. PromptNodes are designed to expose where verification, memory transfer, contradiction detection, and answer forwarding happen. This is why our experiments report not only accuracy, but also fix/harm, wrong-forward decisions, lifecycle traces, label audits, and cost boundaries.
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
            r"\bibliographystyle{plain}",
            r"\bibliography{references}",
            "",
            r"\end{document}",
            "",
        ]
    )


def _cite_keys(tex: str) -> List[str]:
    keys: List[str] = []
    for match in re.finditer(r"\\cite\{([^}]+)\}", tex):
        keys.extend(key.strip() for key in match.group(1).split(",") if key.strip())
    return sorted(set(keys))


def _bib_keys(references_bib: str) -> Set[str]:
    text = _repo_path(references_bib).read_text(encoding="utf-8")
    return set(re.findall(r"@\w+\{([^,\s]+),", text))


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
    targets = [_repo_path("paper/main.tex"), _repo_path("paper/sections/2_related_work.tex")]
    if not any(path.exists() for path in targets):
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = _repo_path(f"paper-backup-r437-{stamp}")
    shutil.copytree(_repo_path("paper"), backup)
    return str(backup.relative_to(REPO_ROOT))


def run_related_work_draft(
    references_bib: str = DEFAULT_REFERENCES_BIB,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    backup = _maybe_backup_targets()
    related = _related_work_text()
    _write_text("paper/sections/2_related_work.tex", related)
    _write_text("paper/main.tex", _main_tex())
    citation_keys = _cite_keys(related)
    missing = sorted(set(citation_keys) - _bib_keys(references_bib))
    hits = _scan_forbidden(["paper/main.tex", *REFERENCED_SECTIONS])
    summary: Dict[str, Any] = {
        "run_id": "R437",
        "title": "Related work initial draft",
        "claim_boundary": (
            "R437 drafts related work using R436 citation skeleton keys. "
            "It still requires citation-context audit before final manuscript use."
        ),
        "no_api": True,
        "broad_api": False,
        "referenced_sections": REFERENCED_SECTIONS,
        "citation_keys_used": citation_keys,
        "missing_bib_keys": missing,
        "remaining_forbidden_hits": hits,
        "complete_initial_paper_draft": not missing and not hits,
        "citation_context_audit_required_next": True,
        "final_bib_authorized": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "backup_created": backup,
        "next_required_run": "R438_citation_context_static_audit",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R437 Related Work Initial Draft",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Complete initial paper draft: `{summary['complete_initial_paper_draft']}`",
        f"- Citation-context audit required next: `{summary['citation_context_audit_required_next']}`",
        "",
        "## Citation Keys",
        "",
    ]
    rows.extend(f"- `{key}`" for key in summary["citation_keys_used"])
    rows.extend(["", "## Missing Bib Keys", ""])
    if summary["missing_bib_keys"]:
        rows.extend(f"- `{key}`" for key in summary["missing_bib_keys"])
    else:
        rows.append("- none")
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draft initial related work with fetched citation skeleton keys.")
    parser.add_argument("--references_bib", default=DEFAULT_REFERENCES_BIB)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_related_work_draft(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
