from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R337_RESULTS = "experiment/mmlu/run_logs/mmlu_r337_prospective_selector_eval_expand24_results.jsonl"
DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r341_answer_bearing_candidate_generator_probe_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r341_answer_bearing_candidate_generator_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r341_answer_bearing_candidate_generator_preflight_report.md"

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


def _visible_item(row: Dict[str, Any]) -> str:
    content = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", []) if message.get("role") == "user")
    content = re.sub(r"^Held-out MMLU multiple-choice item:\s*", "", content.strip())
    content = content.split("\n\nPromptNode identities:", 1)[0]
    return content.strip()


def _family_for(row: Dict[str, Any], item: str) -> str:
    text = item.lower()
    subject = str(row.get("subject") or "").lower()
    if any(word in text for word in ["reflected", "reflection", "coordinate", "vertices", "slope"]):
        return "coordinate_geometry_verifier"
    chemistry_pattern = re.search(r"\b(reaction|redox|oxidation|reduction|coefficient|mno4|mn2|io3|h2o|acidic|basic)\b", text)
    if "chem" in subject or chemistry_pattern:
        return "chemistry_balancer_verifier"
    if any(word in text for word in ["group", "vector", "null space", "rank", "polynomial", "field", "operator"]):
        return "algebraic_structure_verifier"
    return "option_by_option_symbolic_verifier"


def _messages(item: str, family: str, baseline: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "You are an answer-bearing PromptNode verifier. Use only visible stem/options. Do not assume hidden labels.",
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Visible multiple-choice item:",
                    item,
                    "",
                    f"ARG initial choice: {baseline}",
                    f"Verifier family: {family}",
                    "",
                    "Task:",
                    "- Verify options independently.",
                    "- Emit candidate_label only if visible evidence supports a specific option.",
                    "- Otherwise emit candidate_label as empty string.",
                    "",
                    "Return compact JSON with keys candidate_label, confidence, evidence_count, verifier_family, rationale.",
                ]
            ),
        },
    ]


def _leakage(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    violations = []
    for row in rows:
        prompt = "\n".join(message["content"] for message in row["model_visible_messages"]).lower()
        for field in FORBIDDEN_PROMPT_FIELDS:
            if field in prompt:
                violations.append({"task_id": row.get("task_id", ""), "field": field})
    return violations


def build_generator_preflight(r337_results: str = DEFAULT_R337_RESULTS) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    source_rows = [
        row
        for row in _load_jsonl(r337_results)
        if row.get("control_variant") == "selector_promptnode_promptedge_policy" and row.get("is_correct") is False
    ]
    records: List[Dict[str, Any]] = []
    for row in source_rows:
        item = _visible_item(row)
        family = _family_for(row, item)
        records.append(
            {
                "run_id": "R341",
                "task_id": row.get("task_id"),
                "dataset_family": row.get("dataset_family"),
                "subject": row.get("subject"),
                "baseline_prediction": row.get("baseline_prediction"),
                "verifier_family": family,
                "model": row.get("model") or "gpt-4o-2024-08-06",
                "max_completion_tokens": 220,
                "model_visible_messages": _messages(item, family, row.get("baseline_prediction", "")),
                "evaluation_only": {"true_answer": row.get("true_answer")},
                "api_required": True,
            }
        )
    violations = _leakage(records)
    return records, {
        "run_id": "R341",
        "title": "Answer-bearing candidate generator preflight",
        "claim_boundary": (
            "R341 prepares a targeted mechanism-debug probe on R337 wrong tasks. It is not a paper claim and does not "
            "authorize broader API expansion."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(records),
        "verifier_family_counts": dict(sorted({row["verifier_family"]: sum(1 for item in records if item["verifier_family"] == row["verifier_family"]) for row in records}.items())),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "uses_true_answers_in_prompt": False,
        "api_probe_authorized_next": not violations and bool(records),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R342_answer_bearing_candidate_generator_api_probe",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R341 Answer-Bearing Candidate Generator Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records: `{summary['records']}`",
            f"- Verifier families: `{summary['verifier_family_counts']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            f"- API probe authorized next: `{summary['api_probe_authorized_next']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r337_results: str = DEFAULT_R337_RESULTS,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_generator_preflight(r337_results=r337_results)
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R341 answer-bearing verifier preflight.")
    parser.add_argument("--r337_results", default=DEFAULT_R337_RESULTS)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
