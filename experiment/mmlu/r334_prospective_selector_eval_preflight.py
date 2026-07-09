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

from experiment.mmlu.r305_nonmath_promptnode_library import propose_nonmath_candidate


DEFAULT_MMLU_TEST_DIR = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/datasets/MMLU/test"
DEFAULT_R304_JSONL = "experiment/mmlu/run_logs/mmlu_r304_multi_trigger_safety_gate_results.jsonl"
DEFAULT_R306_JSONL = "experiment/mmlu/run_logs/mmlu_r306_nonmath_stack_eval_results.jsonl"
DEFAULT_R312_JSONL = "experiment/mmlu/run_logs/mmlu_r312_nonstem_safety_replay_results.jsonl"
DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r334_prospective_selector_eval_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r334_prospective_selector_eval_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r334_prospective_selector_eval_preflight_report.md"

STEM_SUBJECTS = [
    "high_school_mathematics",
    "college_mathematics",
    "high_school_physics",
    "college_physics",
    "high_school_chemistry",
    "college_chemistry",
]
NONSTEM_SUBJECTS = [
    "business_ethics",
    "logical_fallacies",
    "philosophy",
    "moral_disputes",
    "professional_law",
    "high_school_us_history",
    "sociology",
    "world_religions",
]
VARIANTS = [
    "arg_baseline_direct",
    "selector_promptnode_promptedge_policy",
    "cost_matched_plain_requery",
]
FORBIDDEN_PROMPT_FIELDS = {"task_id", "true_answer", "gold_answer", "is_correct", "evaluation_only", "source_ref_hash"}


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
    target.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _question(row: List[str]) -> str:
    return "\n".join(
        [
            row[0].strip(),
            f"Option A: {row[1].strip()}",
            f"Option B: {row[2].strip()}",
            f"Option C: {row[3].strip()}",
            f"Option D: {row[4].strip()}",
        ]
    )


def _used_task_ids(paths: Iterable[str]) -> set[str]:
    used = set()
    for path in paths:
        for row in _load_jsonl(path):
            task_id = str(row.get("task_id") or "")
            if task_id:
                used.add(task_id)
    return used


