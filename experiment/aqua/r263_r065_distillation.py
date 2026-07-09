from __future__ import annotations

from typing import Any, Dict, List


def gate_triggers(features: Dict[str, Any], spec: Dict[str, Any]) -> bool:
    if "risk_min" in spec and float(features.get("risk_score") or 0) < float(spec["risk_min"]):
        return False
    if "objective_top_score_min" in spec and float(features.get("objective_top_score") or 0) < float(
        spec["objective_top_score_min"]
    ):
        return False
    if spec.get("requires_objective_differs") and not bool(features.get("objective_differs_from_arg")):
        return False
    return True


def evaluate_gate(
    rows: List[Dict[str, Any]],
    spec: Dict[str, Any],
    promptnode_cost_per_trigger: float,
) -> Dict[str, Any]:
    selected_correct = 0
    triggers = 0
    fixes = 0
    harms = 0
    clean_fixes = 0
    clean_harms = 0
    for row in rows:
        triggered = gate_triggers(row.get("features", {}), spec)
        if triggered:
            triggers += 1
            correct = bool(row.get("teacher_correct"))
            fixes += int(bool(row.get("teacher_would_fix")))
            harms += int(bool(row.get("teacher_would_harm")))
            clean = row.get("labels_not_model_visible", {}).get("clean_label") == "clean"
            clean_fixes += int(clean and bool(row.get("teacher_would_fix")))
            clean_harms += int(clean and bool(row.get("teacher_would_harm")))
        else:
            correct = bool(row.get("arg_correct"))
        selected_correct += int(correct)
    return {
        "name": spec.get("name", "unnamed_gate"),
        "selected_correct": selected_correct,
        "total": len(rows),
        "triggers": triggers,
        "fixes": fixes,
        "harms": harms,
        "clean_fixes": clean_fixes,
        "clean_harms": clean_harms,
        "estimated_incremental_cost": round(triggers * float(promptnode_cost_per_trigger), 6),
        "spec": dict(spec),
    }


def search_gate_specs(
    rows: List[Dict[str, Any]],
    promptnode_cost_per_trigger: float,
) -> List[Dict[str, Any]]:
    specs = [
        {"name": "risk_ge_1", "risk_min": 1},
        {"name": "risk_ge_2", "risk_min": 2},
        {"name": "top_ge_1", "objective_top_score_min": 1},
        {"name": "top_ge_2", "objective_top_score_min": 2},
        {
            "name": "risk_ge_1_top_ge_2_differs",
            "risk_min": 1,
            "objective_top_score_min": 2,
            "requires_objective_differs": True,
        },
    ]
    candidates = [evaluate_gate(rows, spec, promptnode_cost_per_trigger) for spec in specs]
    return sorted(
        candidates,
        key=lambda item: (
            -int(item["selected_correct"]),
            int(item["harms"]),
            float(item["estimated_incremental_cost"]),
            -int(item["fixes"]),
        ),
    )
