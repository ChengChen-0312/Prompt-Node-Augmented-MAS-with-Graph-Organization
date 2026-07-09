from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r357_learned_graph_policy_training_manifest.jsonl"
DEFAULT_PREDICTIONS_JSONL = "experiment/mmlu/run_logs/mmlu_r360_source_invariant_graph_policy_predictions.jsonl"
DEFAULT_MODEL_JSON = "experiment/mmlu/run_logs/mmlu_r360_source_invariant_graph_policy_model.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r360_source_invariant_graph_policy_retraining_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r360_source_invariant_graph_policy_retraining_report.md"
DECISION_THRESHOLD = 0.7


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    p = _repo_path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _clean_features(features: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in features.items() if not key.startswith("source_run")}


def _split_rows(rows: List[Dict[str, Any]], split: str) -> List[Dict[str, Any]]:
    return [row for row in rows if row.get("split") == split]


def _metrics(y_true: List[int], y_score: List[float], threshold: float) -> Dict[str, Any]:
    y_pred = [int(score >= threshold) for score in y_score]
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 6) if y_true else 0.0,
        "precision": round(float(precision), 6),
        "recall": round(float(recall), 6),
        "f1": round(float(f1), 6),
        "confusion_matrix_labels_0_1": cm,
        "false_positives": int(cm[0][1]),
        "false_negatives": int(cm[1][0]),
        "predicted_positive": int(sum(y_pred)),
        "true_positive_targets": int(sum(y_true)),
    }


def _feature_names_by_weight(vectorizer: DictVectorizer, model: LogisticRegression) -> Tuple[List[str], List[str], Dict[str, float]]:
    names = list(vectorizer.get_feature_names_out())
    weights = list(model.coef_[0])
    weight_map = {name: round(float(weight), 6) for name, weight in zip(names, weights)}
    positive = [names[i] for i in sorted(range(len(weights)), key=lambda idx: weights[idx], reverse=True)[:10]]
    negative = [names[i] for i in sorted(range(len(weights)), key=lambda idx: weights[idx])[:10]]
    return positive, negative, weight_map


def train_source_invariant_policy(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    train_rows = _split_rows(rows, "train")
    vectorizer = DictVectorizer(sparse=True)
    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=0, solver="liblinear")
    x_train = vectorizer.fit_transform([_clean_features(row["features"]) for row in train_rows])
    y_train = [int(bool(row.get("target_forward"))) for row in train_rows]
    model.fit(x_train, y_train)
    split_metrics: Dict[str, Any] = {}
    all_predictions = []
    for split in ["train", "dev", "test"]:
        subset = _split_rows(rows, split)
        x = vectorizer.transform([_clean_features(row["features"]) for row in subset])
        y = [int(bool(row.get("target_forward"))) for row in subset]
        scores = [float(value) for value in model.predict_proba(x)[:, 1]]
        split_metrics[split] = _metrics(y, scores, DECISION_THRESHOLD)
        for row, score in zip(subset, scores):
            all_predictions.append(
                {
                    "run_id": "R360",
                    "source_run": row.get("source_run"),
                    "source_ref_hash": row.get("source_ref_hash"),
                    "split": split,
                    "target_forward": bool(row.get("target_forward")),
                    "predicted_forward": bool(score >= DECISION_THRESHOLD),
                    "forward_probability": round(score, 6),
                    "promptnode_family": row.get("features", {}).get("promptnode_family", ""),
                    "target_add_node": row.get("target_add_node", ""),
                    "target_add_edge": row.get("target_add_edge", ""),
                    "target_prune": row.get("target_prune", False),
                }
            )
    top_positive, top_negative, weights = _feature_names_by_weight(vectorizer, model)
    return {
        "run_id": "R360",
        "title": "Source-invariant graph-policy retraining",
        "claim_boundary": (
            "R360 retrains the offline graph-policy gate after removing source_run features and uses a conservative "
            "0.7 forward threshold. It remains an offline feasibility step."
        ),
        "no_api": True,
        "broad_api": False,
        "model": "source_invariant_logistic_regression_liblinear_balanced",
        "source_features_removed": True,
        "decision_threshold": DECISION_THRESHOLD,
        "train_records": len(train_rows),
        "dev_records": len(_split_rows(rows, "dev")),
        "test_records": len(_split_rows(rows, "test")),
        "train_metrics": split_metrics["train"],
        "dev_metrics": split_metrics["dev"],
        "test_metrics": split_metrics["test"],
        "dev_false_positives": split_metrics["dev"]["false_positives"],
        "dev_false_negatives": split_metrics["dev"]["false_negatives"],
        "test_false_positives": split_metrics["test"]["false_positives"],
        "test_false_negatives": split_metrics["test"]["false_negatives"],
        "top_positive_features": top_positive,
        "top_negative_features": top_negative,
        "model_weights": weights,
        "predictions": all_predictions,
        "fresh_eval_preflight_authorized_next": True,
        "api_execution_authorized_next": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R361_goal_audit_after_source_invariant_policy",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R360 Source-Invariant Graph-Policy Retraining",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Decision threshold: `{summary['decision_threshold']}`",
            f"- Dev FP/FN: `{summary['dev_false_positives']}/{summary['dev_false_negatives']}`",
            f"- Test FP/FN: `{summary['test_false_positives']}/{summary['test_false_negatives']}`",
            f"- Top positive features: `{summary['top_positive_features'][:5]}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    predictions_jsonl: str = DEFAULT_PREDICTIONS_JSONL,
    model_json: str = DEFAULT_MODEL_JSON,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = train_source_invariant_policy(manifest_jsonl=manifest_jsonl)
    predictions = summary.pop("predictions")
    model_payload = {
        "model": summary["model"],
        "decision_threshold": summary["decision_threshold"],
        "top_positive_features": summary["top_positive_features"],
        "top_negative_features": summary["top_negative_features"],
        "model_weights": summary["model_weights"],
    }
    summary.update(
        {
            "predictions_jsonl": predictions_jsonl,
            "model_json": model_json,
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    _write_jsonl(predictions_jsonl, predictions)
    _write_json(model_json, model_payload)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retrain R360 source-invariant graph-policy gate.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--predictions_jsonl", default=DEFAULT_PREDICTIONS_JSONL)
    parser.add_argument("--model_json", default=DEFAULT_MODEL_JSON)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
