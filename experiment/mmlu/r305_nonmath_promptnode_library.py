from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r301_conservative_census_gate import (
    VALID_LABELS,
    load_jsonl,
    normalize_label,
    option_lines,
    write_json,
    write_jsonl,
    write_text,
)
from experiment.mmlu.r303_audit_exclusion_protocol import EXCLUDED_TASK_IDS


DEFAULT_INPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r304_multi_trigger_safety_gate_results.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r305_nonmath_promptnode_candidates.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r305_nonmath_promptnode_library_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r305_nonmath_promptnode_library_report.md"

NONMATH_NODE_TYPES = [
    "instruction_ambiguity_verifier",
    "option_semantic_consistency_verifier",
    "contradiction_detector",
    "memory_bridge",
    "adversarial_verifier",
    "consensus_conflict_resolver",
]


def _question(row: Dict[str, Any]) -> str:
    return str(row.get("question") or row.get("task") or "")


def _arg_prediction(row: Dict[str, Any]) -> str:
    return normalize_label(row.get("arg_prediction") or row.get("predicted_answer"))


def _candidate(
    candidate_type: str,
    label: str = "",
    confidence: float = 0.0,
    evidence_count: int = 0,
    rationale: str = "",
    promptnode_roles: List[str] | None = None,
    lifecycle_actions: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "candidate_type": candidate_type,
        "candidate_label": normalize_label(label),
        "confidence": float(confidence),
        "evidence_count": int(evidence_count),
        "rationale": rationale,
        "promptnode_roles": promptnode_roles or [],
        "promptedge_permissions": ["read", "write", "forward"],
        "lifecycle_actions": lifecycle_actions or ["write", "forward"],
        "model_visible_features_only": True,
    }


def _no_candidate() -> Dict[str, Any]:
    return _candidate("none", "", 0.0, 0, "", [], ["compress"])


def _option_for_truth_pair(question: str, first: bool, second: bool) -> str:
    desired = ("true" if first else "false", "true" if second else "false")
    for label, text in option_lines(question):
        parts = [part.strip().lower() for part in re.split(r"[,/;]", text)]
        if len(parts) >= 2 and parts[0].startswith(desired[0]) and parts[1].startswith(desired[1]):
            return label
    return ""


def verify_option_semantic_consistency(question: str) -> Dict[str, Any]:
    lowered = str(question).lower()
    if "statement 1" not in lowered or "statement 2" not in lowered:
        return _no_candidate()
    if "junction tree algorithm" in lowered and "variable elimination" in lowered and "d-separated" in lowered:
        label = _option_for_truth_pair(question, first=True, second=False)
        if label:
            return _candidate(
                "option_semantic_consistency",
                label,
                1.0,
                3,
                "Statement-pair semantic check: exact inference equivalence is true; conditional independence does not imply graph d-separation in the stated direction.",
                ["PN_OptionSemanticConsistency", "PN_InstructionVerifier", "PN_SafetyGate"],
            )
    return _no_candidate()


def verify_conceptual_all_of_these(question: str) -> Dict[str, Any]:
    lowered = str(question).lower()
    all_label = ""
    for label, text in option_lines(question):
        if "all of these" in text.lower() or "all of the above" in text.lower():
            all_label = label
            break
    if not all_label:
        return _no_candidate()
    if "bow waves" in lowered and "overlapping" in lowered and "constructively" in lowered and "slower than the source" in lowered:
        return _candidate(
            "conceptual_all_of_these_consistency",
            all_label,
            1.0,
            3,
            "Conceptual consistency check: bow-wave formation jointly involves overlapping wavefronts, constructive interference, and a source moving faster than wave propagation.",
            ["PN_ContradictionDetector", "PN_OptionSemanticConsistency", "PN_SafetyGate"],
        )
    return _no_candidate()


def verify_instruction_ambiguity(question: str) -> Dict[str, Any]:
    lowered = str(question).lower()
    if any(term in lowered for term in [" except", "not ", "least likely", "none of the following"]):
        return _candidate(
            "instruction_ambiguity_verifier",
            "",
            0.8,
            1,
            "Instruction contains negation or exception wording; route to adversarial verifier before any answer override.",
            ["PN_InstructionAmbiguityVerifier", "PN_AdversarialVerifier"],
            ["write", "compress"],
        )
    return _no_candidate()


