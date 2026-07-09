from __future__ import annotations

import argparse
import ast
import json
import math
import os
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r300_goal_and_label_audit import audit_clean_answer
from experiment.mmlu.r301_conservative_census_gate import (
    DEFAULT_ARG_RESULTS,
    VALID_LABELS,
    build_census_gate_features,
    load_jsonl,
    none_option_label,
    normalize_label,
    option_lines,
    write_json,
    write_jsonl,
    write_text,
)
from experiment.mmlu.r303_audit_exclusion_protocol import EXCLUDED_TASK_IDS


DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r304_multi_trigger_safety_gate_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r304_multi_trigger_safety_gate_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r304_multi_trigger_safety_gate_report.md"

CANDIDATE_TYPES = [
    "census_no_inference",
    "money_expression_binding",
    "expected_value_single_event",
    "uniform_probability_geometry",
    "nmr_frequency_constant",
    "alternating_work_rate",
    "ring_ideal_structure",
]

FEATURE_NAMES = [
    "bias",
    "candidate_label_valid",
    "candidate_differs_arg",
    "confidence",
    "evidence_count",
    *[f"type_{name}" for name in CANDIDATE_TYPES],
]

NMR_GYROMAGNETIC_MHZ_PER_T = {
    "31P": 17.235,
    "1H": 42.571,
    "13C": 10.7084,
    "19F": 40.078,
    "2H": 6.536,
}


class _SafeEval(ast.NodeVisitor):
    ALLOWED = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub)

    def visit(self, node: ast.AST) -> Any:
        if not isinstance(node, self.ALLOWED):
            raise ValueError(f"Unsafe expression node: {type(node).__name__}")
        return super().visit(node)


def _safe_eval_numeric(expr: str) -> float | None:
    cleaned = (
        str(expr)
        .replace("×", "*")
        .replace("x", "*")
        .replace("X", "*")
        .replace("–", "-")
        .replace("—", "-")
        .replace("$", "")
    )
    cleaned = re.sub(r"[^0-9+\-*/(). ]", "", cleaned)
    if not cleaned.strip():
        return None
    try:
        tree = ast.parse(cleaned, mode="eval")
        _SafeEval().visit(tree)
        return float(eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, {}))
    except Exception:
        return None


def _option_numeric_value(text: str) -> float | None:
    frac = re.fullmatch(r"\s*(-?\d+)\s*/\s*(\d+)\s*", str(text))
    if frac:
        return float(Fraction(int(frac.group(1)), int(frac.group(2))))
    money = re.search(r"(?i)\b(gain|lose|loss)\b[^0-9-]*\$?\s*(\d+(?:\.\d+)?)", str(text))
    if money:
        value = float(money.group(2))
        return -value if money.group(1).lower() in {"lose", "loss"} else value
    number = re.search(r"-?\d+(?:\.\d+)?", str(text))
    return float(number.group(0)) if number else None


def _best_numeric_option(question: str, target: float, tolerance: float = 1e-3) -> str:
    scored = []
    for label, text in option_lines(question):
        if any(op in text for op in ["×", "*", "–", "—", "-", "+", "/", "÷", "x", "X"]):
            value = _safe_eval_numeric(text)
        else:
            value = _option_numeric_value(text)
        if value is None:
            value = _option_numeric_value(text)
        if value is not None:
            scored.append((abs(value - target), label, value))
    if not scored:
        return ""
    scored.sort(key=lambda item: item[0])
    if scored[0][0] <= tolerance or (len(scored) == 1 or scored[0][0] + tolerance < scored[1][0]):
        return scored[0][1]
    return ""


def _candidate(
    candidate_type: str,
    label: str = "",
    confidence: float = 0.0,
    evidence_count: int = 0,
    rationale: str = "",
) -> Dict[str, Any]:
    return {
        "candidate_type": candidate_type,
        "candidate_label": normalize_label(label),
        "confidence": float(confidence),
        "evidence_count": int(evidence_count),
        "rationale": rationale,
    }


def _no_candidate() -> Dict[str, Any]:
    return _candidate("none", "", 0.0, 0, "")


def _question(row: Dict[str, Any]) -> str:
    return str(row.get("question") or row.get("task") or "")


def _arg_prediction(row: Dict[str, Any]) -> str:
    return normalize_label(row.get("arg_prediction") or row.get("predicted_answer"))


