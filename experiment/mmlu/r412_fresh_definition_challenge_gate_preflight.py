from __future__ import annotations

import argparse
import csv
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

from experiment.mmlu.r349_fresh_tool_promptnode_eval_preflight import (
    DEFAULT_MMLU_TEST_DIR,
    EXCLUDED_JSONL_PATHS,
    _api_record,
    _leakage,
    _question,
    _used_task_ids,
)


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r412_fresh_definition_challenge_gate_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r412_fresh_definition_challenge_gate_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r412_fresh_definition_challenge_gate_preflight_report.md"
SUBJECTS = ["logical_fallacies", "moral_disputes", "philosophy"]
TASKS_PER_SUBJECT = 8
EXTRA_EXCLUDES = [
    "experiment/mmlu/run_logs/mmlu_r388_mixed_nonmath_option_binding_manifest.jsonl",
    "experiment/mmlu/run_logs/mmlu_r389_mixed_nonmath_option_binding_api_results.jsonl",
    "experiment/mmlu/run_logs/mmlu_r394_larger_mixed_nonmath_fresh_manifest.jsonl",
    "experiment/mmlu/run_logs/mmlu_r395_larger_mixed_nonmath_fresh_api_results.jsonl",
    "experiment/mmlu/run_logs/mmlu_r408_nonmath_curriculum_fresh_manifest.jsonl",
    "experiment/mmlu/run_logs/mmlu_r409_nonmath_curriculum_api_results.jsonl",
]


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
    target.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _load_subject_tasks(root: str, subject: str, count: int, used: set[str]) -> List[Dict[str, Any]]:
    csv_path = Path(root) / f"{subject}_test.csv"
    tasks: List[Dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for row_index, row in enumerate(reader):
            if len(row) < 6:
                continue
            canonical = f"MMLU-{subject}_test-{row_index}"
            nonstem = f"MMLU-nonstem-{subject}_test-{row_index}"
            if canonical in used or nonstem in used:
                continue
            tasks.append(
                {
                    "run_id": "R412",
                    "task_id": nonstem,
                    "dataset_family": "mmlu_nonstem",
                    "subject": subject,
                    "row_index": row_index,
                    "question": _question(row),
                    "evaluation_only": {"true_answer": str(row[5]).strip().upper()[:1]},
                }
            )
            if len(tasks) >= count:
                break
    return tasks


def _definition_challenge_messages(question: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You execute a PromptNode-Augmented MAS graph for concept-definition multiple-choice reasoning. "
                "The DefinitionChallengeGate is fixed before this fresh run: it may forward only if definition anchor, "
                "adversarial challenge, option binding, and conflict checks all support one visible option."
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Visible multiple-choice item:",
                    question,
                    "",
                    "Virtual graph:",
                    "- InstructionAmbiguityVerifierPN extracts the operative instruction and negation/scope.",
                    "- ConceptDefinitionAnchorPN writes the local concept definition or fallacy boundary.",
                    "- OptionSemanticConsistencyVerifierPN maps every visible option to the definition anchor.",
                    "- AdversarialVerifierPN defends the nearest distractor before any label can be forwarded.",
                    "- ContradictionDetectorPN blocks a candidate when rationale, option text, or instruction conflict.",
                    "- ConsensusConflictResolverPN applies DefinitionChallengeGate.",
                    "",
                    "PromptEdges:",
                    "- DefinitionAnchorPromptEdge: every option judgment must cite or reject the anchor.",
                    "- AdversarialChallengePromptEdge: a surviving candidate must beat the nearest distractor.",
                    "- ConflictResolutionPromptEdge: any hard contradiction blocks forwarding.",
                    "- OptionBindingPromptEdge: candidate_label must be exactly one visible option letter or empty.",
                    "",
                    "DefinitionChallengeGate fields:",
                    "- confidence, node_agreement_count, node_disagreement_count, contradiction_count.",
                    "- ambiguity_flag, definition_anchor_confidence, adversarial_challenge_pass.",
                    "- nearest_distractor, nearest_distractor_margin, option_binding_contract_pass, memory_bridge_write_confidence.",
                    "",
                    "Return raw JSON object only, no markdown fence and no commentary. Required keys: candidate_label, confidence, node_agreement_count, node_disagreement_count, contradiction_count, ambiguity_flag, definition_anchor_confidence, adversarial_challenge_pass, nearest_distractor, nearest_distractor_margin, option_binding_contract_pass, memory_bridge_write_confidence, promptnode_outputs, promptedge_contracts, rationale, abstain_reason.",
                ]
            ),
        },
    ]


def _definition_challenge_record(task: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "run_id": "R412",
        "task_id": task["task_id"],
        "dataset_family": task["dataset_family"],
        "subject": task["subject"],
        "row_index": task["row_index"],
        "control_variant": "definition_challenge_candidate_api",
        "evaluation_only": task["evaluation_only"],
        "model_visible_messages": _definition_challenge_messages(task["question"]),
        "api_required": True,
        "max_completion_tokens": 360,
        "model": "gpt-4o-2024-08-06",
    }


def build_definition_challenge_preflight(mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    used = _used_task_ids(EXCLUDED_JSONL_PATHS + EXTRA_EXCLUDES)
    tasks: List[Dict[str, Any]] = []
    for subject in SUBJECTS:
        tasks.extend(_load_subject_tasks(mmlu_test_dir, subject, TASKS_PER_SUBJECT, used))
    records: List[Dict[str, Any]] = []
    for task in tasks:
        arg = _api_record(task)
        arg["run_id"] = "R412"
        arg["control_variant"] = "arg_baseline_direct_api"
        records.append(arg)
        records.append(_definition_challenge_record(task))
    violations = _leakage(records)
    variants = Counter(row["control_variant"] for row in records)
    subject_counts = Counter(task["subject"] for task in tasks)
    return records, {
        "run_id": "R412",
        "title": "Fresh DefinitionChallenge gate preflight",
        "claim_boundary": (
            "R412 builds a fresh manifest for a fixed DefinitionChallenge gate hypothesis from R411. "
            "It does not execute API or support a paper claim."
        ),
        "no_api": True,
        "broad_api": False,
        "subjects": len(subject_counts),
        "subject_counts": dict(sorted(subject_counts.items())),
        "tasks_per_subject": TASKS_PER_SUBJECT,
        "tasks": len(tasks),
        "api_records": len(records),
        "planned_arg_baseline_calls": variants.get("arg_baseline_direct_api", 0),
        "planned_definition_challenge_calls": variants.get("definition_challenge_candidate_api", 0),
        "variant_counts": dict(sorted(variants.items())),
        "prospective_gate": "definition_challenge_gate",
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_execution_authorized_next": not violations and len(tasks) == len(SUBJECTS) * TASKS_PER_SUBJECT,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R413_definition_challenge_gate_api_execution",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R412 Fresh DefinitionChallenge Gate Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Subjects/tasks: `{summary['subjects']}/{summary['tasks']}`",
            f"- API records: `{summary['api_records']}`",
            f"- Variant counts: `{summary['variant_counts']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_definition_challenge_preflight(mmlu_test_dir=mmlu_test_dir)
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R412 fresh DefinitionChallenge gate preflight.")
    parser.add_argument("--mmlu_test_dir", default=DEFAULT_MMLU_TEST_DIR)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
