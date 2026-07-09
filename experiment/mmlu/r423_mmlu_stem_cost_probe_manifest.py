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

from experiment.mmlu.r349_fresh_tool_promptnode_eval_preflight import _leakage


DEFAULT_STEM_JSONL = "experiment/mmlu/mmlu_stem_transfer100.jsonl"
DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r423_mmlu_stem_cost_probe_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r423_mmlu_stem_cost_probe_manifest_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r423_mmlu_stem_cost_probe_manifest_report.md"
TASK_LIMIT = 12


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


def _baseline_messages(question: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": "You answer MMLU STEM multiple-choice questions. Use only the visible item."},
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Visible multiple-choice item:",
                    question,
                    "",
                    "Return compact JSON with keys selected_label, confidence, rationale.",
                ]
            ),
        },
    ]


def _promptnode_stack_messages(question: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You execute a cost-probe PromptNode stack for MMLU STEM reasoning. This run measures token/cost; "
                "it is not used as a new accuracy claim."
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
                    "- InstructionVerifierPN extracts the mathematical or scientific task objective.",
                    "- ToolResourcePN writes a lightweight symbolic/checking plan when arithmetic or formulas are present.",
                    "- OptionVerifierPN checks each visible option against the plan.",
                    "- SafetyGatePN forwards one option only when evidence is sufficient; otherwise it abstains.",
                    "",
                    "PromptEdges:",
                    "- Read the visible item, write structured evidence, then forward only one visible option label or abstain.",
                    "- Do not use hidden labels or dataset metadata.",
                    "",
                    "Return compact JSON with keys candidate_label, confidence, evidence_count, promptnode_roles, promptedge_permissions, lifecycle_actions, rationale.",
                ]
            ),
        },
    ]


def _records_for_task(task: Dict[str, Any]) -> List[Dict[str, Any]]:
    base = {
        "run_id": "R423",
        "task_id": task["task_id"],
        "dataset_family": "mmlu_stem",
        "subject": task.get("subject"),
        "evaluation_only": {"true_answer": str(task.get("answer") or "").strip().upper()[:1]},
        "api_required": True,
        "model": "gpt-4o-2024-08-06",
    }
    return [
        {
            **base,
            "control_variant": "arg_direct_cost_probe",
            "model_visible_messages": _baseline_messages(task["question"]),
            "max_completion_tokens": 180,
        },
        {
            **base,
            "control_variant": "promptnode_stack_cost_probe",
            "model_visible_messages": _promptnode_stack_messages(task["question"]),
            "max_completion_tokens": 260,
        },
    ]


def build_cost_probe_manifest(stem_jsonl: str = DEFAULT_STEM_JSONL, task_limit: int = TASK_LIMIT) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    tasks = _load_jsonl(stem_jsonl)[:task_limit]
    records: List[Dict[str, Any]] = []
    for task in tasks:
        records.extend(_records_for_task(task))
    violations = _leakage(records)
    variants = Counter(row["control_variant"] for row in records)
    return records, {
        "run_id": "R423",
        "title": "MMLU STEM cost probe manifest",
        "claim_boundary": (
            "R423 freezes a small cost probe for MMLU STEM. It measures token/cost only and cannot create a new "
            "accuracy claim."
        ),
        "no_api": True,
        "broad_api": False,
        "tasks": len(tasks),
        "api_records": len(records),
        "variant_counts": dict(sorted(variants.items())),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "cost_probe_authorized_next": not violations and len(tasks) == task_limit,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R424_mmlu_stem_cost_probe_api_execution",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R423 MMLU STEM Cost Probe Manifest",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- API records: `{summary['api_records']}`",
            f"- Variant counts: `{summary['variant_counts']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    stem_jsonl: str = DEFAULT_STEM_JSONL,
    task_limit: int = TASK_LIMIT,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_cost_probe_manifest(stem_jsonl=stem_jsonl, task_limit=task_limit)
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build MMLU STEM cost probe manifest.")
    parser.add_argument("--stem_jsonl", default=DEFAULT_STEM_JSONL)
    parser.add_argument("--task_limit", type=int, default=TASK_LIMIT)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
