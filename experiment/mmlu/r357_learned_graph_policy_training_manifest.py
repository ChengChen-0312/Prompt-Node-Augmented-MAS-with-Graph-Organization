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


DEFAULT_BASE_AUGMENTED_MANIFEST = "experiment/mmlu/run_logs/mmlu_r325_selector_augmented_manifest.jsonl"
DEFAULT_R352_RESULTS = "experiment/mmlu/run_logs/mmlu_r352_fresh_coverage_promptnode_expansion_preflight_results.jsonl"
DEFAULT_R354_RESULTS = "experiment/mmlu/run_logs/mmlu_r354_fresh_eval_after_coverage_expansion_local_tool_results.jsonl"
DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r357_learned_graph_policy_training_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r357_learned_graph_policy_training_manifest_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r357_learned_graph_policy_training_manifest_report.md"

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


def _split(ref_hash: str, target_forward: bool) -> str:
    bucket = int(ref_hash[-2:], 16) % 10
    if target_forward:
        return "dev" if bucket == 8 else "test" if bucket == 9 else "train"
    return "dev" if bucket == 7 else "test" if bucket in {8, 9} else "train"


def _promptnode_family(promptnode_id: str) -> str:
    mapping = {
        "PN_NumericWordProblemSolver": "tool_resource_numeric",
        "PN_PhysicsFormulaEvaluator": "tool_resource_physics",
        "PN_ChemistryConceptAndStoichiometryTool": "tool_resource_chemistry",
        "PN_DefinitionFallacyVerifier": "nonmath_definition",
        "PN_None": "none",
    }
    return mapping.get(promptnode_id or "", "tool_or_verifier_other")


def _new_feature_row(row: Dict[str, Any], source_run: str, source_line: int) -> Dict[str, Any]:
    promptnode_id = str(row.get("promptnode_id") or "PN_None")
    candidate_present = bool(row.get("candidate_label"))
    contract_pass = bool(row.get("promptedge_contract_pass"))
    evidence = row.get("evidence") or {}
    target_forward = bool(candidate_present and contract_pass and row.get("candidate_is_correct"))
    ref_hash = _hash_ref(source_run, row.get("task_id", ""), promptnode_id, source_line)
    features = {
        "source_run": source_run,
        "dataset_family": row.get("dataset_family", ""),
        "subject_family": str(row.get("subject", "")).split("_")[0],
        "promptnode_family": _promptnode_family(promptnode_id),
        "candidate_type": str(evidence.get("template") or evidence.get("status") or "none"),
        "candidate_has_answer_label": int(candidate_present),
        "candidate_confidence": 1.0 if contract_pass else 0.0,
        "candidate_evidence_count": 1 if evidence and evidence.get("status") != "no_expanded_promptnode_forwarded" else 0,
        "gate_score": 1.0 if contract_pass else -0.5,
        "gate_hard_veto": int(not contract_pass),
        "model_visible_features_only": 1,
        "promptedge_text_present": 1,
        "promptedge_has_read": 1,
        "promptedge_has_write": int(bool(evidence)),
        "promptedge_has_forward": int(contract_pass),
        "lifecycle_has_update": int(candidate_present),
        "lifecycle_has_write": int(bool(evidence)),
        "lifecycle_has_compress": 1,
        "lifecycle_has_prune": int(not contract_pass),
        "lifecycle_has_merge": 0,
        "lifecycle_has_upgrade": int(contract_pass),
        "role_has_pn_instructionverifier": 0,
        "role_has_pn_optionbindingverifier": 0,
        "role_has_pn_symbolicverifier": int("Numeric" in promptnode_id),
        "role_has_pn_toolresource": int(promptnode_id.startswith("PN_") and promptnode_id != "PN_None"),
        "role_has_pn_safetygate": 1,
        "role_has_pn_router": 1,
        "role_has_pn_adversarialverifier": 0,
        "role_has_pn_contradictiondetector": 0,
        "role_has_pn_consensusconflictresolver": int(not contract_pass),
        "role_has_pn_memorybridge": 0,
    }
    return {
        "run_id": "R357",
        "source_run": source_run,
        "dataset_family": row.get("dataset_family", ""),
        "source_ref_hash": ref_hash,
        "source_line": source_line,
        "split": _split(ref_hash, target_forward),
        "features": features,
        "target_forward": target_forward,
        "target_add_node": promptnode_id if promptnode_id != "PN_None" else "NONE",
        "target_add_edge": "forward_candidate_if_contract_passes" if target_forward else "block_forward_if_warning_only",
        "target_prune": not target_forward,
        "target_policy": "learned_graph_policy_promptnode_edge_action",
    }


