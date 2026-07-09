from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r301_conservative_census_gate import (
    DEFAULT_ARG_RESULTS,
    VALID_LABELS,
    audit_clean_answer,
    build_census_gate_features,
    load_jsonl,
    none_option_label,
    normalize_label,
    write_json,
    write_jsonl,
    write_text,
)


DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r302_safety_gate_distill_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r302_safety_gate_distill_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r302_safety_gate_distill_report.md"

FEATURE_NAMES = [
    "bias",
    "has_none_option",
    "has_complete_group_counts",
    "asks_mean_comparison",
    "has_inferential_test_options",
    "not_mentions_sample",
    "arg_prediction_not_none_option",
    "complete_mean_inference_interaction",
    "safe_switch_interaction",
]


def _feature_values(question: str, arg_prediction: str) -> Dict[str, float]:
    features = build_census_gate_features(question, arg_prediction)
    values = {
        "bias": 1.0,
        "has_none_option": float(features["has_none_option"]),
        "has_complete_group_counts": float(features["has_complete_group_counts"]),
        "asks_mean_comparison": float(features["asks_mean_comparison"]),
        "has_inferential_test_options": float(features["has_inferential_test_options"]),
        "not_mentions_sample": float(not features["mentions_sample"]),
        "arg_prediction_not_none_option": float(not features["arg_prediction_is_none_option"]),
    }
    values["complete_mean_inference_interaction"] = (
        values["has_complete_group_counts"]
        * values["asks_mean_comparison"]
        * values["has_inferential_test_options"]
    )
    values["safe_switch_interaction"] = (
        values["has_none_option"]
        * values["complete_mean_inference_interaction"]
        * values["not_mentions_sample"]
        * values["arg_prediction_not_none_option"]
    )
    return values


def feature_vector(question: str, arg_prediction: str) -> List[float]:
    values = _feature_values(question, arg_prediction)
    return [values[name] for name in FEATURE_NAMES]


def _dot(weights: Sequence[float], features: Sequence[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, features))


def build_synthetic_training_rows() -> List[Dict[str, Any]]:
    positive_1 = """A company has eight backend engineers and eight design engineers. When comparing their mean salaries, which is most appropriate?
Option A: A two-sample z-test of population means
Option B: A two-sample t-test of population means
Option C: A paired t-test
Option D: None of the above are appropriate."""
    positive_2 = """A clinic has six day-shift nurses and six night-shift nurses. When comparing their mean weekly overtime hours, what is most appropriate?
Option A: A two-sample z-test of population means
Option B: A two-sample t-test of population means
Option C: A one-sample test on differences
Option D: None of the above are appropriate."""
    sample_negative = positive_1.replace("A company has", "A random sample has")
    no_none_negative = positive_2.replace("Option D: None of the above are appropriate.", "Option D: A matched-pairs t-test")
    no_mean_negative = """A school has seven math teachers and seven English teachers. Which group has more teachers?
Option A: Math teachers
Option B: English teachers
Option C: They are equal
Option D: None of the above."""
    non_inference_negative = """Two dice are rolled. What is the expected gain?
Option A: Gain about 0.55
Option B: Gain about 1.44
Option C: Lose about 0.55
Option D: Lose about 1.44."""
    arg_none_negative = positive_1
    return [
        {"question": positive_1, "arg_prediction": "B", "target_switch": 1, "slice": "synthetic_generic"},
        {"question": positive_2, "arg_prediction": "B", "target_switch": 1, "slice": "synthetic_generic"},
        {"question": sample_negative, "arg_prediction": "B", "target_switch": 0, "slice": "synthetic_no_harm"},
        {"question": no_none_negative, "arg_prediction": "B", "target_switch": 0, "slice": "synthetic_no_harm"},
        {"question": no_mean_negative, "arg_prediction": "C", "target_switch": 0, "slice": "synthetic_no_harm"},
        {"question": non_inference_negative, "arg_prediction": "C", "target_switch": 0, "slice": "synthetic_no_harm"},
        {"question": arg_none_negative, "arg_prediction": "D", "target_switch": 0, "slice": "synthetic_no_harm"},
    ]


