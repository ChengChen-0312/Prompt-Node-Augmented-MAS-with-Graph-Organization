from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r323_selector_model_dry_run import (
    DEFAULT_MANIFEST_JSONL,
    _load_jsonl,
    _metrics,
    predict,
    train_structural_selector,
)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r324_selector_feature_ablation_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r324_selector_feature_ablation_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _family_selector(policy: Dict[str, Any], row: Dict[str, Any]) -> bool:
    return predict(policy, row)


def _no_family_selector(policy: Dict[str, Any], row: Dict[str, Any]) -> bool:
    features = row["features"]
    return bool(features.get("candidate_has_answer_label")) and float(features.get("candidate_confidence", 0.0)) >= float(
        policy["min_candidate_confidence"]
    )


def _no_answer_label_selector(policy: Dict[str, Any], row: Dict[str, Any]) -> bool:
    features = row["features"]
    return (
        features.get("promptnode_family") in set(policy["allowed_promptnode_families"])
        and float(features.get("candidate_confidence", 0.0)) >= float(policy["min_candidate_confidence"])
    )


def _confidence_only_selector(policy: Dict[str, Any], row: Dict[str, Any]) -> bool:
    return float(row["features"].get("candidate_confidence", 0.0)) >= float(policy["min_candidate_confidence"])


def _evaluate_variant(
    name: str,
    rows: List[Dict[str, Any]],
    selector: Callable[[Dict[str, Any], Dict[str, Any]], bool],
    policy: Dict[str, Any],
    uses_promptedge_features: bool = False,
) -> Dict[str, Any]:
    predictions = []
    for row in rows:
        predictions.append(
            {
                "split": row["split"],
                "target_forward": row["target_forward"],
                "predicted_forward": selector(policy, row),
            }
        )
    by_split = {
        split: _metrics([row for row in predictions if row["split"] == split])
        for split in ["train", "dev", "test"]
    }
    return {
        "variant": name,
        "uses_promptedge_features": uses_promptedge_features,
        "train_accuracy": by_split["train"]["accuracy"],
        "dev_accuracy": by_split["dev"]["accuracy"],
        "test_accuracy": by_split["test"]["accuracy"],
        "test_precision_forward": by_split["test"]["precision_forward"],
        "test_recall_forward": by_split["test"]["recall_forward"],
        "test_false_forward": by_split["test"]["false_forward"],
        "test_missed_forward": by_split["test"]["missed_forward"],
    }


def _random_same_budget_variant(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    predictions = []
    for split in ["train", "dev", "test"]:
        split_rows = [row for row in rows if row["split"] == split]
        budget = sum(1 for row in split_rows if row["target_forward"])
        selected = {
            row["source_ref_hash"]
            for row in sorted(split_rows, key=lambda item: item["source_ref_hash"])[:budget]
        }
        predictions.extend(
            {
                "split": row["split"],
                "target_forward": row["target_forward"],
                "predicted_forward": row["source_ref_hash"] in selected,
            }
            for row in split_rows
        )
    by_split = {
        split: _metrics([row for row in predictions if row["split"] == split])
        for split in ["train", "dev", "test"]
    }
    return {
        "variant": "random_same_forward_budget",
        "uses_promptedge_features": False,
        "train_accuracy": by_split["train"]["accuracy"],
        "dev_accuracy": by_split["dev"]["accuracy"],
        "test_accuracy": by_split["test"]["accuracy"],
        "test_precision_forward": by_split["test"]["precision_forward"],
        "test_recall_forward": by_split["test"]["recall_forward"],
        "test_false_forward": by_split["test"]["false_forward"],
        "test_missed_forward": by_split["test"]["missed_forward"],
    }


def build_feature_ablation_summary(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    policy = train_structural_selector(rows)
    ablations = [
        _evaluate_variant("full_structural_selector", rows, _family_selector, policy),
        _evaluate_variant("remove_promptnode_family", rows, _no_family_selector, policy),
        _evaluate_variant("remove_candidate_answer_label", rows, _no_answer_label_selector, policy),
        _evaluate_variant("confidence_only", rows, _confidence_only_selector, policy),
        _random_same_budget_variant(rows),
    ]
    by_name = {row["variant"]: row for row in ablations}
    full_test = by_name["full_structural_selector"]["test_accuracy"]
    easy_ablation_ties = all(
        by_name[name]["test_accuracy"] == full_test
        for name in ["remove_promptnode_family", "remove_candidate_answer_label", "confidence_only"]
    )
    return {
        "run_id": "R324",
        "title": "Selector feature ablation",
        "claim_boundary": (
            "R324 tests whether the R323 dry-run result identifies real feature contributions. Because several easy "
            "ablations tie the full selector, the current manifest needs hard negative answer-bearing candidates before "
            "a training claim."
        ),
        "no_api": True,
        "broad_api": False,
        "ablation_results": ablations,
        "hard_negative_gap_detected": bool(easy_ablation_ties),
        "promptedge_feature_contribution_identified": any(row["uses_promptedge_features"] for row in ablations),
        "paper_claim_authorized": False,
        "api_execution_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R325_hard_negative_augmentation_protocol",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R324 Selector Feature Ablation",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Variant | Test Accuracy | Test Precision | Test Recall | False Forward | Missed Forward |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["ablation_results"]:
        rows.append(
            f"| `{row['variant']}` | `{row['test_accuracy']}` | `{row['test_precision_forward']}` | `{row['test_recall_forward']}` | `{row['test_false_forward']}` | `{row['test_missed_forward']}` |"
        )
    rows.extend(
        [
            "",
            f"- Hard negative gap detected: `{summary['hard_negative_gap_detected']}`",
            f"- PromptEdge feature contribution identified: `{summary['promptedge_feature_contribution_identified']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )
    return "\n".join(rows)


def run(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_feature_ablation_summary(manifest_jsonl=manifest_jsonl)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R324 selector feature ablation.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
