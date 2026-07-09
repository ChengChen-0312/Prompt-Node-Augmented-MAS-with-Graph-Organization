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


DEFAULT_R358_SUMMARY = "experiment/mmlu/res_logs/mmlu_r358_learned_graph_policy_offline_training_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r359_learned_graph_policy_source_invariance_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r359_learned_graph_policy_source_invariance_audit_report.md"


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


def build_source_invariance_audit(r358_summary: str = DEFAULT_R358_SUMMARY) -> Dict[str, Any]:
    r358 = _load_json(r358_summary)
    top_features: List[str] = list(r358.get("top_positive_features") or []) + list(r358.get("top_negative_features") or [])
    risky = [feature for feature in top_features if feature.startswith("source_run=")]
    return {
        "run_id": "R359",
        "title": "Learned graph-policy source invariance audit",
        "claim_boundary": (
            "R359 audits the R358 offline model for source-run shortcut learning. It blocks fresh evaluation until "
            "source-specific features are removed or neutralized."
        ),
        "no_api": True,
        "broad_api": False,
        "audited_run": "R358",
        "source_run_feature_risk_detected": bool(risky),
        "risky_top_features": risky,
        "r358_test_f1": r358.get("test_f1"),
        "claim_permissions": {
            "r358_offline_feasibility_claim_allowed": True,
            "fresh_eval_preflight_allowed_now": False,
            "source_invariant_retraining_required": True,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "course_correction": [
            "Remove source_run and source-specific proxy features before fresh evaluation.",
            "Retrain using only task-shape, candidate-evidence, PromptNode, PromptEdge, and lifecycle features.",
            "Report R358 perfect offline score only as a failed shortcut-learning audit, not as method evidence.",
        ],
        "next_required_run": "R360_source_invariant_graph_policy_retraining",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R359 Learned Graph-Policy Source Invariance Audit",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Source-run risk detected: `{summary['source_run_feature_risk_detected']}`",
        f"- Risky top features: `{summary['risky_top_features']}`",
        "",
        "## Course Correction",
        "",
    ]
    rows.extend(f"- {item}" for item in summary["course_correction"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r358_summary: str = DEFAULT_R358_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_source_invariance_audit(r358_summary=r358_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R359 learned graph-policy source invariance audit.")
    parser.add_argument("--r358_summary", default=DEFAULT_R358_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
