from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
PAPER_LIBRARY_ROOT = Path(REPO_ROOT).parent
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_CANDIDATES_JSON = ".aris/verify-papers/candidate_papers.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r435_related_work_bibtex_audit_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r435_related_work_bibtex_audit_preflight_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _write_json(path: str, payload: Any) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _pdf(name: str) -> str | None:
    path = PAPER_LIBRARY_ROOT / name
    return str(path) if path.exists() else None


def candidate_papers() -> List[Dict[str, Any]]:
    return [
        {
            "id": "arg_designer",
            "bib_key": "li2026argdesigner",
            "title": "Assemble Your Crew: Automatic Multi-agent Communication Topology Design via Autoregressive Graph Generation",
            "authors_hint": "Shiyuan Li; Yixin Liu; Qingsong Wen; Chengqi Zhang; Shirui Pan",
            "year_hint": 2026,
            "venue_hint": "AAAI 2026",
            "arxiv_id": "2507.18224",
            "doi": None,
            "url": "https://github.com/Shiy-Li/ARG-Designer",
            "local_pdf": _pdf("AAAI'26 ARG-Designer.pdf"),
            "topic": "ARG-Designer",
            "status": "candidate_unverified",
        },
        {
            "id": "agent_dropout",
            "bib_key": "wang2025agentdropout",
            "title": "AgentDropout: Dynamic Agent Elimination for Token-Efficient and High-Performance LLM-Based Multi-Agent Collaboration",
            "authors_hint": "Zhexuan Wang; Yutong Wang; Xuebo Liu; Liang Ding; Miao Zhang; Jie Liu; Min Zhang",
            "year_hint": 2025,
            "venue_hint": "ACL 2025",
            "arxiv_id": "2503.18891",
            "doi": None,
            "url": "https://aclanthology.org/2025.acl-long.1170/",
            "local_pdf": _pdf("ACL'25 AgentDropout.pdf"),
            "topic": "Agent pruning/dropout",
            "status": "candidate_unverified",
        },
        {
            "id": "eib_learner",
            "bib_key": "shen2025eiblearner",
            "title": "Understanding the Information Propagation Effects of Communication Topologies in LLM-based Multi-Agent Systems",
            "authors_hint": "Xu Shen; Yixin Liu; Yiwei Dai; Yili Wang; Rui Miao; Yue Tan; Shirui Pan; Xin Wang",
            "year_hint": 2025,
            "venue_hint": "EMNLP 2025",
            "arxiv_id": "2505.23352",
            "doi": None,
            "url": "https://aclanthology.org/2025.emnlp-main.623/",
            "local_pdf": _pdf("EMNLP'25 EIB-Learner.pdf"),
            "topic": "MAS topology and information propagation",
            "status": "candidate_unverified",
        },
        {
            "id": "agent_prune",
            "bib_key": "zhang2025agentprune",
            "title": "Cut the Crap: An Economical Communication Pipeline for LLM-Based Multi-Agent Systems",
            "authors_hint": "Guibin Zhang; Yanwei Yue; Zhixun Li; Sukwon Yun; Guancheng Wan; Kun Wang; Dawei Cheng; Jeffrey Xu Yu; Tianlong Chen",
            "year_hint": 2025,
            "venue_hint": "ICLR 2025",
            "arxiv_id": None,
            "doi": None,
            "url": "https://proceedings.iclr.cc/paper_files/paper/2025/file/bbc461518c59a2a8d64e70e2c38c4a0e-Paper-Conference.pdf",
            "local_pdf": _pdf("ICLR'25 AgentPrune.pdf"),
            "topic": "Agent pruning/dropout",
            "status": "candidate_unverified",
        },
        {
            "id": "goa",
            "bib_key": "yun2026goa",
            "title": "Graph-of-Agents: A Graph-based Framework for Multi-Agent LLM Collaboration",
            "authors_hint": "Sukwon Yun; Jie Peng; Pingzhi Li; Wendong Fan; Jie Chen; James Zou; Guohao Li; Tianlong Chen",
            "year_hint": 2026,
            "venue_hint": "ICLR 2026",
            "arxiv_id": "2604.17148",
            "doi": None,
            "url": "https://arxiv.org/abs/2604.17148",
            "local_pdf": _pdf("ICLR'26 GoA.pdf"),
            "topic": "Graph-of-agents",
            "status": "candidate_unverified",
        },
        {
            "id": "mas2",
            "bib_key": "wang2026mas2",
            "title": "MAS2: Self-Generative, Self-Configuring, Self-Rectifying Multi-Agent Systems",
            "authors_hint": "Kun Wang; Guibin Zhang; ManKit Ye; Xinyu Deng; Dongxia Wang; Xiaobin Hu; Jinyang Guo; Yang Liu; Yufei Guo",
            "year_hint": 2026,
            "venue_hint": "ICLR 2026",
            "arxiv_id": None,
            "doi": None,
            "url": None,
            "local_pdf": _pdf("ICLR'26 MAS2.pdf"),
            "topic": "Self-organizing MAS",
            "status": "candidate_unverified",
        },
        {
            "id": "prog",
            "bib_key": "zi2024prog",
            "title": "ProG: A Graph Prompt Learning Benchmark",
            "authors_hint": "Chenyi Zi; Haihong Zhao; Xiangguo Sun; Yiqing Lin; Hong Cheng; Jia Li",
            "year_hint": 2024,
            "venue_hint": "NeurIPS 2024 Datasets and Benchmarks",
            "arxiv_id": "2406.05346",
            "doi": None,
            "url": "https://proceedings.neurips.cc/paper_files/paper/2024/hash/ad3e803a977f4279330c6ab7245937c6-Abstract-Datasets_and_Benchmarks_Track.html",
            "local_pdf": _pdf("NeurIPS-2024-prog-a-graph-prompt-learning-benchmark-Paper-Datasets_and_Benchmarks_Track(1).pdf"),
            "topic": "Graph prompt learning",
            "status": "candidate_unverified",
        },
        {
            "id": "goagent",
            "bib_key": "chen2026goagent",
            "title": "GoAgent: Group-of-Agents Communication Topology Generation for LLM-based Multi-Agent Systems",
            "authors_hint": "Hongjiang Chen; Xin Zheng; Yixin Liu; Pengfei Jiao; Shiyuan Li; Huan Liu; Zhidong Zhao; Ziqi Xu; Ibrahim Khalil; Shirui Pan",
            "year_hint": 2026,
            "venue_hint": "arXiv preprint",
            "arxiv_id": None,
            "doi": None,
            "url": None,
            "local_pdf": _pdf("arXiv'26 GoAgent.pdf"),
            "topic": "Communication topology generation",
            "status": "candidate_unverified",
        },
    ]


