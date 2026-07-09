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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r451_journal_scope_gap_matrix_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r451_journal_scope_gap_matrix_report.md"


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


def _scope_gap_matrix() -> List[Dict[str, str]]:
    return [
        {
            "claim_or_component": "PromptNode as first-class MAS graph organization element",
            "JAIR_fit": "strong",
            "KAIS_fit": "medium",
            "current_evidence": "Method defines typed PromptNodes, read/write/forward PromptEdges, and lifecycle actions.",
            "gap": "Need clearer theoretical positioning as graph organization rather than prompt engineering.",
            "action": "Tighten abstract/introduction around MAS graph organization and reliability.",
        },
        {
            "claim_or_component": "Held-out improvements over ARG-Designer on AQuA and MMLU STEM",
            "JAIR_fit": "strong",
            "KAIS_fit": "medium",
            "current_evidence": "AQuA audit-clean 31/31 vs 28/31; MMLU STEM 95/97 vs 88/97.",
            "gap": "External result-integrity audit pending.",
            "action": "Do not authorize paper claims until external experiment and paper-claim audits are imported.",
        },
        {
            "claim_or_component": "Non-math generality",
            "JAIR_fit": "medium",
            "KAIS_fit": "medium",
            "current_evidence": "Mixed non-STEM no-harm 41/48 vs 41/48; DefinitionChallenge 22/24 vs 21/24.",
            "gap": "No broad positive non-math improvement is supported.",
            "action": "State no-harm and narrow positive DefinitionChallenge result; avoid broad nonmath improvement claims.",
        },
        {
            "claim_or_component": "Reliability through audit-clean evaluation",
            "JAIR_fit": "strong",
            "KAIS_fit": "strong",
            "current_evidence": "AQuA and MMLU label-noise audits are recorded; appendix finalization pending.",
            "gap": "Appendix text needs final task-level documentation.",
            "action": "Finalize audit-clean appendix and sensitivity analysis before submission.",
        },
        {
            "claim_or_component": "Knowledge-system framing",
            "JAIR_fit": "medium",
            "KAIS_fit": "strong",
            "current_evidence": "PromptNodes carry structured instructions, verifier states, and memory-like graph state.",
            "gap": "Current manuscript is not framed as a knowledge/information system.",
            "action": "Keep KAIS as backup unless rewriting around knowledge-state propagation and information-system reliability.",
        },
        {
            "claim_or_component": "Cost and deployment practicality",
            "JAIR_fit": "medium",
            "KAIS_fit": "medium",
            "current_evidence": "Cost table includes exact or probe-estimated token/cost fields and R065/R095 comparisons.",
            "gap": "Some cost numbers are probe estimates, not exact original reruns.",
            "action": "Label cost provenance clearly and avoid overstating cost-normalized dominance.",
        },
    ]


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R451 Journal Scope Gap Matrix",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Primary target: `{summary['primary_target']}`",
        f"- Secondary target: `{summary['secondary_target']}`",
        "",
        "## Scope Terms",
        "",
    ]
    for journal, terms in summary["target_scope_terms"].items():
        rows.append(f"- `{journal}`: {', '.join(f'`{term}`' for term in terms)}")
    rows.extend(["", "## Matrix", ""])
    for row in summary["scope_gap_matrix"]:
        rows.extend(
            [
                f"### {row['claim_or_component']}",
                "",
                f"- JAIR fit: `{row['JAIR_fit']}`",
                f"- KAIS fit: `{row['KAIS_fit']}`",
                f"- Current evidence: {row['current_evidence']}",
                f"- Gap: {row['gap']}",
                f"- Action: {row['action']}",
                "",
            ]
        )
    rows.extend(["## Claim Tightening Actions", ""])
    rows.extend(f"- `{action}`" for action in summary["claim_tightening_actions"])
    rows.extend(["", "## Sources", ""])
    rows.extend(f"- {source}" for source in summary["sources_used"])
    rows.extend(
        [
            "",
            f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )
    return "\n".join(rows)


def run_matrix(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "run_id": "R451",
        "title": "Journal scope gap matrix",
        "claim_boundary": (
            "R451 maps the current manuscript claims to JAIR and KAIS scope evidence. "
            "It does not change experiments, transmit audit material, or certify submission readiness."
        ),
        "no_api": True,
        "broad_api": False,
        "primary_target": "JAIR",
        "secondary_target": "KAIS",
        "target_scope_terms": {
            "JAIR": [
                "agents_and_multi_agent_systems",
                "machine_learning",
                "knowledge_representation",
                "automated_reasoning",
                "natural_language",
            ],
            "KAIS": [
                "knowledge_systems",
                "advanced_information_systems",
                "theoretical_foundations",
                "infrastructure",
                "enabling_technologies",
            ],
        },
        "scope_gap_matrix": _scope_gap_matrix(),
        "recommended_framing": (
            "Primary JAIR framing: reliable graph organization for multi-agent LLM systems via first-class "
            "PromptNodes and typed PromptEdges. KAIS backup framing requires a stronger knowledge-state "
            "propagation narrative."
        ),
        "claim_tightening_actions": [
            "no_broad_nonmath_improvement_claim",
            "label_cost_provenance_exact_vs_probe",
            "external_audit_before_claim_authorization",
            "appendix_label_noise_disclosure",
            "position_promptnodes_as_graph_organization_not_answer_patch",
        ],
        "sources_used": [
            "https://www.jair.org/",
            "https://link.springer.com/journal/10115/aims-and-scope",
            "https://www.journalmetrics.org/journal/journal-of-artificial-intelligence-research",
            "https://www.journalmetrics.org/journal/knowledge-and-information-systems",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R452_five_run_goal_audit_and_compile_probe",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build journal scope gap matrix.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_matrix(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
