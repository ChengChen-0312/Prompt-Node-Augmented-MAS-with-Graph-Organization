from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_OUTPUT_MD = "PAPER_PLAN.md"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r331_paper_outline_scaffold_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r331_paper_outline_scaffold_report.md"


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


def _claim(claim_id: str, claim: str, evidence: str, status: str, section: str) -> Dict[str, str]:
    return {
        "id": claim_id,
        "claim": claim,
        "evidence": evidence,
        "status": status,
        "section": section,
    }


def build_paper_outline_scaffold() -> Dict[str, Any]:
    claims = [
        _claim(
            "C1_aqua_clean_gain",
            "PromptNode-guided graph organization improves ARG-Designer on the audited AQuA tail split.",
            "R321 main table: ARG 28/31 vs PromptNode 31/31 after excluding task_59/task_139/task_228.",
            "supported",
            "§5.1",
        ),
        _claim(
            "C2_mmlu_stem_gain",
            "The method transfers to MMLU STEM with a clean positive gain over ARG-Designer.",
            "R321/R306: ARG 88/97 vs PromptNode 95/97; fix/harm 7/0.",
            "supported",
            "§5.2",
        ),
        _claim(
            "C3_nonstem_no_harm_boundary",
            "Non-STEM transfer currently supports a no-harm boundary, not an improvement claim.",
            "R312/R321: ARG 37/40 vs safety replay 37/40; fix/harm 0/0; raw non-STEM 34/40 is reported as limitation.",
            "supported_boundary",
            "§5.3 and §7",
        ),
        _claim(
            "C4_promptedge_selector_safety",
            "PromptEdge text is a safety feature for train-time graph-policy selection.",
            "R327: no-family selector without edge text creates 1 false forward; with edge text creates 0.",
            "partial_offline",
            "§6.2",
        ),
        _claim(
            "C5_broad_general_improvement",
            "PromptNode universally improves multi-agent reasoning across all multiple-choice datasets.",
            "Contradicted by raw non-STEM negative transfer; no prospective selector API evaluation yet.",
            "blocked",
            "Not claimed",
        ),
    ]
    sections = [
        {
            "id": "abstract",
            "title": "Abstract",
            "page_budget": "0.25 pages",
            "contents": "State the graph-organization problem, PromptNode/PromptEdge method, AQuA/MMLU gains, no-harm boundary, and honest limitation.",
        },
        {
            "id": "introduction",
            "title": "Introduction",
            "page_budget": "1.5 pages",
            "contents": "Motivate MAS graph organization, explain why post-hoc answer patches are insufficient, and state the first-class virtual-node contribution.",
        },
        {
            "id": "related_work",
            "title": "Related Work",
            "page_budget": "1.5 pages",
            "contents": "Organize around MAS graph optimization, agent pruning/dropout, workflow optimization, and verifier/tool-augmented reasoning. All citations require later audit.",
        },
        {
            "id": "method",
            "title": "PromptNode-Augmented MAS",
            "page_budget": "2.0 pages",
            "contents": "Define PromptNode identity, PromptEdge read/write/forward permissions, lifecycle actions, insertion locations, and selector gate.",
        },
        {
            "id": "experimental_setup",
            "title": "Experimental Setup",
            "page_budget": "1.2 pages",
            "contents": "ARG-Designer baseline, model setting, AQuA audit-clean protocol, MMLU STEM/non-STEM transfer, cost accounting, and label-audit appendix contract.",
        },
        {
            "id": "results_and_ablations",
            "title": "Results and Ablations",
            "page_budget": "2.5 pages",
            "contents": "Main results, completed negative controls, component ablations, cost-matched requery, symbolic vs non-math separation.",
        },
        {
            "id": "selector_and_cases",
            "title": "Selector Dry Run and Case Studies",
            "page_budget": "1.5 pages",
            "contents": "Offline leakage-safe selector manifest, hard negatives, PromptEdge feature ablation, and four mechanism case studies.",
        },
        {
            "id": "limitations_conclusion",
            "title": "Limitations and Conclusion",
            "page_budget": "0.8 pages",
            "contents": "State no broad non-STEM improvement yet, selector needs prospective evaluation, and SCI-Q2 submission still needs citation/claim audits.",
        },
    ]
    return {
        "run_id": "R331",
        "title": "Paper outline scaffold",
        "working_title": "PromptNode-Augmented Multi-Agent Graphs for Robust Reasoning",
        "one_sentence_contribution": (
            "We introduce PromptNodes as first-class virtual graph elements with typed identities, PromptEdges, and "
            "lifecycle actions, improving audited AQuA tail and MMLU STEM reasoning over ARG-Designer while exposing "
            "clear no-harm and training boundaries."
        ),
        "target_venue": "SCI_Q2_JOURNAL",
        "paper_type": "method_and_empirical_diagnostic",
        "claims_evidence_matrix": claims,
        "sections": sections,
        "section_count": len(sections),
        "figure_plan_source": "experiment/mmlu/res_logs/mmlu_r330_paper_tables_and_figures_plan_summary.json",
        "citation_status": "needs_audit",
        "reviewer_feedback_status": "not_run_no_external_reviewer_tool_available",
        "goal_audit_due_next": True,
        "sci_q2_ready": False,
        "next_required_run": "R332_goal_audit_after_paper_scaffold",
    }


def render_plan(summary: Dict[str, Any]) -> str:
    rows = [
        "# Paper Plan",
        "",
        f"**Title**: {summary['working_title']}",
        f"**One-sentence contribution**: {summary['one_sentence_contribution']}",
        f"**Venue**: {summary['target_venue']}",
        f"**Type**: {summary['paper_type']}",
        f"**Section count**: {summary['section_count']}",
        "",
        "## Claims-Evidence Matrix",
        "",
        "| ID | Claim | Evidence | Status | Section |",
        "|---|---|---|---|---|",
    ]
    for claim in summary["claims_evidence_matrix"]:
        rows.append(
            f"| `{claim['id']}` | {claim['claim']} | {claim['evidence']} | `{claim['status']}` | {claim['section']} |"
        )
    rows.extend(["", "## Structure", ""])
    for section in summary["sections"]:
        rows.extend(
            [
                f"### {section['title']}",
                f"- **Page budget**: {section['page_budget']}",
                f"- **Contents**: {section['contents']}",
                "",
            ]
        )
    rows.extend(
        [
            "## Figure Plan",
            "",
            "See `experiment/mmlu/res_logs/mmlu_r330_paper_tables_and_figures_plan_summary.json`.",
            "",
            "## Citation Plan",
            "",
            "All citations are placeholders until citation audit. Related work should cover ARG-Designer, MAS graph optimization, agent pruning/dropout, workflow optimization, verifier/tool-augmented reasoning, and selector/gating methods.",
            "",
            "## Reviewer Feedback",
            "",
            "External GPT-5.5 outline review was not run in this local pass; mark as required before paper drafting freeze.",
            "",
            "## Next Steps",
            "",
            "- Run R332 goal audit.",
            "- Draft method/results sections only from supported claims.",
            "- Run citation audit and paper claim audit before submission claims.",
            "",
        ]
    )
    return "\n".join(rows)


def run(
    output_md: str = DEFAULT_OUTPUT_MD,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_paper_outline_scaffold()
    summary.update({"output_md": output_md, "summary_json": summary_json, "report_md": report_md})
    plan = render_plan(summary)
    _write_text(output_md, plan)
    _write_json(summary_json, summary)
    _write_text(report_md, plan)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R331 paper outline scaffold.")
    parser.add_argument("--output_md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
