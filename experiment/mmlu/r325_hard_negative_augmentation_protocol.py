from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_BASE_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r322_selector_training_manifest.jsonl"
DEFAULT_R316_RESULTS_JSONL = "experiment/mmlu/run_logs/mmlu_r316_promptedge_cost_controls_results.jsonl"
DEFAULT_AUGMENTED_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r325_selector_augmented_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r325_hard_negative_augmentation_protocol_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r325_hard_negative_augmentation_protocol_report.md"


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


def _confidence(parsed: Dict[str, Any]) -> float:
    raw = str(parsed.get("confidence") or "").strip().lower()
    if raw in {"high", "very_high", "high_confidence"}:
        return 1.0
    try:
        return float(raw)
    except ValueError:
        return 0.95


def _candidate_family(variant: str) -> str:
    if variant == "node_only_no_promptedge_text":
        return "answer_bearing_no_promptedge_text"
    if variant == "plain_requery":
        return "plain_requery_answer_bearing"
    return "answer_bearing_hard_negative"


def _hard_negative_feature_row(row: Dict[str, Any], source_line: int) -> Dict[str, Any]:
    variant = str(row.get("control_variant") or "")
    candidate = row.get("candidate") or {}
    parsed = row.get("parsed_control_response") or {}
    promptedge_text_present = 0 if variant in {"node_only_no_promptedge_text", "plain_requery"} else 1
    features = {
        "source_run": "R325",
        "dataset_family": "mmlu_nonstem",
        "promptnode_family": _candidate_family(variant),
        "candidate_type": str(candidate.get("candidate_type") or "answer_bearing_control"),
        "candidate_has_answer_label": 1,
        "candidate_confidence": _confidence(parsed),
        "candidate_evidence_count": max(1, len(parsed.get("evidence_checks") or [])),
        "gate_score": 0.0,
        "gate_hard_veto": 0,
        "model_visible_features_only": 1,
        "promptedge_text_present": promptedge_text_present,
        "promptedge_has_read": 1,
        "promptedge_has_write": 1 if variant == "node_only_no_promptedge_text" else 0,
        "promptedge_has_forward": 1,
        "lifecycle_has_update": 1,
        "lifecycle_has_write": 1,
        "lifecycle_has_compress": 1,
        "lifecycle_has_prune": 0 if variant == "node_only_no_promptedge_text" else 1,
        "lifecycle_has_merge": 0,
        "lifecycle_has_upgrade": 0,
        "role_has_pn_instructionverifier": int(variant == "node_only_no_promptedge_text"),
        "role_has_pn_optionbindingverifier": 0,
        "role_has_pn_symbolicverifier": 0,
        "role_has_pn_toolresource": 0,
        "role_has_pn_safetygate": 0,
        "role_has_pn_router": 1,
        "role_has_pn_adversarialverifier": int(variant == "node_only_no_promptedge_text"),
        "role_has_pn_contradictiondetector": int(variant == "node_only_no_promptedge_text"),
        "role_has_pn_consensusconflictresolver": 0,
        "role_has_pn_memorybridge": int(variant == "node_only_no_promptedge_text"),
    }
    return {
        "run_id": "R325",
        "source_run": "R325",
        "source_variant": variant,
        "dataset_family": "mmlu_nonstem",
        "source_ref_hash": _hash_ref("R325", variant, row.get("task_id", ""), source_line),
        "source_line": source_line,
        "split": ["train", "train", "dev", "test"][source_line % 4],
        "features": features,
        "target_forward": False,
        "target_policy": "answer_bearing_hard_negative_no_forward_policy",
    }


def build_hard_negative_rows(r316_results_jsonl: str = DEFAULT_R316_RESULTS_JSONL) -> List[Dict[str, Any]]:
    rows = []
    for source_line, row in enumerate(_load_jsonl(r316_results_jsonl)):
        variant = row.get("control_variant")
        if variant not in {"node_only_no_promptedge_text", "plain_requery"}:
            continue
        switched = row.get("predicted_answer") != row.get("arg_prediction")
        false_forward = bool(row.get("harm")) or (switched and not row.get("fix"))
        if false_forward:
            rows.append(_hard_negative_feature_row(row, len(rows)))
    return rows


