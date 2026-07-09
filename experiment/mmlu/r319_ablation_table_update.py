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


DEFAULT_R315_SUMMARY = "experiment/mmlu/res_logs/mmlu_r315_ablation_table_summary.json"
DEFAULT_R316_SUMMARY = "experiment/mmlu/res_logs/mmlu_r316_promptedge_cost_controls_summary.json"
DEFAULT_R318_SUMMARY = "experiment/mmlu/res_logs/mmlu_r318_symbolic_family_ablation_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r319_ablation_table_update_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r319_ablation_table_update_report.md"


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


def _score(item: Dict[str, Any]) -> str:
    return f"{int(item.get('correct', 0))}/{int(item.get('evaluated_records', 0))}"


def update_ablation_rows(rows: List[Dict[str, Any]], r316: Dict[str, Any], r318: Dict[str, Any]) -> List[Dict[str, Any]]:
    by_variant = r316.get("by_variant", {})
    node_only = by_variant.get("node_only_no_promptedge_text", {})
    plain = by_variant.get("plain_requery", {})
    updated: List[Dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        if out["name"] == "remove_promptedge_text":
            out.update(
                {
                    "status": "completed",
                    "reference": "R316_node_only_no_promptedge_text",
                    "slice": "MMLU_nonSTEM40",
                    "full_method": "37/40",
                    "observed_main": _score(node_only),
                    "delta_vs_full": node_only.get("delta_vs_arg"),
                    "fix_harm": node_only.get("fix_harm"),
                    "interpretation": "removing_promptedge_text_harms_nonstem_safety",
                }
            )
        elif out["name"] == "cost_matched_plain_requery":
            out.update(
                {
                    "status": "completed",
                    "reference": "R316_plain_requery",
                    "slice": "MMLU_nonSTEM40",
                    "full_method": "37/40",
                    "observed_main": _score(plain),
                    "delta_vs_full": plain.get("delta_vs_arg"),
                    "fix_harm": plain.get("fix_harm"),
                    "interpretation": "plain_requery_ties_arg_but_has_fix_and_harm",
                }
            )
        elif out["name"] == "remove_symbolic_verifier_family":
            out.update(
                {
                    "status": "completed",
                    "reference": "R318_symbolic_family_ablation",
                    "slice": "MMLU_STEM_main97",
                    "full_method": r318.get("full_r306_main", "95/97"),
                    "observed_main": r318.get("nonmath_only_main", "unknown"),
                    "delta_vs_full": -int(r318.get("symbolic_family_delta", 0)),
                    "fix_harm": r318.get("nonmath_only_fix_harm"),
                    "interpretation": "symbolic_family_adds_five_stem_repairs",
                }
            )
        updated.append(out)
    return updated


def build_updated_ablation_summary(
    r315_summary: str = DEFAULT_R315_SUMMARY,
    r316_summary: str = DEFAULT_R316_SUMMARY,
    r318_summary: str = DEFAULT_R318_SUMMARY,
) -> Dict[str, Any]:
    r315 = _load_json(r315_summary)
    rows = update_ablation_rows(
        list(r315.get("ablation_table", [])),
        _load_json(r316_summary),
        _load_json(r318_summary),
    )
    priority_pending = [row["name"] for row in rows if row["status"] == "pending" and int(row["priority"]) <= 1]
    return {
        "run_id": "R319",
        "title": "Updated ablation table after R316/R318",
        "claim_boundary": "R319 updates the ablation ledger only. It does not train and does not broaden claims.",
        "no_api": True,
        "broad_api": False,
        "ablation_table": rows,
        "completed_ablations": [row["name"] for row in rows if row["status"] == "completed"],
        "pending_ablations": [row["name"] for row in rows if row["status"] == "pending"],
        "priority_pending_ablations": priority_pending,
        "claim_permissions": {
            "all_priority_ablations_completed": not priority_pending,
            "training_authorized": False,
            "sci_q2_ready": False,
        },
        "training_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R320_goal_audit_after_ablations",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R319 Updated Ablation Table",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Ablation | Status | Slice | Full | Observed | Fix/Harm | Interpretation |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in summary["ablation_table"]:
        rows.append(
            f"| `{row['name']}` | `{row['status']}` | `{row['slice']}` | `{row.get('full_method', '-')}` | `{row.get('observed_main', '-')}` | `{row.get('fix_harm', '-')}` | {row.get('interpretation', '')} |"
        )
    rows.extend(["", f"- Priority pending: `{summary['priority_pending_ablations']}`", ""])
    return "\n".join(rows)


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_updated_ablation_summary()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update R315 ablation table with R316/R318.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
