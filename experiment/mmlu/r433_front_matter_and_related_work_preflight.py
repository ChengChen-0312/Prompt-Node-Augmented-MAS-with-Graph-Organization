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


DEFAULT_R431 = "experiment/mmlu/res_logs/mmlu_r431_draft_claim_sanity_check_summary.json"
DEFAULT_R432 = "experiment/mmlu/res_logs/mmlu_r432_paper_main_tex_scaffold_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r433_front_matter_and_related_work_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r433_front_matter_and_related_work_preflight_report.md"

FRONT_MATTER_SECTIONS = [
    "paper/sections/0_abstract.tex",
    "paper/sections/1_introduction.tex",
    "paper/sections/2_related_work.tex",
    "paper/sections/8_conclusion.tex",
]

WEB_SEED_SOURCES = [
    {
        "title": "ARG-Designer",
        "url": "https://github.com/Shiy-Li/ARG-Designer",
        "role": "main baseline; autoregressive graph generation for MAS design",
        "status": "candidate_needs_bibtex_audit",
    },
    {
        "title": "AgentDropout",
        "url": "https://aclanthology.org/2025.acl-long.1170/",
        "role": "dynamic agent/edge elimination and token-efficient MAS topology optimization",
        "status": "candidate_needs_bibtex_audit",
    },
    {
        "title": "EIB-Learner",
        "url": "https://aclanthology.org/2025.emnlp-main.623/",
        "role": "information-propagation topology design for error suppression and insight preservation",
        "status": "candidate_needs_bibtex_audit",
    },
    {
        "title": "AgentPrune",
        "url": "https://proceedings.iclr.cc/paper_files/paper/2025/file/bbc461518c59a2a8d64e70e2c38c4a0e-Paper-Conference.pdf",
        "role": "communication pruning and cost/robustness baseline",
        "status": "candidate_needs_bibtex_audit",
    },
    {
        "title": "Graph-of-Agents",
        "url": "https://arxiv.org/abs/2604.17148",
        "role": "graph-based agent selection, directed message passing, and pooling for LLM collaboration",
        "status": "candidate_needs_bibtex_audit",
    },
    {
        "title": "ProG",
        "url": "https://proceedings.neurips.cc/paper_files/paper/2024/hash/ad3e803a977f4279330c6ab7245937c6-Abstract-Datasets_and_Benchmarks_Track.html",
        "role": "graph prompt learning benchmark; useful for positioning prompts-as-graphs versus PromptEdges",
        "status": "candidate_needs_bibtex_audit",
    },
]


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    target = _repo_path(path)
    return json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _local_pdf_sources() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in sorted(PAPER_LIBRARY_ROOT.glob("*.pdf")):
        rows.append(
            {
                "file": str(path),
                "title_hint": path.stem,
                "status": "local_pdf_candidate_needs_metadata_audit",
            }
        )
    return rows


def build_preflight(r431_summary: str = DEFAULT_R431, r432_summary: str = DEFAULT_R432) -> Dict[str, Any]:
    r431 = _load_json(r431_summary)
    r432 = _load_json(r432_summary)
    missing = [path for path in FRONT_MATTER_SECTIONS if not _repo_path(path).exists()]
    draft_safe = bool(r431.get("draft_sanity_pass") and r432.get("scaffold_links_all_existing_sections"))
    return {
        "run_id": "R433",
        "title": "Front matter and related work preflight",
        "claim_boundary": (
            "R433 identifies missing front-matter sections and related-work candidate sources. "
            "It does not generate final BibTeX or authorize manuscript claims."
        ),
        "no_api": True,
        "broad_api": False,
        "missing_front_matter_sections": missing,
        "local_pdf_sources": _local_pdf_sources(),
        "web_seed_sources": WEB_SEED_SOURCES,
        "research_lit_sources_contributed": ["local", "web"],
        "citation_audit_required_before_final_bib": True,
        "front_matter_draft_authorized_next": draft_safe,
        "main_tex_update_required_after_front_matter": True,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R434_front_matter_initial_draft",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R433 Front Matter And Related Work Preflight",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Missing Sections",
        "",
    ]
    rows.extend(f"- `{path}`" for path in summary["missing_front_matter_sections"])
    rows.extend(["", "## Local PDFs", ""])
    rows.extend(f"- `{row['title_hint']}`: `{row['file']}`" for row in summary["local_pdf_sources"])
    rows.extend(["", "## Web Seed Sources", ""])
    rows.extend(f"- {row['title']}: {row['url']} ({row['role']})" for row in summary["web_seed_sources"])
    rows.extend(
        [
            "",
            f"- Citation audit required before final BibTeX: `{summary['citation_audit_required_before_final_bib']}`",
            f"- Front matter draft authorized next: `{summary['front_matter_draft_authorized_next']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )
    return "\n".join(rows)


def run_preflight(
    r431_summary: str = DEFAULT_R431,
    r432_summary: str = DEFAULT_R432,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_preflight(r431_summary=r431_summary, r432_summary=r432_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight front matter and related-work source inputs.")
    parser.add_argument("--r431_summary", default=DEFAULT_R431)
    parser.add_argument("--r432_summary", default=DEFAULT_R432)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_preflight(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