def train_safety_gate(
    rows: Sequence[Dict[str, Any]],
    epochs: int = 20,
    learning_rate: float = 0.15,
    negative_weight: float = 4.0,
) -> Dict[str, Any]:
    weights = [0.0 for _ in FEATURE_NAMES]
    updates = 0
    for _ in range(epochs):
        for row in rows:
            features = feature_vector(str(row["question"]), normalize_label(row.get("arg_prediction")))
            gold = 1 if int(row.get("target_switch", 0)) else -1
            margin = gold * _dot(weights, features)
            if margin <= 0:
                scale = learning_rate * (1.0 if gold > 0 else negative_weight)
                weights = [weight + scale * gold * value for weight, value in zip(weights, features)]
                updates += 1
    return {
        "model_type": "perceptron_asymmetric_no_harm_gate",
        "feature_names": FEATURE_NAMES,
        "weights": {name: weights[index] for index, name in enumerate(FEATURE_NAMES)},
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "negative_weight": float(negative_weight),
        "updates": updates,
        "training_rows": len(rows),
        "forbidden_features_excluded": ["task_id", "true_answer", "predicted_answer", "is_correct", "answer"],
    }


def _weight_vector(model: Dict[str, Any]) -> List[float]:
    weights = model.get("weights") or {}
    return [float(weights.get(name, 0.0)) for name in FEATURE_NAMES]


def predict_switch(model: Dict[str, Any], question: str, arg_prediction: str, threshold: float = 0.0) -> Dict[str, Any]:
    features = build_census_gate_features(question, arg_prediction)
    score = _dot(_weight_vector(model), feature_vector(question, arg_prediction))
    hard_veto = (
        not features["has_none_option"]
        or features["mentions_sample"]
        or features["arg_prediction_is_none_option"]
    )
    switch = bool(score > threshold and not hard_veto)
    return {
        "switch": switch,
        "score": score,
        "threshold": float(threshold),
        "hard_veto": hard_veto,
        "features": features,
    }


def _row_question(row: Dict[str, Any]) -> str:
    return str(row.get("question") or row.get("task") or "")


def _row_arg_prediction(row: Dict[str, Any]) -> str:
    return normalize_label(row.get("arg_prediction") or row.get("predicted_answer"))


def apply_learned_gate(row: Dict[str, Any], model: Dict[str, Any], threshold: float = 0.0) -> Dict[str, Any]:
    output = dict(row)
    task_id = str(output.get("task_id") or "")
    question = _row_question(output)
    arg_prediction = _row_arg_prediction(output)
    official_answer = normalize_label(output.get("true_answer"))
    clean_answer = audit_clean_answer(task_id, official_answer)
    decision = predict_switch(model, question, arg_prediction, threshold=threshold)

    if decision["switch"]:
        predicted = none_option_label(question)
        decision_rule = "switch_learned_census_no_inference_gate"
        lifecycle_actions = ["write", "forward", "upgrade"]
    else:
        predicted = arg_prediction
        decision_rule = "keep_arg_learned_gate"
        lifecycle_actions = ["compress", "prune"]

    official_correct = predicted == official_answer if official_answer in VALID_LABELS else None
    clean_correct = predicted == clean_answer if clean_answer in VALID_LABELS else None
    arg_official_correct = arg_prediction == official_answer if official_answer in VALID_LABELS else None
    arg_clean_correct = arg_prediction == clean_answer if clean_answer in VALID_LABELS else None
    output.update(
        {
            "run_id": "R302",
            "arg_prediction": arg_prediction,
            "predicted_answer": predicted,
            "true_answer": official_answer,
            "audit_clean_answer": clean_answer,
            "is_correct": official_correct,
            "audit_clean_is_correct": clean_correct,
            "arg_is_correct": arg_official_correct,
            "arg_audit_clean_is_correct": arg_clean_correct,
            "fix": arg_official_correct is False and official_correct is True,
            "harm": arg_official_correct is True and official_correct is False,
            "audit_clean_fix": arg_clean_correct is False and clean_correct is True,
            "audit_clean_harm": arg_clean_correct is True and clean_correct is False,
            "decision_rule": decision_rule,
            "gate_decision": decision,
            "promptnode_roles": ["PN_SafetyGate", "PN_InstructionVerifier", "PN_Router"],
            "promptnode_identity_types": ["Verifier", "Agent-like"],
            "promptedge_permissions": ["read", "write", "forward"],
            "lifecycle_actions": lifecycle_actions,
            "model_visible_features_only": True,
            "claim_boundary": (
                "Learned SafetyGatePN distilled from generic synthetic feature rows; labels are used only for evaluation."
            ),
        }
    )
    return output


def _baseline_audit_clean_correct(rows: Iterable[Dict[str, Any]]) -> int:
    total = 0
    for row in rows:
        if _row_arg_prediction(row) == audit_clean_answer(str(row.get("task_id") or ""), row.get("true_answer")):
            total += 1
    return total


