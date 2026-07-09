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
from experiment.mmlu.r382_plain_requery_control_preflight import _extract_question


DEFAULT_R394_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r394_larger_mixed_nonmath_fresh_manifest.jsonl"
DEFAULT_R397_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r397_larger_mixed_error_taxonomy_summary.json"
DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r399_contrastive_verifier_targeted_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r399_contrastive_verifier_targeted_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r399_contrastive_verifier_targeted_preflight_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


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


def _contrastive_messages(question: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are PN_ContrastiveOptionVerifier and PN_ConceptDefinitionAnchor with PE_RejectNearestDistractor "
                "and PE_EvidenceSpecificityGate. Use only the visible item and options."
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Visible multiple-choice item:",
                    question,
                    "",
                    "Graph path:",
                    "1. Identify the best candidate option and the nearest plausible distractor.",
                    "2. Write a short concept/definition anchor needed for the decision.",
                    "3. Reject the distractor using a visible clue or a task-specific concept distinction.",
                    "4. Bind candidate_label only if the distractor is explicitly rejected and the evidence is specific.",
                    "",
                    "Rules:",
                    "- Do not forward generic plausibility.",
                    "- If the nearest distractor cannot be rejected, leave candidate_label empty.",
                    "- Set promptedge_contract_pass true only when candidate_label, rejected_distractor_label, definition_anchor, and evidence_count >= 1 are all present.",
                    "",
                    "Return compact JSON with keys candidate_label, confidence, evidence_count, promptnode_family, candidate_type, rejected_distractor_label, definition_anchor, evidence_specificity, promptedge_contract_pass, rationale.",
                ]
            ),
        },
    ]


def build_targeted_preflight(
    r394_manifest_jsonl: str = DEFAULT_R394_MANIFEST_JSONL,
    r397_summary_json: str = DEFAULT_R397_SUMMARY_JSON,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    r397 = _load_json(r397_summary_json)
    target_ids = list(
        dict.fromkeys(
            list(r397.get("wrong_forward_task_ids", []))
            + list(r397.get("candidate_correct_but_blocked_task_ids", []))
            + list(r397.get("abstention_task_ids", []))
            + list(r397.get("candidate_wrong_missed_task_ids", []))
        )
    )
    source_rows = {
        row.get("task_id"): row
        for row in _load_jsonl(r394_manifest_jsonl)
        if row.get("control_variant") == "semantic_option_binding_candidate_api"
    }
    records = []
    for task_id in target_ids:
        row = source_rows.get(task_id)
        if not row:
            continue
        records.append(
            {
                "run_id": "R399",
                "task_id": task_id,
                "dataset_family": row.get("dataset_family"),
                "subject": row.get("subject"),
                "row_index": row.get("row_index"),
                "control_variant": "contrastive_verifier_candidate_api",
                "evaluation_only": row.get("evaluation_only"),
                "model_visible_messages": _contrastive_messages(_extract_question(row)),
                "api_required": True,
                "max_completion_tokens": 260,
                "model": row.get("model") or "gpt-4o-2024-08-06",
            }
        )
    violations = _leakage(records)
    return records, {
        "run_id": "R399",
        "title": "Contrastive verifier targeted preflight",
        "claim_boundary": (
            "R399 builds a targeted diagnostic manifest for R397 error tasks. It is not a fresh-paper claim."
        ),
        "no_api": True,
        "broad_api": False,
        "targeted_tasks": len(target_ids),
        "api_records": len(records),
        "planned_contrastive_candidate_calls": len(records),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_execution_authorized_next": not violations and len(records) == len(target_ids),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R400_contrastive_verifier_targeted_api_execution",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R399 Contrastive Verifier Targeted Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Targeted tasks: `{summary['targeted_tasks']}`",
            f"- API records: `{summary['api_records']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r394_manifest_jsonl: str = DEFAULT_R394_MANIFEST_JSONL,
    r397_summary_json: str = DEFAULT_R397_SUMMARY_JSON,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_targeted_preflight(r394_manifest_jsonl=r394_manifest_jsonl, r397_summary_json=r397_summary_json)
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R399 targeted contrastive verifier preflight.")
    parser.add_argument("--r394_manifest_jsonl", default=DEFAULT_R394_MANIFEST_JSONL)
    parser.add_argument("--r397_summary_json", default=DEFAULT_R397_SUMMARY_JSON)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