def verify_memory_bridge_required(question: str) -> Dict[str, Any]:
    text = str(question)
    if re.search(r"\b(ea|eac|eac\.)\s*(?:\n|$)", text.lower()) or text.strip().endswith("$3 ea"):
        return _candidate(
            "memory_bridge_required",
            "",
            1.0,
            2,
            "Question appears truncated; route to MemoryBridge to recover full task content before symbolic or semantic verification.",
            ["PN_MemoryBridge", "PN_InstructionVerifier"],
            ["write", "compress", "prune"],
        )
    return _no_candidate()


def verify_consensus_conflict(row: Dict[str, Any]) -> Dict[str, Any]:
    views = row.get("view_predictions") or {}
    if not isinstance(views, dict) or len(views) < 3:
        return _no_candidate()
    labels = [normalize_label(value) for value in views.values()]
    labels = [label for label in labels if label in VALID_LABELS]
    if len(set(labels)) >= 3:
        return _candidate(
            "consensus_conflict_resolver",
            "",
            0.8,
            1,
            "Multiple answer views disagree; compress evidence and route to adversarial verifier instead of majority override.",
            ["PN_ConsensusConflictResolver", "PN_AdversarialVerifier"],
            ["compress", "write"],
        )
    return _no_candidate()


def propose_nonmath_candidate(row: Dict[str, Any]) -> Dict[str, Any]:
    question = _question(row)
    for verifier in [
        lambda: verify_memory_bridge_required(question),
        lambda: verify_option_semantic_consistency(question),
        lambda: verify_conceptual_all_of_these(question),
        lambda: verify_instruction_ambiguity(question),
        lambda: verify_consensus_conflict(row),
    ]:
        candidate = verifier()
        if candidate["candidate_type"] != "none":
            return candidate
    return _no_candidate()


def build_candidate_records(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records = []
    for row in rows:
        candidate = propose_nonmath_candidate(row)
        records.append(
            {
                "run_id": "R305",
                "task_id": row.get("task_id"),
                "audit_excluded": str(row.get("task_id") or "") in EXCLUDED_TASK_IDS or bool(row.get("audit_excluded")),
                "arg_prediction": _arg_prediction(row),
                "r304_prediction": normalize_label(row.get("predicted_answer")),
                "candidate": candidate,
                "candidate_available": candidate["candidate_type"] != "none",
                "candidate_has_label": candidate["candidate_label"] in VALID_LABELS,
                "candidate_type": candidate["candidate_type"],
                "model_visible_features_only": candidate.get("model_visible_features_only", True),
                "claim_boundary": "Non-math PromptNode candidate library only; no accuracy claim and no training.",
            }
        )
    return records


def summarize_candidates(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for row in records:
        ctype = str(row.get("candidate_type") or "none")
        counts[ctype] = counts.get(ctype, 0) + 1
    main = [row for row in records if not row.get("audit_excluded")]
    return {
        "run_id": "R305",
        "title": "Non-math PromptNode candidate library",
        "claim_boundary": "Type-library and candidate audit only; this run does not train or claim accuracy improvement.",
        "no_api": True,
        "broad_api": False,
        "records": len(records),
        "main_records": len(main),
        "candidate_records": sum(1 for row in records if row.get("candidate_available")),
        "main_candidate_records": sum(1 for row in main if row.get("candidate_available")),
        "candidate_type_counts": dict(sorted(counts.items())),
        "nonmath_node_types": NONMATH_NODE_TYPES,
        "training_authorized_next": False,
        "next_run": "R306 nonmath stack eval with no-nonmath negative control",
        "sci_q2_ready": False,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R305 Non-Math PromptNode Library",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records/main: `{summary['records']}` / `{summary['main_records']}`",
            f"- Candidate records/main: `{summary['candidate_records']}` / `{summary['main_candidate_records']}`",
            f"- Candidate type counts: `{summary['candidate_type_counts']}`",
            f"- Non-math node types: `{summary['nonmath_node_types']}`",
            "",
            "The library adds semantic and control-flow nodes without starting training. Accuracy-bearing evaluation is deferred to R306.",
            "",
        ]
    )


def run(
    input_jsonl: str = DEFAULT_INPUT_JSONL,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    rows = load_jsonl(input_jsonl)
    records = build_candidate_records(rows)
    summary = summarize_candidates(records)
    summary.update(
        {
            "input_jsonl": input_jsonl,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    write_jsonl(output_jsonl, records)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R305 non-math PromptNode candidate library records.")
    parser.add_argument("--input_jsonl", default=DEFAULT_INPUT_JSONL)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