def build_preflight() -> Dict[str, Any]:
    candidates = candidate_papers()
    topics = sorted({paper["topic"] for paper in candidates})
    return {
        "run_id": "R435",
        "title": "Related work BibTeX audit preflight",
        "claim_boundary": (
            "R435 writes a candidate-paper manifest for citation verification. "
            "It does not authorize final BibTeX or related-work prose."
        ),
        "no_api": True,
        "broad_api": False,
        "candidate_count": len(candidates),
        "candidate_papers_json": DEFAULT_CANDIDATES_JSON,
        "required_related_work_topics": topics,
        "verify_papers_required_next": True,
        "bibtex_fetch_required_next": True,
        "final_bib_authorized": False,
        "related_work_draft_authorized": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R436_citation_metadata_fetch_and_bib_skeleton",
    }


def render_report(summary: Dict[str, Any], candidates: List[Dict[str, Any]]) -> str:
    rows = [
        "# R435 Related Work BibTeX Audit Preflight",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Candidate manifest: `{summary['candidate_papers_json']}`",
        f"- Candidate count: `{summary['candidate_count']}`",
        f"- Final BibTeX authorized: `{summary['final_bib_authorized']}`",
        "",
        "## Candidate Papers",
        "",
    ]
    rows.extend(
        f"- `{paper['id']}`: {paper['title']} ({paper['venue_hint']}); arXiv=`{paper['arxiv_id']}`"
        for paper in candidates
    )
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_preflight(
    candidate_papers_json: str = DEFAULT_CANDIDATES_JSON,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    candidates = candidate_papers()
    _write_json(candidate_papers_json, candidates)
    summary = build_preflight()
    summary["candidate_papers_json"] = candidate_papers_json
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary, candidates))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build related-work candidate citation manifest.")
    parser.add_argument("--candidate_papers_json", default=DEFAULT_CANDIDATES_JSON)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_preflight(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
