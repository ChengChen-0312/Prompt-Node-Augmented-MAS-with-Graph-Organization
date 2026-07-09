from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r398_nonmath_contrastive_verifier_design_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r398_nonmath_contrastive_verifier_design_report.md"


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


def build_design_summary() -> Dict[str, Any]:
    return {
        "run_id": "R398",
        "title": "Nonmath contrastive verifier design",
        "claim_boundary": (
            "R398 is a design step derived from R397 error taxonomy. It adds general-purpose nonmath PromptNodes "
            "and PromptEdges, but does not execute API or support a result claim."
        ),
        "no_api": True,
        "broad_api": False,
        "promptnode_roles": {
            "PN_ContrastiveOptionVerifier": {
                "purpose": "Require the candidate answer to defeat the nearest plausible distractor before forwarding.",
                "intended_errors": ["wrong_forward_definition_misbinding", "candidate_quality_failure"],
            },
            "PN_ConceptDefinitionAnchor": {
                "purpose": "Anchor the decision in a concise concept or definition before binding an option.",
                "intended_errors": ["logical_fallacies", "moral_disputes", "philosophy"],
            },
            "PN_AbstentionRecoveryVerifier": {
                "purpose": "Retry only abstentions by comparing options semantically; it must still leave candidate_label empty if no option is supported.",
                "intended_errors": ["abstention_or_schema_failure"],
            },
            "PN_ConsensusConflictResolver": {
                "purpose": "Block candidate forwarding when the contrastive verifier cannot separate top two options.",
                "intended_errors": ["wrong_forward_definition_misbinding"],
            },
        },
        "promptedge_roles": {
            "PE_RejectNearestDistractor": "Forward only if the rationale names one plausible distractor and rejects it with a visible reason.",
            "PE_DefinitionAnchorBinding": "Forward only if a short concept/definition anchor is present.",
            "PE_EvidenceSpecificityGate": "Downweight generic rationales that do not quote or paraphrase a task-specific clue.",
            "PE_AbstentionRecoveryRoute": "Route empty candidate_label cases to the abstention recovery verifier; never use gold labels.",
        },
        "expected_policy_features": [
            "candidate_has_rejected_distractor",
            "candidate_has_definition_anchor",
            "candidate_evidence_specificity",
            "candidate_abstention_recovered",
            "promptedge_has_contrast",
        ],
        "targeted_probe_authorized_next": True,
        "api_execution_authorized_now": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R399_contrastive_verifier_targeted_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R398 Nonmath Contrastive Verifier Design",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## PromptNodes",
        "",
    ]
    rows.extend(f"- `{name}`: {payload['purpose']}" for name, payload in summary["promptnode_roles"].items())
    rows.extend(["", "## PromptEdges", ""])
    rows.extend(f"- `{name}`: {text}" for name, text in summary["promptedge_roles"].items())
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(summary_json: str = DEFAULT_SUMMARY_JSON, report_md: str = DEFAULT_REPORT_MD) -> Dict[str, Any]:
    summary = build_design_summary()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Design nonmath contrastive verifier PromptNodes and PromptEdges.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
