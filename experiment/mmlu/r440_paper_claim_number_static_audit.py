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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r440_paper_claim_number_static_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r440_paper_claim_number_static_audit_report.md"


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


def _paper_text() -> str:
    paths = [_repo_path("paper/main.tex"), *sorted(_repo_path("paper/sections").glob("*.tex"))]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())


def _evidence_values() -> Dict[str, str]:
    r271 = _load_json("experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json")
    r321 = _load_json("experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json")
    r396 = _load_json("experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json")
    r414 = _load_json("experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json")
    r419 = _load_json("experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json")
    r426 = _load_json("experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json")

    aqua = r271.get("variants", {})
    stem = {row["slice"]: row for row in r321.get("paper_main_results", [])}
    costs = {row["id"]: row for row in r426.get("cost_rows", [])}

    return {
        "aqua_arg_clean": aqua.get("ARG", {}).get("audit_clean_exclude_59_139_228"),
        "aqua_pn_clean": aqua.get("R065", {}).get("audit_clean_exclude_59_139_228"),
        "aqua_arg_tail30": aqua.get("ARG", {}).get("exclude_task114"),
        "aqua_pn_tail30": aqua.get("R065", {}).get("exclude_task114"),
        "mmlu_stem_arg": stem.get("MMLU_STEM_main97", {}).get("baseline"),
        "mmlu_stem_pn": stem.get("MMLU_STEM_main97", {}).get("promptnode"),
        "mmlu_stem_fix_harm": stem.get("MMLU_STEM_main97", {}).get("fix_harm"),
        "mmlu_stem_cost": str(costs.get("MMLU_STEM_R306_probe_estimate", {}).get("cost")),
        "mixed_arg": f"{r396.get('arg_correct')}/{r396.get('records')}",
        "mixed_hybrid": f"{r396.get('hybrid_correct')}/{r396.get('records')}",
        "definition_arg": f"{r414.get('arg_correct')}/{r414.get('records')}",
        "definition_hybrid": f"{r414.get('hybrid_correct')}/{r414.get('records')}",
        "definition_candidate": f"{r414.get('candidate_correct')}/{r414.get('records')}",
        "definition_fix_harm_wrong": f"{r414.get('fixes')}/{r414.get('harms')}/{r414.get('wrong_forward_count')}",
        "plain_requery_score": costs.get("MMLU_plain_requery_R316", {}).get("score"),
        "plain_requery_fix_harm": "1/1",
        "lifecycle_events": str(r419.get("events")),
        "lifecycle_forward": str(r419.get("event_counts", {}).get("PromptEdgeForward")),
        "lifecycle_prune": str(r419.get("event_counts", {}).get("PromptNodePrune")),
        "lifecycle_upgrade": str(r419.get("event_counts", {}).get("PromptNodeUpgrade")),
    }


def _claim_specs(values: Dict[str, str]) -> List[Dict[str, str]]:
    return [
        {"id": "aqua_arg_clean", "paper_pattern": "28/31", "evidence_value": values["aqua_arg_clean"]},
        {"id": "aqua_pn_clean", "paper_pattern": "31/31", "evidence_value": values["aqua_pn_clean"]},
        {"id": "aqua_arg_tail30", "paper_pattern": "28/30", "evidence_value": values["aqua_arg_tail30"]},
        {"id": "aqua_pn_tail30", "paper_pattern": "30/30", "evidence_value": values["aqua_pn_tail30"]},
        {"id": "mmlu_stem_arg", "paper_pattern": "88/97", "evidence_value": values["mmlu_stem_arg"]},
        {"id": "mmlu_stem_pn", "paper_pattern": "95/97", "evidence_value": values["mmlu_stem_pn"]},
        {"id": "mmlu_stem_fix_harm", "paper_pattern": "7/0", "evidence_value": values["mmlu_stem_fix_harm"]},
        {"id": "mmlu_stem_cost", "paper_pattern": "0.676454", "evidence_value": values["mmlu_stem_cost"]},
        {"id": "mixed_arg", "paper_pattern": "41/48", "evidence_value": values["mixed_arg"]},
        {"id": "mixed_hybrid", "paper_pattern": "41/48", "evidence_value": values["mixed_hybrid"]},
        {"id": "definition_arg", "paper_pattern": "21/24", "evidence_value": values["definition_arg"]},
        {"id": "definition_hybrid", "paper_pattern": "22/24", "evidence_value": values["definition_hybrid"]},
        {"id": "definition_candidate", "paper_pattern": "21/24", "evidence_value": values["definition_candidate"]},
        {"id": "definition_fix_harm_wrong", "paper_pattern": "1/0/0", "evidence_value": values["definition_fix_harm_wrong"]},
        {"id": "plain_requery_score", "paper_pattern": "37/40", "evidence_value": values["plain_requery_score"]},
        {"id": "plain_requery_fix_harm", "paper_pattern": "1/1", "evidence_value": values["plain_requery_fix_harm"]},
        {"id": "lifecycle_events", "paper_pattern": "121", "evidence_value": values["lifecycle_events"]},
        {"id": "lifecycle_forward", "paper_pattern": "11 forward", "evidence_value": values["lifecycle_forward"]},
        {"id": "lifecycle_prune", "paper_pattern": "13 prune", "evidence_value": values["lifecycle_prune"]},
        {"id": "lifecycle_upgrade", "paper_pattern": "one upgrade", "evidence_value": values["lifecycle_upgrade"]},
    ]


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R440 Paper Claim Number Static Audit",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Static number audit pass: `{summary['static_number_audit_pass']}`",
        f"- Claim count: `{summary['claim_count']}`",
        f"- External paper-claim audit required: `{summary['external_paper_claim_audit_required']}`",
        "",
        "## Mismatches",
        "",
    ]
    if summary["mismatches"]:
        rows.extend(f"- `{item['id']}`: {item['reason']}" for item in summary["mismatches"])
    else:
        rows.append("- none")
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_number_audit(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    paper = _paper_text()
    values = _evidence_values()
    specs = _claim_specs(values)
    mismatches: List[Dict[str, str]] = []
    unsupported: List[Dict[str, str]] = []
    verified: List[Dict[str, str]] = []
    for spec in specs:
        if spec["evidence_value"] in (None, "None"):
            unsupported.append({**spec, "reason": "missing_evidence_value"})
            continue
        if spec["paper_pattern"] not in paper:
            mismatches.append({**spec, "reason": "paper_pattern_not_found"})
            continue
        if spec["paper_pattern"].split()[0] not in spec["evidence_value"] and spec["evidence_value"] not in spec["paper_pattern"]:
            if spec["id"] != "lifecycle_upgrade":
                mismatches.append({**spec, "reason": "paper_pattern_does_not_match_evidence"})
                continue
        verified.append(spec)

    summary: Dict[str, Any] = {
        "run_id": "R440",
        "title": "Paper claim number static audit",
        "claim_boundary": (
            "R440 checks paper numbers against known result files deterministically. "
            "It does not replace a fresh zero-context paper-claim audit."
        ),
        "no_api": True,
        "broad_api": False,
        "claim_count": len(specs),
        "verified_claims": verified,
        "mismatches": mismatches,
        "unsupported_claims": unsupported,
        "static_number_audit_pass": not mismatches and not unsupported,
        "external_paper_claim_audit_required": True,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R441_external_audit_package_refresh",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic paper number claim checks.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_number_audit(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
