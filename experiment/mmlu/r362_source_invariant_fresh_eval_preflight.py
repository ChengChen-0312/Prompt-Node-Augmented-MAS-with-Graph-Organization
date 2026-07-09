from __future__ import annotations

import argparse
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
    FORBIDDEN_PROMPT_FIELDS,
    NONSTEM_SUBJECTS,
    STEM_SUBJECTS,
    _api_record,
    _leakage,
    _load_subject_records,
    _used_task_ids,
)


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r362_source_invariant_fresh_eval_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r362_source_invariant_fresh_eval_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r362_source_invariant_fresh_eval_preflight_report.md"
EXTRA_EXCLUDED_JSONL_PATHS = [
    "experiment/mmlu/run_logs/mmlu_r352_fresh_coverage_promptnode_expansion_preflight_results.jsonl",
    "experiment/mmlu/run_logs/mmlu_r354_fresh_eval_after_coverage_expansion_api_manifest.jsonl",
    "experiment/mmlu/run_logs/mmlu_r354_fresh_eval_after_coverage_expansion_local_tool_results.jsonl",
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


def _candidate_messages(question: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a PromptNode candidate generator for a source-invariant MAS graph policy. Use only visible "
                "stem/options. Do not assume hidden labels."
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Visible multiple-choice item:",
                    question,
                    "",
                    "Available PromptNode families:",
                    "- ToolResourceVerifier: compute/check numeric, symbolic, formula, or conservation evidence when possible",
                    "- PassageEntailmentVerifier: use only quoted passage or visible case facts",
                    "- DefinitionFallacyVerifier: use exact definition/theory matches",
                    "- OptionSemanticConsistencyVerifier: compare all options against the stem",
                    "- ContradictionDetector: identify options contradicted by visible evidence",
                    "- SafetyGate: write warning-only evidence if no concrete candidate exists",
                    "",
                    "PromptEdge contract:",
                    "- read: visible problem only",
                    "- write: structured evidence checks",
                    "- forward: only exact single-option candidate with evidence; otherwise empty candidate_label",
                    "",
                    "Return compact JSON with keys candidate_label, confidence, evidence_count, promptnode_family, candidate_type, promptedge_contract_pass, rationale.",
                ]
            ),
        },
    ]


def _candidate_record(task: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "run_id": "R362",
        "task_id": task["task_id"],
        "dataset_family": task["dataset_family"],
        "subject": task["subject"],
        "row_index": task["row_index"],
        "control_variant": "promptnode_candidate_api",
        "evaluation_only": task["evaluation_only"],
        "model_visible_messages": _candidate_messages(task["question"]),
        "api_required": True,
        "max_completion_tokens": 220,
        "model": "gpt-4o-2024-08-06",
    }


def build_fresh_preflight(mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    used = _used_task_ids(EXCLUDED_JSONL_PATHS + EXTRA_EXCLUDED_JSONL_PATHS)
    stem = _load_subject_records(mmlu_test_dir, STEM_SUBJECTS, "mmlu_stem", 4, used)[:24]
    nonstem = _load_subject_records(mmlu_test_dir, NONSTEM_SUBJECTS, "mmlu_nonstem", 3, used)[:24]
    tasks = stem + nonstem
    records = []
    for task in tasks:
        arg = _api_record(task)
        arg["run_id"] = "R362"
        arg["control_variant"] = "arg_baseline_direct_api"
        records.append(arg)
        records.append(_candidate_record(task))
    violations = _leakage(records)
    task_ids = {task["task_id"] for task in tasks}
    overlap = task_ids & used
    family_counts = Counter(task["dataset_family"] for task in tasks)
    variant_counts = Counter(row["control_variant"] for row in records)
    return records, {
        "run_id": "R362",
        "title": "Source-invariant fresh eval preflight",
        "claim_boundary": (
            "R362 builds a fresh MMLU manifest for ARG baseline and PromptNode candidate API calls. It does not "
            "execute API; the R360 source-invariant gate will be applied after candidate responses are collected."
        ),
        "no_api": True,
        "broad_api": False,
        "policy_model": "R360_source_invariant_graph_policy",
        "policy_threshold": 0.7,
        "tasks": len(tasks),
        "task_family_counts": dict(sorted(family_counts.items())),
        "api_records": len(records),
        "variant_counts": dict(sorted(variant_counts.items())),
        "planned_arg_baseline_calls": variant_counts.get("arg_baseline_direct_api", 0),
        "planned_promptnode_candidate_calls": variant_counts.get("promptnode_candidate_api", 0),
        "api_calls_planned": len(records),
        "overlap_with_excluded_task_count": len(overlap),
        "overlap_with_excluded_task_ids": sorted(overlap),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "uses_true_answers_in_prompt": False,
        "api_execution_authorized_next": not violations and len(tasks) == 48 and not overlap,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R363_source_invariant_fresh_eval_api_execution",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R362 Source-Invariant Fresh Eval Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- API records: `{summary['api_records']}`",
            f"- Variants: `{summary['variant_counts']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            f"- API execution authorized next: `{summary['api_execution_authorized_next']}`",
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
    records, summary = build_fresh_preflight(mmlu_test_dir=mmlu_test_dir)
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R362 source-invariant fresh eval preflight.")
    parser.add_argument("--mmlu_test_dir", default=DEFAULT_MMLU_TEST_DIR)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