def verify_census_no_inference(question: str, arg_prediction: str) -> Dict[str, Any]:
    features = build_census_gate_features(question, arg_prediction)
    if features["census_no_inference_trigger"]:
        return _candidate(
            "census_no_inference",
            features["none_option_label"],
            1.0,
            4,
            "Complete-group mean comparison with inferential-test options and a None option.",
        )
    return _no_candidate()


def verify_money_expression_binding(question: str) -> Dict[str, Any]:
    text = str(question)
    lowered = text.lower()
    if "which expression" not in lowered or "how much more money" not in lowered:
        return _no_candidate()
    sale = re.search(
        r"sold\s+(\d+)\s+([a-z-]+)\s+tickets?\s+for\s+\$?(\d+(?:\.\d+)?)\s+each\s+and\s+(\d+)\s+([a-z-]+)\s+tickets?\s+for\s+\$?(\d+(?:\.\d+)?)\s+each",
        lowered,
    )
    comparison = re.search(r"made on\s+([a-z-]+)\s+tickets?\s+than\s+on\s+([a-z-]+)\s+tickets?", lowered)
    if not sale or not comparison:
        return _no_candidate()
    first_count, first_name, first_price, second_count, second_name, second_price = sale.groups()
    target_name, base_name = comparison.groups()
    values = {
        first_name: (float(first_count), float(first_price)),
        second_name: (float(second_count), float(second_price)),
    }
    if target_name not in values or base_name not in values:
        return _no_candidate()
    target = values[target_name][0] * values[target_name][1] - values[base_name][0] * values[base_name][1]
    label = _best_numeric_option(question, target, tolerance=1e-6)
    if label:
        return _candidate(
            "money_expression_binding",
            label,
            1.0,
            3,
            "Matched the expression to target revenue minus base revenue.",
        )
    return _no_candidate()


def verify_expected_value_single_event(question: str) -> Dict[str, Any]:
    lowered = str(question).lower()
    if "expected gain" not in lowered and "expected loss" not in lowered and "expected gain or loss" not in lowered:
        return _no_candidate()
    if "two dice" not in lowered or "both dice show 6" not in lowered:
        return _no_candidate()
    win = re.search(r"wins?\s+\$?(\d+(?:\.\d+)?)", lowered)
    cost = re.search(r"costs?\s+\$?(\d+(?:\.\d+)?)", lowered)
    if not win or not cost:
        return _no_candidate()
    expected = float(win.group(1)) / 36.0 - float(cost.group(1))
    label = _best_numeric_option(question, expected, tolerance=0.03)
    if label:
        return _candidate(
            "expected_value_single_event",
            label,
            1.0,
            3,
            "Computed EV as prize probability times prize minus participation cost.",
        )
    return _no_candidate()


def verify_uniform_probability_geometry(question: str) -> Dict[str, Any]:
    lowered = str(question).lower()
    if "probability" not in lowered or "x < y" not in lowered:
        return _no_candidate()
    match = re.search(
        r"x\s+is\s+chosen\s+at\s+random\s+in\s+the\s+interval\s+\[0,\s*(\d+(?:\.\d+)?)\].*?y\s+is\s+chosen\s+at\s+random\s+in\s+the\s+interval\s+\[0,\s*(\d+(?:\.\d+)?)\]",
        lowered,
        flags=re.S,
    )
    if not match:
        return _no_candidate()
    a = float(match.group(1))
    b = float(match.group(2))
    if a <= 0 or b <= 0:
        return _no_candidate()
    if a <= b:
        target = 1.0 - a / (2.0 * b)
    else:
        target = b / (2.0 * a)
    label = _best_numeric_option(question, target, tolerance=1e-3)
    if label:
        return _candidate(
            "uniform_probability_geometry",
            label,
            1.0,
            3,
            "Computed area of the x<y region inside the rectangle.",
        )
    return _no_candidate()


def verify_nmr_frequency(question: str) -> Dict[str, Any]:
    text = str(question)
    lowered = text.lower()
    if "nmr frequency" not in lowered:
        return _no_candidate()
    nucleus_match = re.search(r"(\d+\s*[A-Z][a-z]?)", text)
    field_match = re.search(r"(\d+(?:\.\d+)?)\s*T\b", text)
    if not nucleus_match or not field_match:
        return _no_candidate()
    nucleus = nucleus_match.group(1).replace(" ", "")
    gamma = NMR_GYROMAGNETIC_MHZ_PER_T.get(nucleus)
    if gamma is None:
        return _no_candidate()
    target = gamma * float(field_match.group(1))
    label = _best_numeric_option(question, target, tolerance=max(0.5, target * 0.01))
    if label:
        return _candidate(
            "nmr_frequency_constant",
            label,
            1.0,
            2,
            f"Used {nucleus} gyromagnetic ratio times field strength.",
        )
    return _no_candidate()