def _with_promptedge_text_default(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    features = dict(out.get("features", {}))
    features.setdefault("promptedge_text_present", 1)
    out["features"] = features
    return out


def _leakage_violations(rows: List[Dict[str, Any]]) -> List[str]:
    violations = set()
    for row in rows:
        for key in FORBIDDEN_EXPORT_KEYS:
            if key in row:
                violations.add(f"top_level:{key}")
            if key in row.get("features", {}):
                violations.add(f"features:{key}")
    return sorted(violations)


def build_augmented_manifest(
    base_manifest_jsonl: str = DEFAULT_BASE_MANIFEST_JSONL,
    r316_results_jsonl: str = DEFAULT_R316_RESULTS_JSONL,
) -> List[Dict[str, Any]]:
    base_rows = [_with_promptedge_text_default(row) for row in _load_jsonl(base_manifest_jsonl)]
    return base_rows + build_hard_negative_rows(r316_results_jsonl=r316_results_jsonl)


def build_hard_negative_summary(
    base_manifest_jsonl: str = DEFAULT_BASE_MANIFEST_JSONL,
    r316_results_jsonl: str = DEFAULT_R316_RESULTS_JSONL,
) -> Dict[str, Any]:
    base_rows = [_with_promptedge_text_default(row) for row in _load_jsonl(base_manifest_jsonl)]
    hard_rows = build_hard_negative_rows(r316_results_jsonl=r316_results_jsonl)
    augmented = base_rows + hard_rows
    violations = _leakage_violations(augmented)
    target_counts = Counter("true" if row["target_forward"] else "false" for row in hard_rows)
    return {
        "run_id": "R325",
        "title": "Hard negative augmentation protocol",
        "claim_boundary": (
            "R325 augments the selector manifest with answer-bearing false-forward cases mined from R316 controls. "
            "It prepares a harder offline retraining set but does not authorize API execution or paper claims."
        ),
        "no_api": True,
        "broad_api": False,
        "base_manifest_records": len(base_rows),
        "hard_negative_records": len(hard_rows),
        "augmented_manifest_records": len(augmented),
        "hard_negative_target_forward_counts": dict(target_counts),
        "hard_negative_source_variants": sorted(set(row["source_variant"] for row in hard_rows)),
        "feature_leakage_pass": not violations,
        "feature_leakage_violations": violations,
        "paper_claim_authorized": False,
        "api_execution_authorized_next": False,
        "offline_selector_retraining_authorized_next": not violations and bool(hard_rows),
        "sci_q2_ready": False,
        "next_required_run": "R326_goal_audit_after_selector_pretraining",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R325 Hard Negative Augmentation Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Base manifest records: `{summary['base_manifest_records']}`",
            f"- Hard negative records: `{summary['hard_negative_records']}`",
            f"- Augmented manifest records: `{summary['augmented_manifest_records']}`",
            f"- Hard negative variants: `{summary['hard_negative_source_variants']}`",
            f"- Feature leakage pass: `{summary['feature_leakage_pass']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    base_manifest_jsonl: str = DEFAULT_BASE_MANIFEST_JSONL,
    r316_results_jsonl: str = DEFAULT_R316_RESULTS_JSONL,
    augmented_manifest_jsonl: str = DEFAULT_AUGMENTED_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    augmented = build_augmented_manifest(base_manifest_jsonl=base_manifest_jsonl, r316_results_jsonl=r316_results_jsonl)
    summary = build_hard_negative_summary(base_manifest_jsonl=base_manifest_jsonl, r316_results_jsonl=r316_results_jsonl)
    summary.update({"augmented_manifest_jsonl": augmented_manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(augmented_manifest_jsonl, augmented)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R325 hard negative selector augmentation.")
    parser.add_argument("--base_manifest_jsonl", default=DEFAULT_BASE_MANIFEST_JSONL)
    parser.add_argument("--r316_results_jsonl", default=DEFAULT_R316_RESULTS_JSONL)
    parser.add_argument("--augmented_manifest_jsonl", default=DEFAULT_AUGMENTED_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