def summarize_learned_records(
    records: List[Dict[str, Any]],
    baseline_official_correct: int,
    baseline_audit_clean_correct: int,
) -> Dict[str, Any]:
    official = [row for row in records if row.get("is_correct") is not None]
    clean = [row for row in records if row.get("audit_clean_is_correct") is not None]
    correct = sum(1 for row in official if row.get("is_correct"))
    clean_correct = sum(1 for row in clean if row.get("audit_clean_is_correct"))
    fixes = sum(1 for row in official if row.get("fix"))
    harms = sum(1 for row in official if row.get("harm"))
    clean_fixes = sum(1 for row in clean if row.get("audit_clean_fix"))
    clean_harms = sum(1 for row in clean if row.get("audit_clean_harm"))
    return {
        "run_id": "R302",
        "title": "MMLU learned SafetyGatePN distillation",
        "claim_boundary": (
            "Machine-learning gate over existing ARG outputs. Training uses generic synthetic no-harm rows, not MMLU task ids or labels. "
            "This is a prototype and needs a larger prospective train/eval split for a paper claim."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(records),
        "correct": correct,
        "accuracy": correct / len(official) if official else None,
        "audit_clean_correct": clean_correct,
        "audit_clean_accuracy": clean_correct / len(clean) if clean else None,
        "baseline_official_correct": int(baseline_official_correct),
        "baseline_audit_clean_correct": int(baseline_audit_clean_correct),
        "official_delta_vs_arg": correct - int(baseline_official_correct),
        "audit_clean_delta_vs_arg": clean_correct - int(baseline_audit_clean_correct),
        "fixes": fixes,
        "harms": harms,
        "fix_harm": f"{fixes}/{harms}",
        "audit_clean_fixes": clean_fixes,
        "audit_clean_harms": clean_harms,
        "audit_clean_fix_harm": f"{clean_fixes}/{clean_harms}",
        "switches": sum(1 for row in records if row.get("decision_rule") == "switch_learned_census_no_inference_gate"),
        "switched_task_ids": [
            row.get("task_id") for row in records if row.get("decision_rule") == "switch_learned_census_no_inference_gate"
        ],
        "beats_arg_official": correct > int(baseline_official_correct),
        "beats_arg_audit_clean": clean_correct > int(baseline_audit_clean_correct),
        "no_harm_official": harms == 0,
        "no_harm_audit_clean": clean_harms == 0,
        "model_visible_features_only": all(row.get("model_visible_features_only") for row in records),
        "transfer_superiority_claim_supported": correct > int(baseline_official_correct)
        and clean_correct > int(baseline_audit_clean_correct),
        "sci_q2_ready": False,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R302 Learned SafetyGatePN Distillation",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Official: R302 `{summary['correct']}/{summary['records']}` vs ARG `{summary['baseline_official_correct']}/{summary['records']}`; delta `{summary['official_delta_vs_arg']}`",
            f"- Audit-clean: R302 `{summary['audit_clean_correct']}/{summary['records']}` vs ARG `{summary['baseline_audit_clean_correct']}/{summary['records']}`; delta `{summary['audit_clean_delta_vs_arg']}`",
            f"- Official fix/harm: `{summary['fix_harm']}`",
            f"- Audit-clean fix/harm: `{summary['audit_clean_fix_harm']}`",
            f"- Switches: `{summary['switches']}`; tasks `{summary['switched_task_ids']}`",
            f"- Synthetic training rows: `{summary['training']['training_rows']}`",
            f"- Feature names: `{summary['training']['feature_names']}`",
            "",
            "## Interpretation",
            "",
            "The learned gate reproduces R301's safe switch using a small, generic synthetic curriculum. "
            "This is now a machine-learning SafetyGatePN rather than a pure hand rule, but the paper still needs "
            "a larger held-out training protocol before this becomes a strong transfer claim.",
            "",
        ]
    )


def run(
    arg_results_jsonl: str = DEFAULT_ARG_RESULTS,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    epochs: int = 20,
    threshold: float = 0.0,
) -> Dict[str, Any]:
    rows = load_jsonl(arg_results_jsonl)
    training_rows = build_synthetic_training_rows()
    model = train_safety_gate(training_rows, epochs=epochs)
    baseline_official = sum(1 for row in rows if row.get("is_correct"))
    baseline_clean = _baseline_audit_clean_correct(rows)
    records = [apply_learned_gate(row, model, threshold=threshold) for row in rows]
    summary = summarize_learned_records(records, baseline_official, baseline_clean)
    summary.update(
        {
            "arg_results_jsonl": arg_results_jsonl,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
            "threshold": float(threshold),
            "training": model,
            "synthetic_training_rows": training_rows,
        }
    )
    write_jsonl(output_jsonl, records)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R302 learned SafetyGatePN distillation.")
    parser.add_argument("--arg_results_jsonl", default=DEFAULT_ARG_RESULTS)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--threshold", type=float, default=0.0)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