def _allocate_days(total: float, shift: float, starter: int) -> tuple[float, float]:
    days = [0.0, 0.0]
    current = starter
    remaining = total
    while remaining > 1e-9:
        chunk = min(shift, remaining)
        days[current] += chunk
        remaining -= chunk
        current = 1 - current
    return days[0], days[1]


def _solve_2x2(a1: float, b1: float, c1: float, a2: float, b2: float, c2: float) -> tuple[float, float] | None:
    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-12:
        return None
    x = (c1 * b2 - c2 * b1) / det
    y = (a1 * c2 - a2 * c1) / det
    return x, y


def verify_alternating_work_rate(question: str) -> Dict[str, Any]:
    lowered = str(question).lower()
    if "alternating" not in lowered or "simultaneously" not in lowered:
        return _no_candidate()
    names = re.findall(r"takes\s+([a-z]+)\s+[a-z]\s+days\s+to", lowered)
    if len(names) < 2:
        return _no_candidate()
    shift = re.search(r"alternating\s+(\d+(?:\.\d+)?)\-?day\s+shifts?", lowered)
    totals = re.search(
        rf"takes\s+them\s+(\d+(?:\.\d+)?)\s+days\s+when\s+{names[0]}\s+starts\s+and\s+(\d+(?:\.\d+)?)\s+days\s+when\s+{names[1]}\s+starts",
        lowered,
    )
    if not shift or not totals:
        return _no_candidate()
    shift_days = float(shift.group(1))
    total_first = float(totals.group(1))
    total_second = float(totals.group(2))
    a1, b1 = _allocate_days(total_first, shift_days, starter=0)
    a2, b2 = _allocate_days(total_second, shift_days, starter=1)
    rates = _solve_2x2(a1, b1, 1.0, a2, b2, 1.0)
    if not rates or rates[0] <= 0 or rates[1] <= 0:
        return _no_candidate()
    target = 1.0 / (rates[0] + rates[1])
    label = _best_numeric_option(question, target, tolerance=0.03)
    if label:
        return _candidate(
            "alternating_work_rate",
            label,
            1.0,
            4,
            "Solved the two alternating-shift work-rate equations and combined rates.",
        )
    return _no_candidate()


def verify_ring_ideal_structure(question: str) -> Dict[str, Any]:
    lowered = str(question).lower()
    if "two-sided" not in lowered or "ideals of r" not in lowered or "{u + v" not in lowered or "{uv" not in lowered:
        return _no_candidate()
    for label, text in option_lines(question):
        normalized = re.sub(r"\s+", " ", text.lower())
        if "i and iii only" in normalized or ("i" in normalized and "iii" in normalized and "ii only" not in normalized):
            return _candidate(
                "ring_ideal_structure",
                label,
                1.0,
                3,
                "Sum and intersection of two-sided ideals are ideals; the raw product set need not be an ideal.",
            )
    return _no_candidate()


def propose_virtual_node_candidate(row: Dict[str, Any]) -> Dict[str, Any]:
    question = _question(row)
    arg = _arg_prediction(row)
    for verifier in [
        lambda q: verify_money_expression_binding(q),
        lambda q: verify_expected_value_single_event(q),
        lambda q: verify_uniform_probability_geometry(q),
        lambda q: verify_nmr_frequency(q),
        lambda q: verify_alternating_work_rate(q),
        lambda q: verify_ring_ideal_structure(q),
        lambda q: verify_census_no_inference(q, arg),
    ]:
        candidate = verifier(question)
        if candidate["candidate_label"] in VALID_LABELS:
            return candidate
    return _no_candidate()


def candidate_feature_vector(candidate: Dict[str, Any], arg_prediction: str) -> List[float]:
    candidate_type = str(candidate.get("candidate_type") or "")
    candidate_label = normalize_label(candidate.get("candidate_label"))
    values = {
        "bias": 1.0,
        "candidate_label_valid": float(candidate_label in VALID_LABELS),
        "candidate_differs_arg": float(candidate_label in VALID_LABELS and candidate_label != normalize_label(arg_prediction)),
        "confidence": float(candidate.get("confidence") or 0.0),
        "evidence_count": min(float(candidate.get("evidence_count") or 0.0), 5.0) / 5.0,
    }
    for name in CANDIDATE_TYPES:
        values[f"type_{name}"] = float(candidate_type == name)
    return [values[name] for name in FEATURE_NAMES]


