from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_BASE_MANIFEST = "experiment/mmlu/run_logs/mmlu_r371_graph_policy_manifest_with_r369_hard_negatives.jsonl"
DEFAULT_R389_RESULTS = "experiment/mmlu/run_logs/mmlu_r389_mixed_nonmath_option_binding_api_results.jsonl"
DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r391_graph_policy_manifest_with_mixed_nonmath_hard_negatives.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r391_mixed_nonmath_hard_negative_update_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r391_mixed_nonmath_hard_negative_update_report.md"
FORBIDDEN_EXPORT_KEYS = {
    "task_id",
    "question",
    "true_answer",
    "predicted_answer",
    "arg_prediction",
    "answer",
    "label",
    "is_correct",
    "fix",
    "harm",
}


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


def _hash_ref(*parts: Any) -> str:
    joined = "::".join(str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def _feature_row(row: Dict[str, Any], source_line: int) -> Dict[str, Any]:
    target_forward = bool(row.get("fix"))
    features = dict(row.get("candidate_features") or {})
    ref_hash = _hash_ref("R389", row.get("subject", ""), row.get("candidate_label", ""), row.get("gate_forward_probability", ""), source_line)
    family = str(features.get("promptnode_family") or "nonmath_semantic")
    return {
        "run_id": "R391",
        "source_run": "R389",
        "source_variant": "semantic_option_binding_candidate_api",
        "dataset_family": row.get("dataset_family", ""),
        "source_ref_hash": ref_hash,
        "source_line": source_line,
        "split": "train",
        "features": features,
        "target_forward": target_forward,
        "target_add_node": family,
        "target_add_edge": "forward_candidate_if_contract_passes" if target_forward else "block_forward_after_mixed_nonmath_hard_negative",
        "target_prune": not target_forward,
        "target_policy": "r389_mixed_nonmath_hard_negative_update_policy",
    }


def _leakage_violations(rows: List[Dict[str, Any]]) -> List[str]:
    violations = set()
    for row in rows:
        for key in FORBIDDEN_EXPORT_KEYS:
            if key in row:
                violations.add(f"top_level:{key}")
            if key in row.get("features", {}):
                violations.add(f"features:{key}")
    return sorted(violations)


def build_updated_manifest(
    base_manifest: str = DEFAULT_BASE_MANIFEST,
    r389_results: str = DEFAULT_R389_RESULTS,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    base_rows = _load_jsonl(base_manifest)
    informative_rows = [
        row
        for row in _load_jsonl(r389_results)
        if row.get("candidate_label") and (row.get("fix") or row.get("wrong_forward"))
    ]
    added = [_feature_row(row, i) for i, row in enumerate(informative_rows)]
    rows = base_rows + added
    violations = _leakage_violations(rows)
    source_counts = Counter(row.get("source_run") for row in rows)
    return rows, {
        "run_id": "R391",
        "title": "Mixed nonmath hard-negative update",
        "claim_boundary": (
            "R391 adds the R389 mixed-nonmath fix as a positive row and wrong-forwards as hard negatives. "
            "It is offline only and does not authorize API execution."
        ),
        "no_api": True,
        "broad_api": False,
        "base_records": len(base_rows),
        "r389_added_records": len(added),
        "r389_hard_negative_records": sum(1 for row in added if not row.get("target_forward")),
        "r389_positive_records": sum(1 for row in added if row.get("target_forward")),
        "manifest_records": len(rows),
        "source_run_counts": dict(sorted(source_counts.items())),
        "feature_leakage_pass": not violations,
        "feature_leakage_violations": violations,
        "api_execution_authorized_next": False,
        "offline_retraining_authorized_next": not violations,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R392_retrain_after_mixed_nonmath_hard_negatives",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R391 Mixed Nonmath Hard-Negative Update",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Base records: `{summary['base_records']}`",
            f"- Added records: `{summary['r389_added_records']}`",
            f"- R389 hard negatives/positives: `{summary['r389_hard_negative_records']}/{summary['r389_positive_records']}`",
            f"- Feature leakage pass: `{summary['feature_leakage_pass']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    base_manifest: str = DEFAULT_BASE_MANIFEST,
    r389_results: str = DEFAULT_R389_RESULTS,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    rows, summary = build_updated_manifest(base_manifest=base_manifest, r389_results=r389_results)
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, rows)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R391 hard-negative update from R389 mixed nonmath results.")
    parser.add_argument("--base_manifest", default=DEFAULT_BASE_MANIFEST)
    parser.add_argument("--r389_results", default=DEFAULT_R389_RESULTS)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
