from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r322_selector_training_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r323_selector_model_dry_run_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r323_selector_model_dry_run_report.md"
DEFAULT_PREDICTIONS_JSONL = "experiment/mmlu/run_logs/mmlu_r323_selector_model_dry_run_predictions.jsonl"


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
    target.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def train_structural_selector(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    train = [row for row in rows if row.get("split") == "train"]
    counts: Dict[str, Counter] = defaultdict(Counter)
    for row in train:
        family = row["features"]["promptnode_family"]
        counts[family]["positive" if row["target_forward"] else "negative"] += 1
    allowed = sorted(
        family for family, counter in counts.items() if counter["positive"] > 0 and counter["negative"] == 0
    )
    positive_confidences = [
        float(row["features"].get("candidate_confidence", 0.0))
        for row in train
        if row["target_forward"] and row["features"]["promptnode_family"] in allowed
    ]
    return {
        "model_type": "transparent_family_whitelist_selector",
        "allowed_promptnode_families": allowed,
        "min_candidate_confidence": min(positive_confidences) if positive_confidences else 1.0,
        "requires_candidate_answer_label": True,
        "forbidden_promptnode_families": sorted(family for family in counts if family not in allowed),
        "train_family_counts": {family: dict(counter) for family, counter in sorted(counts.items())},
        "forbidden_features_excluded": [
            "task_id",
            "question",
            "true_answer",
            "predicted_answer",
            "arg_prediction",
            "is_correct",
            "fix",
            "harm",
        ],
    }


def predict(policy: Dict[str, Any], row: Dict[str, Any]) -> bool:
    features = row["features"]
    return (
        features["promptnode_family"] in set(policy["allowed_promptnode_families"])
        and float(features.get("candidate_confidence", 0.0)) >= float(policy["min_candidate_confidence"])
        and bool(features.get("candidate_has_answer_label"))
    )


def _metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    correct = sum(1 for row in rows if row["predicted_forward"] == row["target_forward"])
    tp = sum(1 for row in rows if row["predicted_forward"] and row["target_forward"])
    fp = sum(1 for row in rows if row["predicted_forward"] and not row["target_forward"])
    fn = sum(1 for row in rows if not row["predicted_forward"] and row["target_forward"])
    positives = sum(1 for row in rows if row["target_forward"])
    predicted_pos = sum(1 for row in rows if row["predicted_forward"])
    return {
        "records": total,
        "accuracy": correct / total if total else None,
        "target_forward": positives,
        "predicted_forward": predicted_pos,
        "precision_forward": tp / (tp + fp) if (tp + fp) else 0.0,
        "recall_forward": tp / (tp + fn) if (tp + fn) else 0.0,
        "false_forward": fp,
        "missed_forward": fn,
    }


def feature_leakage_pass(rows: List[Dict[str, Any]]) -> bool:
    forbidden = {
        "task_id",
        "question",
        "true_answer",
        "predicted_answer",
        "arg_prediction",
        "is_correct",
        "fix",
        "harm",
    }
    for row in rows:
        if forbidden.intersection(row):
            return False
        if forbidden.intersection(row.get("features", {})):
            return False
    return True


def build_selector_model_summary(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    policy = train_structural_selector(rows)
    predictions = []
    for row in rows:
        pred = predict(policy, row)
        predictions.append(
            {
                "run_id": "R323",
                "source_ref_hash": row["source_ref_hash"],
                "split": row["split"],
                "dataset_family": row["dataset_family"],
                "promptnode_family": row["features"]["promptnode_family"],
                "target_forward": row["target_forward"],
                "predicted_forward": pred,
            }
        )
    by_split = {
        split: _metrics([row for row in predictions if row["split"] == split])
        for split in ["train", "dev", "test"]
    }
    return {
        "run_id": "R323",
        "title": "Selector model dry run",
        "claim_boundary": (
            "R323 trains a transparent no-API selector only on the R322 manifest. It is a feasibility dry run, not a "
            "paper claim and not an API execution authorization."
        ),
        "no_api": True,
        "broad_api": False,
        "manifest_records": len(rows),
        "learned_policy": policy,
        "metrics": by_split,
        "forwarded_warning_only_count": sum(
            1 for row in predictions if row["promptnode_family"] == "warning_only" and row["predicted_forward"]
        ),
        "feature_leakage_pass": feature_leakage_pass(rows),
        "paper_claim_authorized": False,
        "api_execution_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R324_selector_feature_ablation",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R323 Selector Model Dry Run",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Learned policy: `{summary['learned_policy']}`",
        f"- Forwarded warning-only count: `{summary['forwarded_warning_only_count']}`",
        f"- Feature leakage pass: `{summary['feature_leakage_pass']}`",
        "",
        "## Metrics",
        "",
        "| Split | Records | Accuracy | Target Forward | Predicted Forward | Precision | Recall |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for split, metric in summary["metrics"].items():
        rows.append(
            f"| `{split}` | `{metric['records']}` | `{metric['accuracy']}` | `{metric['target_forward']}` | `{metric['predicted_forward']}` | `{metric['precision_forward']}` | `{metric['recall_forward']}` |"
        )
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    predictions_jsonl: str = DEFAULT_PREDICTIONS_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    policy = train_structural_selector(rows)
    predictions = []
    for row in rows:
        pred = predict(policy, row)
        predictions.append(
            {
                "run_id": "R323",
                "source_ref_hash": row["source_ref_hash"],
                "split": row["split"],
                "dataset_family": row["dataset_family"],
                "promptnode_family": row["features"]["promptnode_family"],
                "target_forward": row["target_forward"],
                "predicted_forward": pred,
            }
        )
    summary = build_selector_model_summary(manifest_jsonl=manifest_jsonl)
    summary.update({"predictions_jsonl": predictions_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(predictions_jsonl, predictions)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R323 selector model dry run.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--predictions_jsonl", default=DEFAULT_PREDICTIONS_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