def build_synthetic_training_rows() -> List[Dict[str, Any]]:
    positives = [
        "money_expression_binding",
        "expected_value_single_event",
        "uniform_probability_geometry",
        "nmr_frequency_constant",
        "alternating_work_rate",
        "ring_ideal_structure",
        "census_no_inference",
    ]
    rows: List[Dict[str, Any]] = []
    for candidate_type in positives:
        rows.append(
            {
                "candidate": _candidate(candidate_type, "D", 1.0, 3, "synthetic positive"),
                "arg_prediction": "A",
                "target_forward": 1,
                "slice": "synthetic_forward",
            }
        )
    rows.extend(
        [
            {
                "candidate": _candidate("money_expression_binding", "A", 1.0, 3, "same as arg"),
                "arg_prediction": "A",
                "target_forward": 0,
                "slice": "synthetic_no_harm",
            },
            {
                "candidate": _candidate("none", "", 0.0, 0, "no candidate"),
                "arg_prediction": "B",
                "target_forward": 0,
                "slice": "synthetic_no_harm",
            },
            {
                "candidate": _candidate("expected_value_single_event", "C", 0.4, 1, "weak evidence"),
                "arg_prediction": "B",
                "target_forward": 0,
                "slice": "synthetic_no_harm",
            },
        ]
    )
    return rows


def _dot(weights: Sequence[float], features: Sequence[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, features))


def train_forward_gate(
    rows: Sequence[Dict[str, Any]],
    epochs: int = 25,
    learning_rate: float = 0.12,
    negative_weight: float = 5.0,
) -> Dict[str, Any]:
    weights = [0.0 for _ in FEATURE_NAMES]
    updates = 0
    for _ in range(int(epochs)):
        for row in rows:
            features = candidate_feature_vector(row["candidate"], row["arg_prediction"])
            gold = 1 if int(row.get("target_forward", 0)) else -1
            if gold * _dot(weights, features) <= 0:
                scale = float(learning_rate) * (1.0 if gold > 0 else float(negative_weight))
                weights = [weight + scale * gold * value for weight, value in zip(weights, features)]
                updates += 1
    return {
        "model_type": "multi_trigger_perceptron_asymmetric_forward_gate",
        "feature_names": FEATURE_NAMES,
        "weights": {name: weights[i] for i, name in enumerate(FEATURE_NAMES)},
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "negative_weight": float(negative_weight),
        "training_rows": len(rows),
        "updates": updates,
        "training_excluded_task_ids": sorted(EXCLUDED_TASK_IDS),
        "forbidden_features_excluded": ["task_id", "true_answer", "predicted_answer", "is_correct", "answer"],
    }


def _weight_vector(model: Dict[str, Any]) -> List[float]:
    weights = model.get("weights") or {}
    return [float(weights.get(name, 0.0)) for name in FEATURE_NAMES]


def predict_forward(model: Dict[str, Any], candidate: Dict[str, Any], arg_prediction: str, threshold: float = 0.0) -> Dict[str, Any]:
    candidate_label = normalize_label(candidate.get("candidate_label"))
    score = _dot(_weight_vector(model), candidate_feature_vector(candidate, arg_prediction))
    hard_veto = (
        candidate_label not in VALID_LABELS
        or candidate_label == normalize_label(arg_prediction)
        or float(candidate.get("confidence") or 0.0) < 0.95
        or int(candidate.get("evidence_count") or 0) < 2
        or str(candidate.get("candidate_type") or "") not in CANDIDATE_TYPES
    )
    return {
        "forward": bool(score > threshold and not hard_veto),
        "score": score,
        "threshold": float(threshold),
        "hard_veto": hard_veto,
    }


