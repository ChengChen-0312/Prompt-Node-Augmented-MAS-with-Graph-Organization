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


DEFAULT_R306_SUMMARY = "experiment/mmlu/res_logs/mmlu_r306_nonmath_stack_eval_summary.json"
DEFAULT_R309_SUMMARY = "experiment/mmlu/res_logs/mmlu_r309_negative_controls_summary.json"
DEFAULT_R312_SUMMARY = "experiment/mmlu/res_logs/mmlu_r312_nonstem_safety_replay_summary.json"
DEFAULT_R313_SUMMARY = "experiment/mmlu/res_logs/mmlu_r313_claim_matrix_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r315_ablation_table_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r315_ablation_table_report.md"


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


def _score(correct: Any, total: Any) -> str:
    return f"{int(correct)}/{int(total)}"


def _control(r309: Dict[str, Any], name: str) -> Dict[str, Any]:
    return dict(r309.get("controls", {}).get(name, {}))


def build_ablation_rows(r306: Dict[str, Any], r309: Dict[str, Any], r312: Dict[str, Any]) -> List[Dict[str, Any]]:
    main_total = int(r306.get("main_records", 97))
    r306_main = _score(r306.get("main_correct", 0), main_total)
    r304_main = _score(r306.get("r304_main_correct", 0), main_total)
    no_safety = _control(r309, "no_safety_gate_unsafe_forward")
    no_lifecycle = _control(r309, "no_lifecycle_prune_disabled")
    random_forward = _control(r309, "random_forward_same_budget")
    random_type = _control(r309, "random_promptnode_type_same_budget")
    always_forward = _control(r309, "always_forward_candidate_nodes")
    nonstem_replay = r312.get("by_variant", {}).get("proposed_nonstem_promptnode_promptedge_safety_replay", {})

    return [
        {
            "name": "remove_nonmath_promptnodes",
            "status": "completed",
            "reference": "R306_vs_R304",
            "slice": "MMLU_STEM_main97",
            "full_method": r306_main,
            "observed_main": r304_main,
            "delta_vs_full": int(r306.get("r304_main_correct", 0)) - int(r306.get("main_correct", 0)),
            "what_it_tests": "Contribution of non-math semantic/contradiction PromptNodes beyond symbolic R304.",
            "expected_if_component_matters": "R306 should outperform R304 on semantic consistency cases.",
            "interpretation": "nonmath_nodes_add_two_clean_repairs",
            "priority": 1,
        },
        {
            "name": "remove_safety_gate",
            "status": "completed",
            "reference": "R309_no_safety_gate_unsafe_forward",
            "slice": "MMLU_STEM_main97",
            "full_method": r306_main,
            "observed_main": no_safety.get("main97", "unknown"),
            "delta_vs_full": int(no_safety.get("main_correct", 0)) - int(r306.get("main_correct", 0)),
            "fix_harm": no_safety.get("main_fix_harm", "unknown"),
            "what_it_tests": "Whether PromptNode forwarding is safe without PN_SafetyGate.",
            "expected_if_component_matters": "Removing the gate should introduce harms and lower accuracy.",
            "interpretation": "safety_gate_prevents_large_harm",
            "priority": 1,
        },
        {
            "name": "remove_lifecycle_prune",
            "status": "completed",
            "reference": "R309_no_lifecycle_prune_disabled",
            "slice": "MMLU_STEM_main97",
            "full_method": r306_main,
            "observed_main": no_lifecycle.get("main97", "unknown"),
            "delta_vs_full": int(no_lifecycle.get("main_correct", 0)) - int(r306.get("main_correct", 0)),
            "fix_harm": no_lifecycle.get("main_fix_harm", "unknown"),
            "forwarded": no_lifecycle.get("main_forwarded"),
            "full_forwarded": r309.get("reference", {}).get("r306_main_forwarded"),
            "cost_normalized_correct": no_lifecycle.get("main_cost_normalized_correct"),
            "full_cost_normalized_correct": r309.get("reference", {}).get("r306_main_cost_normalized_correct"),
            "what_it_tests": "Whether lifecycle prune/compress matters for efficiency even when accuracy ties.",
            "expected_if_component_matters": "Accuracy may tie, but routing cost should rise without prune.",
            "interpretation": "accuracy_ties_but_cost_worse",
            "priority": 1,
        },
        {
            "name": "random_forward_same_budget",
            "status": "completed",
            "reference": "R309_random_forward_same_budget",
            "slice": "MMLU_STEM_main97",
            "full_method": r306_main,
            "observed_main": random_forward.get("main97", "unknown"),
            "fix_harm": random_forward.get("main_fix_harm", "unknown"),
            "what_it_tests": "Whether gains are just from switching the same number of answers at random.",
            "expected_if_component_matters": "Random forwarding should not match R306 and should introduce harm.",
            "interpretation": "not_explained_by_random_switch_budget",
            "priority": 1,
        },
        {
            "name": "random_promptnode_type",
            "status": "completed",
            "reference": "R309_random_promptnode_type_same_budget",
            "slice": "MMLU_STEM_main97",
            "full_method": r306_main,
            "observed_main": random_type.get("main97", "unknown"),
            "fix_harm": random_type.get("main_fix_harm", "unknown"),
            "what_it_tests": "Whether PromptNode identity/type carries meaningful routing information.",
            "expected_if_component_matters": "Randomizing type should suppress useful forwarding.",
            "interpretation": "node_identity_matters_for_gate",
            "priority": 2,
        },
        {
            "name": "always_forward_candidate_nodes",
            "status": "completed",
            "reference": "R309_always_forward_candidate_nodes",
            "slice": "MMLU_STEM_main97",
            "full_method": r306_main,
            "observed_main": always_forward.get("main97", "unknown"),
            "fix_harm": always_forward.get("main_fix_harm", "unknown"),
            "forwarded": always_forward.get("main_forwarded"),
            "full_forwarded": r309.get("reference", {}).get("r306_main_forwarded"),
            "what_it_tests": "Whether explicit routing policy saves cost compared with forwarding all candidates.",
            "expected_if_component_matters": "Accuracy can tie, but cost should be worse.",
            "interpretation": "accuracy_ties_but_cost_worse",
            "priority": 2,
        },
        {
            "name": "answer_bearing_vs_warning_only_promptnodes",
            "status": "completed",
            "reference": "R311_raw_vs_R312_safety_replay",
            "slice": "MMLU_nonSTEM40",
            "full_method": r312.get("proposed_safety_replay_main", "unknown"),
            "observed_main": r312.get("proposed_safety_replay_main", "unknown"),
            "fix_harm": r312.get("fix_harm_vs_arg", "unknown"),
            "switches": nonstem_replay.get("switches"),
            "what_it_tests": "Whether warning-only nodes should update/compress/prune rather than override answers.",
            "expected_if_component_matters": "Warning-only override should harm; lifecycle safety should recover no-harm.",
            "interpretation": "warning_nodes_are_lifecycle_nodes_not_answer_nodes",
            "priority": 1,
        },
        {
            "name": "remove_promptedge_text",
            "status": "pending",
            "reference": "R316_required",
            "slice": "MMLU_STEM_main97_and_nonSTEM40",
            "full_method": "pending",
            "observed_main": "pending",
            "what_it_tests": "Whether prompt text carried on edges adds value beyond node identity.",
            "expected_if_component_matters": "Removing edge text should reduce safe switches or increase ambiguity.",
            "interpretation": "not_measured_yet",
            "priority": 1,
        },
        {
            "name": "remove_symbolic_verifier_family",
            "status": "pending",
            "reference": "R316_required",
            "slice": "MMLU_STEM_main97",
            "full_method": "pending",
            "observed_main": "pending",
            "what_it_tests": "Separate symbolic/math contribution from non-math PromptNodes.",
            "expected_if_component_matters": "MMLU STEM should drop toward ARG or lose R304 repairs.",
            "interpretation": "not_measured_yet",
            "priority": 1,
        },
        {
            "name": "cost_matched_plain_requery",
            "status": "pending",
            "reference": "R316_required",
            "slice": "AQuA_tail34_MMLU_STEM_main97_nonSTEM40",
            "full_method": "pending",
            "observed_main": "pending",
            "what_it_tests": "Whether gains exceed simply spending the same token/API budget on direct requery.",
            "expected_if_component_matters": "PromptNode should match or beat requery at lower or comparable cost on the claimed slices.",
            "interpretation": "not_measured_yet",
            "priority": 1,
        },
    ]


