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

from experiment.mmlu.r303_audit_exclusion_protocol import EXCLUDED_TASK_IDS


DEFAULT_R304_JSONL = "experiment/mmlu/run_logs/mmlu_r304_multi_trigger_safety_gate_results.jsonl"
DEFAULT_R306_JSONL = "experiment/mmlu/run_logs/mmlu_r306_nonmath_stack_eval_results.jsonl"
DEFAULT_R312_JSONL = "experiment/mmlu/run_logs/mmlu_r312_nonstem_safety_replay_results.jsonl"
DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r322_selector_training_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r322_selector_training_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r322_selector_training_preflight_report.md"


FORBIDDEN_FEATURE_KEYS = {
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


def _bool_feature_map(prefix: str, values: Iterable[str], allowed: Iterable[str]) -> Dict[str, int]:
    present = set(values or [])
    return {f"{prefix}_{name.lower()}": int(name in present) for name in allowed}


def _promptnode_family(source_run: str, candidate_type: str) -> str:
    if candidate_type in {"", "none"}:
        return "none"
    if source_run == "R304":
        return "symbolic_verifier"
    if candidate_type in {"option_semantic_consistency", "conceptual_all_of_these_consistency"}:
        return "nonmath_semantic"
    if candidate_type in {"instruction_ambiguity_verifier", "memory_bridge_required"}:
        return "warning_only"
    return "other_verifier"


def _base_features(row: Dict[str, Any], source_run: str, dataset_family: str) -> Dict[str, Any]:
    candidate = row.get("candidate") or {}
    gate = row.get("gate_decision") or {}
    permissions = candidate.get("promptedge_permissions") or row.get("promptedge_permissions") or []
    lifecycle = candidate.get("lifecycle_actions") or row.get("lifecycle_actions") or []
    roles = candidate.get("promptnode_roles") or row.get("promptnode_roles") or []
    candidate_type = str(candidate.get("candidate_type") or "none")
    features: Dict[str, Any] = {
        "source_run": source_run,
        "dataset_family": dataset_family,
        "promptnode_family": _promptnode_family(source_run, candidate_type),
        "candidate_type": candidate_type,
        "candidate_has_answer_label": int(bool(candidate.get("candidate_label"))),
        "candidate_confidence": float(candidate.get("confidence") or 0.0),
        "candidate_evidence_count": int(candidate.get("evidence_count") or 0),
        "gate_score": float(gate.get("score") or 0.0),
        "gate_hard_veto": int(bool(gate.get("hard_veto"))),
        "model_visible_features_only": int(bool(row.get("model_visible_features_only", True))),
    }
    features.update(_bool_feature_map("promptedge_has", permissions, ["read", "write", "forward"]))
    features.update(_bool_feature_map("lifecycle_has", lifecycle, ["update", "write", "compress", "prune", "merge", "upgrade"]))
    features.update(
        _bool_feature_map(
            "role_has",
            roles,
            [
                "PN_InstructionVerifier",
                "PN_OptionBindingVerifier",
                "PN_SymbolicVerifier",
                "PN_ToolResource",
                "PN_SafetyGate",
                "PN_Router",
                "PN_AdversarialVerifier",
                "PN_ContradictionDetector",
                "PN_ConsensusConflictResolver",
                "PN_MemoryBridge",
            ],
        )
    )
    return features


def _manifest_row(
    row: Dict[str, Any],
    source_run: str,
    dataset_family: str,
    source_line: int,
    target_forward: bool,
    target_policy: str,
) -> Dict[str, Any]:
    task_id = str(row.get("task_id") or f"{source_run}:{source_line}")
    candidate = row.get("candidate") or {}
    return {
        "run_id": "R322",
        "source_run": source_run,
        "dataset_family": dataset_family,
        "source_ref_hash": _hash_ref(source_run, task_id, source_line, candidate.get("candidate_type", "")),
        "source_line": source_line,
        "features": _base_features(row, source_run, dataset_family),
        "target_forward": bool(target_forward),
        "target_policy": target_policy,
    }


def build_manifest_rows(
    r304_jsonl: str = DEFAULT_R304_JSONL,
    r306_jsonl: str = DEFAULT_R306_JSONL,
    r312_jsonl: str = DEFAULT_R312_JSONL,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for source_line, row in enumerate(_load_jsonl(r304_jsonl)):
        if row.get("task_id") in EXCLUDED_TASK_IDS:
            continue
        rows.append(
            _manifest_row(
                row,
                source_run="R304",
                dataset_family="mmlu_stem",
                source_line=source_line,
                target_forward=bool((row.get("gate_decision") or {}).get("forward")),
                target_policy="symbolic_promptnode_forward_policy",
            )
        )
    for source_line, row in enumerate(_load_jsonl(r306_jsonl)):
        if row.get("task_id") in EXCLUDED_TASK_IDS or row.get("audit_excluded"):
            continue
        rows.append(
            _manifest_row(
                row,
                source_run="R306",
                dataset_family="mmlu_stem",
                source_line=source_line,
                target_forward=bool(row.get("nonmath_forward")),
                target_policy="nonmath_promptnode_forward_policy",
            )
        )
    for source_line, row in enumerate(_load_jsonl(r312_jsonl)):
        if row.get("control_variant") != "proposed_nonstem_promptnode_promptedge_safety_replay":
            continue
        rows.append(
            _manifest_row(
                row,
                source_run="R312",
                dataset_family="mmlu_nonstem",
                source_line=source_line,
                target_forward=False,
                target_policy="warning_only_lifecycle_no_override_policy",
            )
        )
    return _assign_splits(rows)


def _assign_splits(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = [dict(row) for row in rows]
    for target in [False, True]:
        group = sorted((row for row in out if row["target_forward"] is target), key=lambda item: item["source_ref_hash"])
        for i, row in enumerate(group):
            if len(group) >= 3 and i == len(group) - 2:
                split = "dev"
            elif len(group) >= 3 and i == len(group) - 1:
                split = "test"
            elif i % 10 == 7:
                split = "dev"
            elif i % 10 in {8, 9}:
                split = "test"
            else:
                split = "train"
            row["split"] = split
    return out


def leakage_violations(rows: List[Dict[str, Any]]) -> List[str]:
    violations = set()
    for row in rows:
        for key in FORBIDDEN_FEATURE_KEYS:
            if key in row:
                violations.add(f"top_level:{key}")
            if key in row.get("features", {}):
                violations.add(f"features:{key}")
    return sorted(violations)


def build_selector_preflight_summary(
    r304_jsonl: str = DEFAULT_R304_JSONL,
    r306_jsonl: str = DEFAULT_R306_JSONL,
    r312_jsonl: str = DEFAULT_R312_JSONL,
) -> Dict[str, Any]:
    rows = build_manifest_rows(r304_jsonl=r304_jsonl, r306_jsonl=r306_jsonl, r312_jsonl=r312_jsonl)
    split_counts = Counter(row["split"] for row in rows)
    positive_split_counts = Counter(row["split"] for row in rows if row["target_forward"])
    family_counts = Counter(row["features"]["promptnode_family"] for row in rows)
    violations = leakage_violations(rows)
    return {
        "run_id": "R322",
        "title": "Selector training preflight manifest",
        "claim_boundary": (
            "R322 freezes an offline graph-policy selector manifest. It authorizes only the next no-API dry run, not "
            "API execution or paper claims."
        ),
        "no_api": True,
        "broad_api": False,
        "manifest_records": len(rows),
        "positive_forward_targets": sum(1 for row in rows if row["target_forward"]),
        "negative_forward_targets": sum(1 for row in rows if not row["target_forward"]),
        "split_counts": dict(split_counts),
        "positive_split_counts": dict(positive_split_counts),
        "promptnode_family_counts": dict(family_counts),
        "excluded_audit_items_count": len(EXCLUDED_TASK_IDS),
        "excluded_audit_items": sorted(EXCLUDED_TASK_IDS),
        "forbidden_feature_keys": sorted(FORBIDDEN_FEATURE_KEYS),
        "feature_leakage_pass": not violations,
        "feature_leakage_violations": violations,
        "offline_selector_training_authorized_next": not violations and len(rows) > 0,
        "api_execution_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R323_selector_model_dry_run",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R322 Selector Training Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Manifest records: `{summary['manifest_records']}`",
            f"- Positive forward targets: `{summary['positive_forward_targets']}`",
            f"- Split counts: `{summary['split_counts']}`",
            f"- Positive split counts: `{summary['positive_split_counts']}`",
            f"- PromptNode family counts: `{summary['promptnode_family_counts']}`",
            f"- Feature leakage pass: `{summary['feature_leakage_pass']}`",
            f"- Offline selector training authorized next: `{summary['offline_selector_training_authorized_next']}`",
            f"- API execution authorized next: `{summary['api_execution_authorized_next']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r304_jsonl: str = DEFAULT_R304_JSONL,
    r306_jsonl: str = DEFAULT_R306_JSONL,
    r312_jsonl: str = DEFAULT_R312_JSONL,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    rows = build_manifest_rows(r304_jsonl=r304_jsonl, r306_jsonl=r306_jsonl, r312_jsonl=r312_jsonl)
    summary = build_selector_preflight_summary(r304_jsonl=r304_jsonl, r306_jsonl=r306_jsonl, r312_jsonl=r312_jsonl)
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, rows)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R322 selector training preflight manifest.")
    parser.add_argument("--r304_jsonl", default=DEFAULT_R304_JSONL)
    parser.add_argument("--r306_jsonl", default=DEFAULT_R306_JSONL)
    parser.add_argument("--r312_jsonl", default=DEFAULT_R312_JSONL)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