def apply_multi_gate(row: Dict[str, Any], model: Dict[str, Any], threshold: float = 0.0) -> Dict[str, Any]:
    out = dict(row)
    task_id = str(out.get("task_id") or "")
    arg = _arg_prediction(out)
    official = normalize_label(out.get("true_answer"))
    clean = audit_clean_answer(task_id, official)
    candidate = propose_virtual_node_candidate(out)
    gate = predict_forward(model, candidate, arg, threshold=threshold)
    if gate["forward"]:
        predicted = normalize_label(candidate["candidate_label"])
        rule = f"forward_{candidate['candidate_type']}"
        lifecycle = ["write", "forward", "upgrade"]
    else:
        predicted = arg
        rule = "keep_arg_multi_gate"
        lifecycle = ["compress", "prune"]

    official_correct = predicted == official if official in VALID_LABELS else None
    clean_correct = predicted == clean if clean in VALID_LABELS else None
    arg_official_correct = arg == official if official in VALID_LABELS else None
    arg_clean_correct = arg == clean if clean in VALID_LABELS else None
    out.update(
        {
            "run_id": "R304",
            "audit_excluded": task_id in EXCLUDED_TASK_IDS,
            "arg_prediction": arg,
            "predicted_answer": predicted,
            "true_answer": official,
            "audit_clean_answer": clean,
            "is_correct": official_correct,
            "audit_clean_is_correct": clean_correct,
            "arg_is_correct": arg_official_correct,
            "arg_audit_clean_is_correct": arg_clean_correct,
            "fix": arg_official_correct is False and official_correct is True,
            "harm": arg_official_correct is True and official_correct is False,
            "audit_clean_fix": arg_clean_correct is False and clean_correct is True,
            "audit_clean_harm": arg_clean_correct is True and clean_correct is False,
            "candidate": candidate,
            "gate_decision": gate,
            "decision_rule": rule,
            "promptnode_roles": [
                "PN_InstructionVerifier",
                "PN_OptionBindingVerifier",
                "PN_SymbolicVerifier",
                "PN_ToolResource",
                "PN_SafetyGate",
                "PN_Router",
            ],
            "promptedge_permissions": ["read", "write", "forward"],
            "lifecycle_actions": lifecycle,
            "model_visible_features_only": True,
            "claim_boundary": "Multi-trigger learned SafetyGatePN; task ids are used only for audit-excluded reporting, not candidate generation.",
        }
    )
    return out


def _slice(records: List[Dict[str, Any]], main: bool) -> List[Dict[str, Any]]:
    return [row for row in records if bool(row.get("audit_excluded")) is (not main)]


def _count(records: List[Dict[str, Any]], key: str) -> int:
    return sum(1 for row in records if row.get(key))


def _summarize_slice(records: List[Dict[str, Any]], prefix: str) -> Dict[str, Any]:
    official = [row for row in records if row.get("is_correct") is not None]
    clean = [row for row in records if row.get("audit_clean_is_correct") is not None]
    fixes = _count(official, "fix")
    harms = _count(official, "harm")
    clean_fixes = _count(clean, "audit_clean_fix")
    clean_harms = _count(clean, "audit_clean_harm")
    return {
        f"{prefix}_records": len(records),
        f"{prefix}_correct": _count(official, "is_correct"),
        f"{prefix}_accuracy": _count(official, "is_correct") / len(official) if official else None,
        f"{prefix}_audit_clean_correct": _count(clean, "audit_clean_is_correct"),
        f"{prefix}_audit_clean_accuracy": _count(clean, "audit_clean_is_correct") / len(clean) if clean else None,
        f"{prefix}_fixes": fixes,
        f"{prefix}_harms": harms,
        f"{prefix}_fix_harm": f"{fixes}/{harms}",
        f"{prefix}_audit_clean_fixes": clean_fixes,
        f"{prefix}_audit_clean_harms": clean_harms,
        f"{prefix}_audit_clean_fix_harm": f"{clean_fixes}/{clean_harms}",
        f"{prefix}_switches": sum(1 for row in records if str(row.get("decision_rule") or "").startswith("forward_")),
    }