def build_ablation_table_summary(
    r306_summary: str = DEFAULT_R306_SUMMARY,
    r309_summary: str = DEFAULT_R309_SUMMARY,
    r312_summary: str = DEFAULT_R312_SUMMARY,
    r313_summary: str = DEFAULT_R313_SUMMARY,
) -> Dict[str, Any]:
    r306 = _load_json(r306_summary)
    r309 = _load_json(r309_summary)
    r312 = _load_json(r312_summary)
    r313 = _load_json(r313_summary)
    rows = build_ablation_rows(r306, r309, r312)
    pending = [row["name"] for row in rows if row["status"] == "pending" and int(row["priority"]) <= 1]
    return {
        "run_id": "R315",
        "title": "Ablation table and reviewer-check queue",
        "claim_boundary": (
            "R315 consolidates completed ablations and marks required pending ablations. It does not train, "
            "does not call APIs, and does not make new accuracy claims."
        ),
        "no_api": True,
        "broad_api": False,
        "source_summaries": {
            "r306": r306_summary,
            "r309": r309_summary,
            "r312": r312_summary,
            "r313": r313_summary,
        },
        "claim_permissions_from_r313": r313.get("claim_permissions", {}),
        "ablation_table": rows,
        "completed_ablations": [row["name"] for row in rows if row["status"] == "completed"],
        "pending_ablations": [row["name"] for row in rows if row["status"] == "pending"],
        "priority_pending_ablations": pending,
        "training_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R316_promptedge_text_and_cost_matched_controls",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R315 Ablation Table",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Ablation | Status | Slice | Full | Observed | Interpretation | Priority |",
        "|---|---|---|---:|---:|---|---:|",
    ]
    for row in summary["ablation_table"]:
        rows.append(
            "| `{name}` | `{status}` | `{slice}` | `{full}` | `{observed}` | {interp} | `{priority}` |".format(
                name=row["name"],
                status=row["status"],
                slice=row["slice"],
                full=row.get("full_method", "-"),
                observed=row.get("observed_main", "-"),
                interp=row.get("interpretation", ""),
                priority=row["priority"],
            )
        )
    rows.extend(["", "## Priority Pending", ""])
    rows.extend(f"- `{name}`" for name in summary["priority_pending_ablations"])
    rows.append("")
    return "\n".join(rows)


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_ablation_table_summary()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R315 ablation table.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
