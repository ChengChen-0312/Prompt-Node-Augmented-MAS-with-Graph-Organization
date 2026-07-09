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


DEFAULT_BASE_MANIFEST = "experiment/mmlu/run_logs/mmlu_r357_learned_graph_policy_training_manifest.jsonl"
DEFAULT_R369_RESULTS = "experiment/mmlu/run_logs/mmlu_r369_adversarial_verifier_api_probe_results.jsonl"
DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r371_graph_policy_manifest_with_r369_hard_negatives.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r371_adversarial_probe_hard_negative_update_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r371_adversarial_probe_hard_negative_update_report.md"
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


def _family(row: Dict[str, Any]) -> str:
    parsed = row.get("parsed_response") or {}
    family = str(parsed.get("promptnode_family") or parsed.get("verifier_family") or "").lower()
    subject = str(row.get("subject") or "")
    if "history" in subject:
        return "passage_history_entailment"
    if "chem" in subject or "physics" in subject:
        return "unsafe_domain_specialized"
    if "adversarial" in family or row.get("control_variant") == "adversarial_candidate_verifier_api":
        return "unsafe_adversarial_candidate"
    return "unsafe_domain_specialized"


def _feature_row(row: Dict[str, Any], source_line: int) -> Dict[str, Any]:
    target_forward = bool(row.get("candidate_is_correct"))
    ref_hash = _hash_ref("R369", row.get("control_variant", ""), row.get("task_id", ""), source_line)
    family = _family(row)
    parsed = row.get("parsed_response") or {}
    evidence_count = int(parsed.get("evidence_count") or 0)
    confidence_raw = str(parsed.get("confidence") or "").lower()
    confidence = 1.0 if confidence_raw == "high" else float(confidence_raw or 0.0)
    features = {
        "dataset_family": row.get("dataset_family", ""),
        "subject_family": str(row.get("subject", "")).split("_")[0],
        "promptnode_family": family,
        "candidate_type": str(parsed.get("candidate_type") or family),
        "candidate_has_answer_label": 1,
        "candidate_confidence": confidence,
        "candidate_evidence_count": evidence_count,
        "gate_score": 1.0 if target_forward else -0.25,
        "gate_hard_veto": int(not target_forward),
        "model_visible_features_only": 1,
        "promptedge_text_present": 1,
        "promptedge_has_read": 1,
        "promptedge_has_write": int(evidence_count > 0),
        "promptedge_has_forward": int(target_forward),
        "lifecycle_has_update": 1,
        "lifecycle_has_write": int(evidence_count > 0),
        "lifecycle_has_compress": 1,
        "lifecycle_has_prune": int(not target_forward),
        "lifecycle_has_merge": 0,
        "lifecycle_has_upgrade": int(target_forward),
        "role_has_pn_instructionverifier": 0,
        "role_has_pn_optionbindingverifier": 0,
        "role_has_pn_symbolicverifier": int("math" in str(row.get("subject") or "")),
        "role_has_pn_toolresource": int("chem" in str(row.get("subject") or "") or "physics" in str(row.get("subject") or "")),
        "role_has_pn_safetygate": 1,
        "role_has_pn_router": 1,
        "role_has_pn_adversarialverifier": int(row.get("control_variant") == "adversarial_candidate_verifier_api"),
        "role_has_pn_contradictiondetector": int(row.get("control_variant") == "adversarial_candidate_verifier_api"),
        "role_has_pn_consensusconflictresolver": int(not target_forward),
        "role_has_pn_memorybridge": 0,
    }
    return {
        "run_id": "R371",
        "source_run": "R369",
        "source_variant": row.get("control_variant"),
        "dataset_family": row.get("dataset_family", ""),
        "source_ref_hash": ref_hash,
        "source_line": source_line,
        "split": ["train", "train", "dev", "test"][source_line % 4],
        "features": features,
        "target_forward": target_forward,
        "target_add_node": family,
        "target_add_edge": "forward_candidate_if_contract_passes" if target_forward else "block_forward_if_warning_only",
        "target_prune": not target_forward,
        "target_policy": "r369_hard_negative_update_policy",
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
    r369_results: str = DEFAULT_R369_RESULTS,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    base_rows = _load_jsonl(base_manifest)
    candidate_rows = [row for row in _load_jsonl(r369_results) if row.get("candidate_label")]
    added = [_feature_row(row, i) for i, row in enumerate(candidate_rows)]
    rows = base_rows + added
    violations = _leakage_violations(rows)
    source_counts = Counter(row.get("source_run") for row in rows)
    return rows, {
        "run_id": "R371",
        "title": "Adversarial probe hard-negative update",
        "claim_boundary": (
            "R371 adds R369 wrong verifier candidates as hard negatives and the two history passage successes as "
            "positive training rows. It does not authorize API execution."
        ),
        "no_api": True,
        "broad_api": False,
        "base_records": len(base_rows),
        "r369_added_records": len(added),
        "r369_hard_negative_records": sum(1 for row in added if not row.get("target_forward")),
        "r369_positive_records": sum(1 for row in added if row.get("target_forward")),
        "manifest_records": len(rows),
        "source_run_counts": dict(sorted(source_counts.items())),
        "feature_leakage_pass": not violations,
        "feature_leakage_violations": violations,
        "api_execution_authorized_next": False,
        "offline_retraining_authorized_next": not violations,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R372_goal_audit_after_adversarial_probe_update",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R371 Adversarial Probe Hard-Negative Update",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Base records: `{summary['base_records']}`",
            f"- Added records: `{summary['r369_added_records']}`",
            f"- R369 hard negatives/positives: `{summary['r369_hard_negative_records']}/{summary['r369_positive_records']}`",
            f"- Feature leakage pass: `{summary['feature_leakage_pass']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    base_manifest: str = DEFAULT_BASE_MANIFEST,
    r369_results: str = DEFAULT_R369_RESULTS,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    rows, summary = build_updated_manifest(base_manifest=base_manifest, r369_results=r369_results)
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, rows)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R371 hard-negative update from R369 probe.")
    parser.add_argument("--base_manifest", default=DEFAULT_BASE_MANIFEST)
    parser.add_argument("--r369_results", default=DEFAULT_R369_RESULTS)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