def _normalize_base_row(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    out["run_id"] = "R357"
    out.setdefault("target_add_node", out.get("features", {}).get("promptnode_family", "none"))
    out.setdefault("target_add_edge", "forward_candidate_if_contract_passes" if out.get("target_forward") else "block_forward_if_warning_only")
    out.setdefault("target_prune", not bool(out.get("target_forward")))
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


def build_training_manifest(
    base_augmented_manifest: str = DEFAULT_BASE_AUGMENTED_MANIFEST,
    r352_results: str = DEFAULT_R352_RESULTS,
    r354_results: str = DEFAULT_R354_RESULTS,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    base_rows = [_normalize_base_row(row) for row in _load_jsonl(base_augmented_manifest)]
    r352_rows = [_new_feature_row(row, "R352", i) for i, row in enumerate(_load_jsonl(r352_results))]
    r354_rows = [_new_feature_row(row, "R354", i) for i, row in enumerate(_load_jsonl(r354_results))]
    rows = base_rows + r352_rows + r354_rows
    violations = _leakage_violations(rows)
    source_counts = Counter(row.get("source_run") for row in rows)
    split_counts = Counter(row.get("split") for row in rows)
    return rows, {
        "run_id": "R357",
        "title": "Learned graph-policy training manifest",
        "claim_boundary": (
            "R357 creates a leakage-safe offline training manifest for graph actions. It does not train a model or "
            "authorize API execution."
        ),
        "no_api": True,
        "broad_api": False,
        "base_augmented_records": len(base_rows),
        "r352_added_records": len(r352_rows),
        "r354_added_records": len(r354_rows),
        "manifest_records": len(rows),
        "positive_forward_targets": sum(1 for row in rows if row.get("target_forward")),
        "source_run_counts": dict(sorted(source_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "contains_first_class_graph_action_targets": all(
            key in rows[0] for key in ["target_add_node", "target_add_edge", "target_prune", "target_forward"]
        )
        if rows
        else False,
        "feature_leakage_pass": not violations,
        "feature_leakage_violations": violations,
        "api_execution_authorized_next": False,
        "offline_training_authorized_next": not violations and bool(rows),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R358_learned_graph_policy_offline_training",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R357 Learned Graph-Policy Training Manifest",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records: `{summary['manifest_records']}`",
            f"- Positive forward targets: `{summary['positive_forward_targets']}`",
            f"- Source runs: `{summary['source_run_counts']}`",
            f"- Feature leakage pass: `{summary['feature_leakage_pass']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    base_augmented_manifest: str = DEFAULT_BASE_AUGMENTED_MANIFEST,
    r352_results: str = DEFAULT_R352_RESULTS,
    r354_results: str = DEFAULT_R354_RESULTS,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    rows, summary = build_training_manifest(
        base_augmented_manifest=base_augmented_manifest,
        r352_results=r352_results,
        r354_results=r354_results,
    )
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, rows)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R357 learned graph-policy training manifest.")
    parser.add_argument("--base_augmented_manifest", default=DEFAULT_BASE_AUGMENTED_MANIFEST)
    parser.add_argument("--r352_results", default=DEFAULT_R352_RESULTS)
    parser.add_argument("--r354_results", default=DEFAULT_R354_RESULTS)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
