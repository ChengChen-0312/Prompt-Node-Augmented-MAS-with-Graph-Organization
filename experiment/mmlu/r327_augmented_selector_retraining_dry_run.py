from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r323_selector_model_dry_run import _load_jsonl, _metrics


DEFAULT_AUGMENTED_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r325_selector_augmented_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r327_augmented_selector_retraining_dry_run_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r327_augmented_selector_retraining_dry_run_report.md"
DEFAULT_PREDICTIONS_JSONL = "experiment/mmlu/run_logs/mmlu_r327_augmented_selector_retraining_dry_run_predictions.jsonl"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


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


def train_augmented_selector(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    train = [row for row in rows if row.get("split") == "train"]
    counts: Dict[str, Counter] = defaultdict(Counter)
    for row in train:
        family = row["features"]["promptnode_family"]
        counts[family]["positive" if row["target_forward"] else "negative"] += 1
    allowed = sorted(
        family for family, counter in counts.items() if counter["positive"] > 0 and counter["negative"] == 0
    )
    return {
        "model_type": "augmented_promptedge_aware_family_selector",
        "allowed_promptnode_families": allowed,
        "min_candidate_confidence": 0.95,
        "requires_candidate_answer_label": True,
        "requires_promptedge_text_present": True,
        "forbidden_promptnode_families": sorted(family for family in counts if family not in allowed),
        "train_family_counts": {family: dict(counter) for family, counter in sorted(counts.items())},
    }


def predict_augmented(policy: Dict[str, Any], row: Dict[str, Any]) -> bool:
    features = row["features"]
    return (
        features["promptnode_family"] in set(policy["allowed_promptnode_families"])
        and float(features.get("candidate_confidence", 0.0)) >= float(policy["min_candidate_confidence"])
        and bool(features.get("candidate_has_answer_label"))
        and bool(features.get("promptedge_text_present", 0))
    )


def _no_family_no_promptedge(policy: Dict[str, Any], row: Dict[str, Any]) -> bool:
    features = row["features"]
    return (
        float(features.get("candidate_confidence", 0.0)) >= float(policy["min_candidate_confidence"])
        and bool(features.get("candidate_has_answer_label"))
    )


def _no_family_with_promptedge(policy: Dict[str, Any], row: Dict[str, Any]) -> bool:
    features = row["features"]
    return (
        float(features.get("candidate_confidence", 0.0)) >= float(policy["min_candidate_confidence"])
        and bool(features.get("candidate_has_answer_label"))
        and bool(features.get("promptedge_text_present", 0))
    )


def _evaluate(
    rows: List[Dict[str, Any]],
    policy: Dict[str, Any],
    selector: Callable[[Dict[str, Any], Dict[str, Any]], bool],
) -> Dict[str, Dict[str, Any]]:
    predictions = [
        {
            "split": row["split"],
            "target_forward": row["target_forward"],
            "predicted_forward": selector(policy, row),
        }
        for row in rows
    ]
    return {
        split: _metrics([row for row in predictions if row["split"] == split])
        for split in ["train", "dev", "test"]
    }


def _prediction_rows(rows: List[Dict[str, Any]], policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "run_id": "R327",
            "source_ref_hash": row["source_ref_hash"],
            "source_run": row["source_run"],
            "source_variant": row.get("source_variant", ""),
            "split": row["split"],
            "dataset_family": row["dataset_family"],
            "promptnode_family": row["features"]["promptnode_family"],
            "promptedge_text_present": row["features"].get("promptedge_text_present", 0),
            "target_forward": row["target_forward"],
            "predicted_forward": predict_augmented(policy, row),
        }
        for row in rows
    ]


def _ablation_row(
    variant: str,
    rows: List[Dict[str, Any]],
    policy: Dict[str, Any],
    selector: Callable[[Dict[str, Any], Dict[str, Any]], bool],
) -> Dict[str, Any]:
    metrics = _evaluate(rows, policy, selector)
    return {
        "variant": variant,
        "test_accuracy": metrics["test"]["accuracy"],
        "test_precision_forward": metrics["test"]["precision_forward"],
        "test_recall_forward": metrics["test"]["recall_forward"],
        "test_false_forward": metrics["test"]["false_forward"],
        "test_missed_forward": metrics["test"]["missed_forward"],
    }


def build_augmented_selector_summary(manifest_jsonl: str = DEFAULT_AUGMENTED_MANIFEST_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    policy = train_augmented_selector(rows)
    predictions = _prediction_rows(rows, policy)
    metrics = {
        split: _metrics([row for row in predictions if row["split"] == split])
        for split in ["train", "dev", "test"]
    }
    hard_predictions = [row for row in predictions if row["source_run"] == "R325"]
    ablations = [
        _ablation_row("full_augmented_selector", rows, policy, predict_augmented),
        _ablation_row("no_family_no_promptedge_text_feature", rows, policy, _no_family_no_promptedge),
        _ablation_row("no_family_with_promptedge_text_feature", rows, policy, _no_family_with_promptedge),
    ]
    by_variant = {row["variant"]: row for row in ablations}
    promptedge_identified = (
        by_variant["no_family_no_promptedge_text_feature"]["test_false_forward"]
        > by_variant["no_family_with_promptedge_text_feature"]["test_false_forward"]
    )
    return {
        "run_id": "R327",
        "title": "Augmented selector retraining dry run",
        "claim_boundary": (
            "R327 retrains the transparent selector on the hard-negative augmented manifest. It identifies PromptEdge "
            "text as a safety feature in the offline manifest, but it is still not an API or paper-result claim."
        ),
        "no_api": True,
        "broad_api": False,
        "manifest_records": len(rows),
        "hard_negative_records": len(hard_predictions),
        "learned_policy": policy,
        "metrics": metrics,
        "forwarded_hard_negative_count": sum(1 for row in hard_predictions if row["predicted_forward"]),
        "feature_ablation_after_hard_negatives": ablations,
        "promptedge_feature_contribution_identified": promptedge_identified,
        "paper_claim_authorized": False,
        "api_execution_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R328_selector_policy_claim_update",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R327 Augmented Selector Retraining Dry Run",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Learned policy: `{summary['learned_policy']}`",
        f"- Forwarded hard negatives: `{summary['forwarded_hard_negative_count']}`",
        f"- PromptEdge contribution identified: `{summary['promptedge_feature_contribution_identified']}`",
        "",
        "## Feature Ablation",
        "",
        "| Variant | Test Accuracy | Test Precision | Test Recall | False Forward | Missed Forward |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["feature_ablation_after_hard_negatives"]:
        rows.append(
            f"| `{row['variant']}` | `{row['test_accuracy']}` | `{row['test_precision_forward']}` | `{row['test_recall_forward']}` | `{row['test_false_forward']}` | `{row['test_missed_forward']}` |"
        )
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    manifest_jsonl: str = DEFAULT_AUGMENTED_MANIFEST_JSONL,
    predictions_jsonl: str = DEFAULT_PREDICTIONS_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    policy = train_augmented_selector(rows)
    predictions = _prediction_rows(rows, policy)
    summary = build_augmented_selector_summary(manifest_jsonl=manifest_jsonl)
    summary.update({"predictions_jsonl": predictions_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(predictions_jsonl, predictions)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R327 augmented selector retraining dry run.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_AUGMENTED_MANIFEST_JSONL)
    parser.add_argument("--predictions_jsonl", default=DEFAULT_PREDICTIONS_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