def _load_subject_records(root: str, subjects: List[str], family: str, per_subject: int, used: set[str]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    base = Path(root)
    for subject in subjects:
        csv_path = base / f"{subject}_test.csv"
        if not csv_path.exists():
            continue
        kept = 0
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row_index, row in enumerate(reader):
                if len(row) < 6:
                    continue
                canonical = f"MMLU-{subject}_test-{row_index}"
                nonstem = f"MMLU-nonstem-{subject}_test-{row_index}"
                if canonical in used or nonstem in used:
                    continue
                question = _question(row)
                candidate = propose_nonmath_candidate({"question": question, "arg_prediction": ""})
                records.append(
                    {
                        "dataset_family": family,
                        "subject": subject,
                        "task_id": canonical if family == "mmlu_stem" else nonstem,
                        "row_index": row_index,
                        "question": question,
                        "evaluation_only": {"true_answer": str(row[5]).strip().upper()[:1]},
                        "candidate": candidate,
                    }
                )
                kept += 1
                if kept >= per_subject:
                    break
    return records


def _messages(variant: str, task: Dict[str, Any]) -> List[Dict[str, str]]:
    question = task["question"]
    if variant == "arg_baseline_direct":
        system = "You are an ARG-Designer-compatible baseline solver for MMLU multiple-choice questions."
        user = "\n".join(
            [
                "Solve this multiple-choice item using only the visible question.",
                question,
                "Return compact JSON with keys selected_label, confidence, rationale.",
            ]
        )
    elif variant == "cost_matched_plain_requery":
        system = "You answer multiple-choice questions directly using only visible text."
        user = "\n".join(
            [
                "Solve directly without PromptNodes or PromptEdges.",
                question,
                "Return compact JSON with keys selected_label, confidence, rationale.",
            ]
        )
    else:
        candidate = task.get("candidate") or {}
        system = "You are a conservative PromptNode/PromptEdge router for held-out MMLU evaluation."
        user = "\n".join(
            [
                "Held-out MMLU multiple-choice item:",
                question,
                "",
                "PromptNode identities:",
                "- PN_MemoryBridge: carry compact prior option evidence without hidden labels",
                "- PN_InstructionVerifier: detect scope, negation, and missing-context risks",
                "- PN_OptionSemanticConsistency: check option/stem semantic fit",
                "- PN_ContradictionDetector: reject options contradicted by the visible item",
                "- PN_SafetyGate: default KEEP unless a concrete high-confidence answer-bearing candidate exists",
                f"- PN_Router: candidate_type={candidate.get('candidate_type', 'none')}",
                "",
                "PromptEdges:",
                "- item_to_verifier: read; inspect only visible item text",
                "- verifier_to_safety_gate: write; write compact evidence and risk flags",
                "- safety_gate_to_router: forward; forward only high-confidence answer-bearing candidates",
                "- router_to_final: forward; KEEP_ARG when evidence is weak or warning-only",
                "",
                "Lifecycle policy: update concrete conflicts; compress warnings; prune warning-only nodes before answer override; merge agreeing nodes; upgrade repeatable high-confidence checks.",
                "Return compact JSON with keys action, final_label, confidence, evidence_checks, rationale.",
            ]
        )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _manifest_records(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for task in tasks:
        for variant in VARIANTS:
            messages = _messages(variant, task)
            rows.append(
                {
                    "run_id": "R334",
                    "task_id": task["task_id"],
                    "dataset_family": task["dataset_family"],
                    "subject": task["subject"],
                    "row_index": task["row_index"],
                    "control_variant": variant,
                    "candidate": task["candidate"],
                    "evaluation_only": task["evaluation_only"],
                    "model_visible_messages": messages,
                    "api_required": variant != "arg_baseline_direct",
                    "max_completion_tokens": 160,
                    "model": "gpt-4o-2024-08-06",
                }
            )
    return rows


def _leakage(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    violations = []
    for row in rows:
        prompt = "\n".join(message["content"] for message in row.get("model_visible_messages", [])).lower()
        for field in FORBIDDEN_PROMPT_FIELDS:
            if field.lower() in prompt:
                violations.append({"task_id": row.get("task_id", ""), "variant": row.get("control_variant", ""), "field": field})
    return violations


def build_preflight_summary(
    mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR,
    r304_jsonl: str = DEFAULT_R304_JSONL,
    r306_jsonl: str = DEFAULT_R306_JSONL,
    r312_jsonl: str = DEFAULT_R312_JSONL,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    used = _used_task_ids([r304_jsonl, r306_jsonl, r312_jsonl])
    stem = _load_subject_records(mmlu_test_dir, STEM_SUBJECTS, "mmlu_stem", 4, used)[:24]
    nonstem = _load_subject_records(mmlu_test_dir, NONSTEM_SUBJECTS, "mmlu_nonstem", 3, used)[:24]
    tasks = stem + nonstem
    records = _manifest_records(tasks)
    violations = _leakage(records)
    family_counts = Counter(task["dataset_family"] for task in tasks)
    variant_counts = Counter(row["control_variant"] for row in records)
    return records, {
        "run_id": "R334",
        "title": "Prospective selector eval preflight",
        "claim_boundary": "R334 constructs a leakage-checked held-out manifest only. It authorizes a bounded API smoke next if leakage remains clean.",
        "no_api": True,
        "broad_api": False,
        "tasks": len(tasks),
        "records": len(records),
        "task_family_counts": dict(sorted(family_counts.items())),
        "variant_counts": dict(sorted(variant_counts.items())),
        "training_overlap_count": 0,
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "estimated_api_calls_next": sum(1 for row in records if row["api_required"]),
        "api_execution_authorized_next": not violations and len(tasks) == 48,
        "sci_q2_ready": False,
        "next_required_run": "R335_prospective_selector_eval_api_smoke",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R334 Prospective Selector Eval Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- Records: `{summary['records']}`",
            f"- Family counts: `{summary['task_family_counts']}`",
            f"- Variant counts: `{summary['variant_counts']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            f"- API calls next: `{summary['estimated_api_calls_next']}`",
            f"- API execution authorized next: `{summary['api_execution_authorized_next']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_preflight_summary()
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R334 prospective selector eval preflight manifest.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
