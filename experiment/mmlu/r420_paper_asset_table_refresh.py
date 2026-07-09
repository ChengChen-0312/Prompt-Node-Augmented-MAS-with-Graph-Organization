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


DEFAULT_R321 = "experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json"
DEFAULT_R415 = "experiment/mmlu/res_logs/mmlu_r415_update_claim_matrix_after_nonmath_positive_summary.json"
DEFAULT_R416 = "experiment/mmlu/res_logs/mmlu_r416_cost_normalized_claim_table_and_goal_audit_summary.json"
DEFAULT_R417 = "experiment/mmlu/res_logs/mmlu_r417_case_study_evidence_pack_summary.json"
DEFAULT_R419 = "experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r420_paper_asset_table_refresh_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r420_paper_asset_table_refresh_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _asset(asset_type: str, title: str, source: str, paper_section: str, status: str, note: str) -> Dict[str, Any]:
    return {
        "asset_type": asset_type,
        "title": title,
        "source": source,
        "paper_section": paper_section,
        "status": status,
        "note": note,
    }


def build_paper_asset_manifest(
    r321_summary: str = DEFAULT_R321,
    r415_summary: str = DEFAULT_R415,
    r416_summary: str = DEFAULT_R416,
    r417_summary: str = DEFAULT_R417,
    r419_summary: str = DEFAULT_R419,
) -> Dict[str, Any]:
    r415 = _load_json(r415_summary)
    r416 = _load_json(r416_summary)
    r417 = _load_json(r417_summary)
    r419 = _load_json(r419_summary)
    claims = r415.get("claims", [])
    paper_assets: List[Dict[str, Any]] = [
        _asset(
            "main_result_table",
            "AQuA/MMLU main result table",
            r321_summary,
            "Results",
            "ready_with_claim_boundaries",
            "Use together with R415 claim update; broad claims remain disabled.",
        ),
        _asset(
            "claim_matrix",
            "Updated claim-evidence matrix",
            r415_summary,
            "Experimental Setup / Results",
            "ready_provisional",
            "Includes C6 narrow DefinitionChallenge positive result.",
        ),
        _asset(
            "cost_table",
            "Cost-normalized result table",
            r416_summary,
            "Results / Cost Analysis",
            "incomplete_for_submission",
            "MMLU STEM cost and external integrity audit are missing.",
        ),
        _asset(
            "case_study_pack",
            "Mechanism case studies",
            r417_summary,
            "Case Studies",
            "ready_with_caveats",
            f"{len(r417.get('case_studies', []))} reproducible case-study entries.",
        ),
        _asset(
            "lifecycle_trace",
            "PromptNode lifecycle trace",
            r419_summary,
            "Method / Case Studies",
            "ready_for_visualization",
            f"{r419.get('events')} lifecycle events from R413 replay.",
        ),
        _asset(
            "paper_plan",
            "Paper plan with claim updates",
            "PAPER_PLAN.md",
            "All sections",
            "updated",
            "Contains R402 and R415 claim-boundary updates.",
        ),
    ]
    missing_assets = []
    if not r416.get("cost_table_complete_for_submission"):
        missing_assets.append("submission_complete_cost_table")
    missing_assets.append("external_experiment_integrity_audit")
    return {
        "run_id": "R420",
        "title": "Paper asset table refresh",
        "claim_boundary": (
            "R420 indexes paper assets for drafting. It does not authorize claims or mark the paper SCI-Q2 ready."
        ),
        "no_api": True,
        "broad_api": False,
        "paper_assets": paper_assets,
        "claim_ids": [claim.get("id") for claim in claims],
        "cost_rows": len(r416.get("cost_rows", [])),
        "case_studies": len(r417.get("case_studies", [])),
        "lifecycle_events": r419.get("events"),
        "missing_assets": missing_assets,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R421_submission_readiness_goal_audit",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R420 Paper Asset Table Refresh",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Asset | Section | Status | Source | Note |",
        "|---|---|---|---|---|",
    ]
    for asset in summary["paper_assets"]:
        rows.append(
            f"| `{asset['asset_type']}` | {asset['paper_section']} | `{asset['status']}` | `{asset['source']}` | {asset['note']} |"
        )
    rows.extend(["", "## Missing Assets", ""])
    rows.extend(f"- `{item}`" for item in summary["missing_assets"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r321_summary: str = DEFAULT_R321,
    r415_summary: str = DEFAULT_R415,
    r416_summary: str = DEFAULT_R416,
    r417_summary: str = DEFAULT_R417,
    r419_summary: str = DEFAULT_R419,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_paper_asset_manifest(
        r321_summary=r321_summary,
        r415_summary=r415_summary,
        r416_summary=r416_summary,
        r417_summary=r417_summary,
        r419_summary=r419_summary,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh paper asset manifest.")
    parser.add_argument("--r321_summary", default=DEFAULT_R321)
    parser.add_argument("--r415_summary", default=DEFAULT_R415)
    parser.add_argument("--r416_summary", default=DEFAULT_R416)
    parser.add_argument("--r417_summary", default=DEFAULT_R417)
    parser.add_argument("--r419_summary", default=DEFAULT_R419)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
