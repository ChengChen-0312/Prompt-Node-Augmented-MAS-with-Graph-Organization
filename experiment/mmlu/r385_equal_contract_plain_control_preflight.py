from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r349_fresh_tool_promptnode_eval_preflight import _leakage
from experiment.mmlu.r382_plain_requery_control_preflight import DEFAULT_R379_MANIFEST_JSONL, _extract_question


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r385_equal_contract_plain_control_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r385_equal_contract_plain_control_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r385_equal_contract_plain_control_preflight_report.md"


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


def _equal_contract_messages(question: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "You are a careful MMLU multiple-choice solver. Use only the visible passage, question, and options.",
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Visible multiple-choice item:",
                    question,
                    "",
                    "Rules:",
                    "- Select exactly one option only when it is best supported by the visible item.",
                    "- If your rationale supports one option as the answer, candidate_label must be that option label.",
                    "- Set evidence_count to the number of distinct visible facts used.",
                    "",
                    "Return compact JSON with keys candidate_label, confidence, evidence_count, candidate_type, rationale.",
                ]
            ),
        },
    ]


def build_equal_contract_preflight(r379_manifest_jsonl: str = DEFAULT_R379_MANIFEST_JSONL) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    source_rows = _load_jsonl(r379_manifest_jsonl)
    candidate_rows = [row for row in source_rows if row.get("control_variant") == "history_option_binding_candidate_api"]
    records = []
    for row in candidate_rows:
        question = _extract_question(row)
        records.append(
            {
                "run_id": "R385",
                "task_id": row.get("task_id"),
                "dataset_family": row.get("dataset_family"),
                "subject": row.get("subject"),
                "row_index": row.get("row_index"),
                "control_variant": "equal_contract_plain_control_api",
                "evaluation_only": row.get("evaluation_only"),
                "model_visible_messages": _equal_contract_messages(question),
                "api_required": True,
                "max_completion_tokens": 220,
                "model": row.get("model") or "gpt-4o-2024-08-06",
            }
        )
    violations = _leakage(records)
    r379_task_ids = {row.get("task_id") for row in candidate_rows}
    selected_task_ids = {row.get("task_id") for row in records}
    prompt_text = "\n".join(
        message.get("content", "") for row in records for message in row.get("model_visible_messages", [])
    ).lower()
    return records, {
        "run_id": "R385",
        "title": "Equal-contract plain control preflight",
        "claim_boundary": (
            "R385 builds a same-task plain control with the same structured answer contract as R380 but without "
            "PromptNode, PromptEdge, or graph terminology."
        ),
        "no_api": True,
        "broad_api": False,
        "tasks": len(selected_task_ids),
        "api_records": len(records),
        "planned_equal_contract_plain_calls": len(records),
        "same_task_set_as_r379": selected_task_ids == r379_task_ids and bool(selected_task_ids),
        "graph_terms_absent": all(term not in prompt_text for term in ["promptnode", "promptedge", "graph path", "safetygate"]),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_execution_authorized_next": not violations and selected_task_ids == r379_task_ids and len(records) == 24,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R386_equal_contract_plain_control_api_execution",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R385 Equal-Contract Plain Control Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- API records: `{summary['api_records']}`",
            f"- Same task set as R379: `{summary['same_task_set_as_r379']}`",
            f"- Graph terms absent: `{summary['graph_terms_absent']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r379_manifest_jsonl: str = DEFAULT_R379_MANIFEST_JSONL,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_equal_contract_preflight(r379_manifest_jsonl=r379_manifest_jsonl)
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R385 equal-contract plain control preflight.")
    parser.add_argument("--r379_manifest_jsonl", default=DEFAULT_R379_MANIFEST_JSONL)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