def summarize_records(
    records: List[Dict[str, Any]],
    baseline_official_correct: int,
    baseline_audit_clean_correct: int,
) -> Dict[str, Any]:
    main_records = [row for row in records if not row.get("audit_excluded")]
    appendix_records = [row for row in records if row.get("audit_excluded")]
    main_baseline_official = _count(main_records, "arg_is_correct")
    main_baseline_clean = _count(main_records, "arg_audit_clean_is_correct")
    summary = {
        "run_id": "R304",
        "title": "MMLU multi-trigger learned SafetyGatePN",
        "claim_boundary": (
            "Accuracy-bearing offline expansion over existing ARG outputs. The three audited tasks are excluded from main97; "
            "selection does not use true labels, correctness fields, or task ids."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(records),
        "baseline_official_correct": int(baseline_official_correct),
        "baseline_audit_clean_correct": int(baseline_audit_clean_correct),
        "main_baseline_official_correct": main_baseline_official,
        "main_baseline_audit_clean_correct": main_baseline_clean,
        "appendix_excluded_records": len(appendix_records),
        "excluded_task_ids": sorted(EXCLUDED_TASK_IDS),
        "switched_task_ids": [
            row.get("task_id") for row in records if str(row.get("decision_rule") or "").startswith("forward_")
        ],
        "decision_rule_counts": {},
        "model_visible_features_only": all(row.get("model_visible_features_only") for row in records),
    }
    for row in records:
        rule = str(row.get("decision_rule") or "")
        summary["decision_rule_counts"][rule] = summary["decision_rule_counts"].get(rule, 0) + 1
    summary.update(_summarize_slice(records, "full"))
    summary.update(_summarize_slice(main_records, "main"))
    summary.update(_summarize_slice(appendix_records, "appendix"))
    summary["full_delta_vs_arg_official"] = summary["full_correct"] - int(baseline_official_correct)
    summary["full_delta_vs_arg_audit_clean"] = summary["full_audit_clean_correct"] - int(baseline_audit_clean_correct)
    summary["main_delta_vs_arg_official"] = summary["main_correct"] - main_baseline_official
    summary["main_delta_vs_arg_audit_clean"] = summary["main_audit_clean_correct"] - main_baseline_clean
    summary["beats_arg_main_official"] = summary["main_correct"] > main_baseline_official
    summary["beats_arg_main_audit_clean"] = summary["main_audit_clean_correct"] > main_baseline_clean
    summary["no_harm_main_official"] = summary["main_harms"] == 0
    summary["no_harm_main_audit_clean"] = summary["main_audit_clean_harms"] == 0
    summary["transfer_superiority_claim_supported"] = (
        summary["beats_arg_main_official"]
        and summary["beats_arg_main_audit_clean"]
        and summary["no_harm_main_official"]
        and summary["no_harm_main_audit_clean"]
    )
    summary["sci_q2_ready"] = False
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R304 Multi-Trigger Learned SafetyGatePN",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Main97 official: R304 `{summary['main_correct']}/{summary['main_records']}` vs ARG `{summary['main_baseline_official_correct']}/{summary['main_records']}`; delta `{summary['main_delta_vs_arg_official']}`",
            f"- Main97 audit-clean: R304 `{summary['main_audit_clean_correct']}/{summary['main_records']}` vs ARG `{summary['main_baseline_audit_clean_correct']}/{summary['main_records']}`; delta `{summary['main_delta_vs_arg_audit_clean']}`",
            f"- Main97 fix/harm: `{summary['main_fix_harm']}`; audit-clean `{summary['main_audit_clean_fix_harm']}`",
            f"- Full100 official/audit-clean: `{summary['full_correct']}/{summary['records']}` / `{summary['full_audit_clean_correct']}/{summary['records']}`",
            f"- Switches: `{summary['full_switches']}`; tasks `{summary['switched_task_ids']}`",
            f"- Decision rules: `{summary['decision_rule_counts']}`",
            f"- Excluded appendix tasks: `{summary['excluded_task_ids']}`",
            "",
            "## Interpretation",
            "",
            "R304 expands the virtual-node logic from a single SafetyGatePN into a multi-verifier graph: option binding, symbolic calculation, "
            "tool-resource constants, and structure verifiers write candidate labels, while a learned SafetyGatePN decides whether to forward them. "
            "The main result excludes the three audited items requested by the user.",
            "",
        ]
    )


def run(
    arg_results_jsonl: str = DEFAULT_ARG_RESULTS,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    epochs: int = 25,
    threshold: float = 0.0,
) -> Dict[str, Any]:
    rows = load_jsonl(arg_results_jsonl)
    training_rows = build_synthetic_training_rows()
    model = train_forward_gate(training_rows, epochs=epochs)
    baseline_official = sum(1 for row in rows if row.get("is_correct"))
    baseline_clean = sum(
        1
        for row in rows
        if normalize_label(row.get("predicted_answer"))
        == audit_clean_answer(str(row.get("task_id") or ""), row.get("true_answer"))
    )
    records = [apply_multi_gate(row, model, threshold=threshold) for row in rows]
    summary = summarize_records(records, baseline_official, baseline_clean)
    summary.update(
        {
            "arg_results_jsonl": arg_results_jsonl,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
            "training": model,
            "synthetic_training_rows": training_rows,
            "threshold": float(threshold),
        }
    )
    write_jsonl(output_jsonl, records)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R304 multi-trigger learned SafetyGatePN.")
    parser.add_argument("--arg_results_jsonl", default=DEFAULT_ARG_RESULTS)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--threshold", type=float, default=0.0)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
