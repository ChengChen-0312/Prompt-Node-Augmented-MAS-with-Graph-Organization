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


DEFAULT_R321_SUMMARY = "experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json"
DEFAULT_R381_SUMMARY = "experiment/mmlu/res_logs/mmlu_r381_option_binding_fresh_eval_analysis_summary.json"
DEFAULT_R396_SUMMARY = "experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json"
DEFAULT_R401_SUMMARY = "experiment/mmlu/res_logs/mmlu_r401_contrastive_verifier_targeted_analysis_and_goal_audit_summary.json"
DEFAULT_EVIDENCE_PRECHECK = ".aris/evidence_precheck.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r402_result_to_claim_synthesis_for_paper_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r402_result_to_claim_synthesis_for_paper_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_claim_synthesis(
    r321_summary: str = DEFAULT_R321_SUMMARY,
    r381_summary: str = DEFAULT_R381_SUMMARY,
    r396_summary: str = DEFAULT_R396_SUMMARY,
    r401_summary: str = DEFAULT_R401_SUMMARY,
    evidence_precheck: str = DEFAULT_EVIDENCE_PRECHECK,
) -> Dict[str, Any]:
    r321 = _load_json(r321_summary)
    r381 = _load_json(r381_summary)
    r396 = _load_json(r396_summary)
    r401 = _load_json(r401_summary)
    precheck = _load_json(evidence_precheck)
    claims = [
        {
            "id": "C1_aqua_audit_clean_gain",
            "status": "supported",
            "evidence": "AQuA audit-clean tail31: ARG 28/31 vs PromptNode 31/31.",
            "source": r321_summary,
            "paper_use": "main_result",
        },
        {
            "id": "C2_mmlu_stem_gain",
            "status": "supported",
            "evidence": "MMLU STEM main97: ARG 88/97 vs PromptNode 95/97, fix/harm 7/0.",
            "source": r321_summary,
            "paper_use": "main_transfer_result",
        },
        {
            "id": "C3_history_optionbinding_pilot_gain",
            "status": "partial",
            "evidence": f"Fresh history pilot R380/R381: ARG {r381.get('arg_correct')}/{r381.get('records')} vs hybrid {r381.get('hybrid_correct')}/{r381.get('records')}, but single subject and small sample.",
            "source": r381_summary,
            "paper_use": "mechanism_pilot_or_appendix",
        },
        {
            "id": "C4_mixed_nonmath_no_harm",
            "status": "supported",
            "evidence": f"Larger mixed nonmath R395/R396: ARG {r396.get('arg_correct')}/{r396.get('records')} vs hybrid {r396.get('hybrid_correct')}/{r396.get('records')}, harm {r396.get('harms')}.",
            "source": r396_summary,
            "paper_use": "boundary_no_harm_result",
        },
        {
            "id": "C5_broad_general_improvement",
            "status": "unsupported",
            "evidence": "Mixed nonmath larger split has no positive delta; contrastive branch failed safely.",
            "source": r401_summary,
            "paper_use": "forbidden_claim",
        },
    ]
    supported = [claim["id"] for claim in claims if claim["status"] == "supported"]
    partial = [claim["id"] for claim in claims if claim["status"] == "partial"]
    unsupported = [claim["id"] for claim in claims if claim["status"] == "unsupported"]
    return {
        "run_id": "R402",
        "title": "Result-to-claim synthesis for paper",
        "claim_boundary": (
            "R402 applies the result-to-claim gate. The current evidence partially supports a narrowed paper: "
            "strong clean gains on AQuA and MMLU STEM, plus no-harm boundaries on mixed nonmath. It does not "
            "support broad general improvement claims."
        ),
        "no_api": True,
        "broad_api": False,
        "skill_used": "result-to-claim",
        "evidence_precheck": precheck.get("summary", {"status": "skipped", "reason": "evidence_check.py not resolved"}),
        "overall_claim_supported": "partial",
        "claims": claims,
        "supported_claim_ids": supported,
        "partial_claim_ids": partial,
        "unsupported_claim_ids": unsupported,
        "suggested_claim_revision": (
            "PromptNode/PromptEdge graph organization improves audited AQuA tail and MMLU STEM under ARG-Designer-matched "
            "settings, while learned safety gates preserve no-harm behavior on broader nonmath multiple-choice transfer. "
            "Do not claim universal improvement."
        ),
        "missing_evidence": [
            "Larger prospective nonmath split with positive gain, not only no-harm.",
            "Independent integrity audit of all tables before manuscript submission.",
            "Cost-normalized deployment result if R065/R380 teacher-like paths are used in main text.",
            "Full paper figures/tables updated with exact claim boundaries.",
        ],
        "claim_permissions": {
            "aqua_clean_improvement_claim_allowed": True,
            "mmlu_stem_improvement_claim_allowed": True,
            "mixed_nonmath_no_harm_claim_allowed": True,
            "history_optionbinding_pilot_claim_allowed": True,
            "broad_general_improvement_claim_allowed": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "confidence": "medium",
        "next_required_run": "R403_paper_plan_update_after_claim_synthesis",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R402 Result-To-Claim Synthesis For Paper",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Overall claim supported: `{summary['overall_claim_supported']}`",
        f"- Supported claims: `{summary['supported_claim_ids']}`",
        f"- Partial claims: `{summary['partial_claim_ids']}`",
        f"- Unsupported claims: `{summary['unsupported_claim_ids']}`",
        "",
        "## Suggested Claim",
        "",
        summary["suggested_claim_revision"],
        "",
        "## Missing Evidence",
        "",
    ]
    rows.extend(f"- {item}" for item in summary["missing_evidence"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r321_summary: str = DEFAULT_R321_SUMMARY,
    r381_summary: str = DEFAULT_R381_SUMMARY,
    r396_summary: str = DEFAULT_R396_SUMMARY,
    r401_summary: str = DEFAULT_R401_SUMMARY,
    evidence_precheck: str = DEFAULT_EVIDENCE_PRECHECK,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_claim_synthesis(
        r321_summary=r321_summary,
        r381_summary=r381_summary,
        r396_summary=r396_summary,
        r401_summary=r401_summary,
        evidence_precheck=evidence_precheck,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthesize experimental results into paper claims.")
    parser.add_argument("--r321_summary", default=DEFAULT_R321_SUMMARY)
    parser.add_argument("--r381_summary", default=DEFAULT_R381_SUMMARY)
    parser.add_argument("--r396_summary", default=DEFAULT_R396_SUMMARY)
    parser.add_argument("--r401_summary", default=DEFAULT_R401_SUMMARY)
    parser.add_argument("--evidence_precheck", default=DEFAULT_EVIDENCE_PRECHECK)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
