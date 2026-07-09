from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R362_MANIFEST = "experiment/mmlu/run_logs/mmlu_r362_source_invariant_fresh_eval_manifest.jsonl"
DEFAULT_R363_RESULTS = "experiment/mmlu/run_logs/mmlu_r363_source_invariant_fresh_eval_api_results.jsonl"
DEFAULT_R365_SUMMARY = "experiment/mmlu/res_logs/mmlu_r365_wrong_forward_and_missed_fix_analysis_summary.json"
DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r368_adversarial_verifier_preflight_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r368_adversarial_verifier_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r368_adversarial_verifier_preflight_report.md"
FORBIDDEN_PROMPT_FIELDS = {"task_id", "true_answer", "gold_answer", "is_correct", "evaluation_only", "source_ref_hash"}


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


def _question_from_record(row: Dict[str, Any]) -> str:
    prompt = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", []) if message.get("role") == "user")
    if "Visible multiple-choice item:" in prompt:
        body = prompt.split("Visible multiple-choice item:", 1)[1]
        return body.split("\n\nAvailable PromptNode families:", 1)[0].strip()
    body = prompt.split("Solve this multiple-choice item using only the visible question.", 1)[-1]
    return body.split("Return compact JSON", 1)[0].strip()


def _leakage(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    violations = []
    for row in rows:
        prompt = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", [])).lower()
        for field in FORBIDDEN_PROMPT_FIELDS:
            if field in prompt:
                violations.append({"task_id": row.get("task_id", ""), "variant": row.get("control_variant", ""), "field": field})
    return violations


def _adversarial_messages(question: str, current_candidate: str, current_rationale: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "You are an adversarial PromptNode verifier. Use only visible text and the given prior candidate; do not assume hidden labels.",
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Visible multiple-choice item:",
                    question,
                    "",
                    f"Prior candidate_label: {current_candidate}",
                    f"Prior candidate rationale: {current_rationale[:700]}",
                    "",
                    "Task:",
                    "- Try to falsify the prior candidate.",
                    "- If a different option is independently better supported, emit that candidate_label.",
                    "- If the prior candidate is unsafe but no replacement is justified, emit block_forward=true and empty candidate_label.",
                    "",
                    "Return compact JSON with keys candidate_label, confidence, evidence_count, block_forward, promptnode_family, candidate_type, rationale.",
                ]
            ),
        },
    ]


def _domain_messages(question: str, subject: str, arg_prediction: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "You are a domain-specialized PromptNode verifier. Use only visible stem/options; do not assume hidden labels.",
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Visible multiple-choice item:",
                    question,
                    "",
                    f"Subject: {subject}",
                    f"ARG initial choice: {arg_prediction}",
                    "",
                    "Task:",
                    "- For chemistry/physics, derive formula, conservation, or concept evidence.",
                    "- For history/passage tasks, cite only visible source/fact entailment.",
                    "- For abstract math, check theorem assumptions and counterexamples.",
                    "- Emit candidate_label only with independent evidence; otherwise empty.",
                    "",
                    "Return compact JSON with keys candidate_label, confidence, evidence_count, promptnode_family, candidate_type, rationale.",
                ]
            ),
        },
    ]


def build_adversarial_preflight(
    r362_manifest: str = DEFAULT_R362_MANIFEST,
    r363_results: str = DEFAULT_R363_RESULTS,
    r365_summary: str = DEFAULT_R365_SUMMARY,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    manifest_rows = _load_jsonl(r362_manifest)
    source_by_task = {
        row.get("task_id"): row for row in manifest_rows if row.get("control_variant") == "promptnode_candidate_api"
    }
    result_by_task = {row.get("task_id"): row for row in _load_jsonl(r363_results)}
    r365 = _load_json(r365_summary)
    target_tasks = list(r365.get("wrong_forward_task_ids", [])) + list(r365.get("missed_fix_task_ids", []))
    records: List[Dict[str, Any]] = []
    for task_id in target_tasks:
        source = source_by_task.get(task_id, {})
        result = result_by_task.get(task_id, {})
        question = _question_from_record(source)
        if task_id in set(r365.get("wrong_forward_task_ids", [])):
            parsed = result.get("candidate_parsed_response") or {}
            messages = _adversarial_messages(question, result.get("candidate_label", ""), parsed.get("rationale", ""))
            variant = "adversarial_candidate_verifier_api"
        else:
            messages = _domain_messages(question, result.get("subject", ""), result.get("arg_prediction", ""))
            variant = "domain_specialized_candidate_api"
        records.append(
            {
                "run_id": "R368",
                "task_id": task_id,
                "dataset_family": result.get("dataset_family") or source.get("dataset_family"),
                "subject": result.get("subject") or source.get("subject"),
                "control_variant": variant,
                "evaluation_only": source.get("evaluation_only"),
                "model_visible_messages": messages,
                "api_required": True,
                "max_completion_tokens": 240,
                "model": "gpt-4o-2024-08-06",
            }
        )
    violations = _leakage(records)
    variant_counts = Counter(row["control_variant"] for row in records)
    return records, {
        "run_id": "R368",
        "title": "Adversarial verifier preflight",
        "claim_boundary": (
            "R368 builds a targeted mechanism-debug API manifest for R365 wrong-forward and missed-fix tasks. It is "
            "not a paper claim."
        ),
        "no_api": True,
        "broad_api": False,
        "target_task_count": len(target_tasks),
        "records": len(records),
        "variant_counts": dict(sorted(variant_counts.items())),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "uses_true_answers_in_prompt": False,
        "api_probe_authorized_next": not violations and bool(records),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R369_adversarial_verifier_api_probe",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R368 Adversarial Verifier Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Target tasks: `{summary['target_task_count']}`",
            f"- Records: `{summary['records']}`",
            f"- Variants: `{summary['variant_counts']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r362_manifest: str = DEFAULT_R362_MANIFEST,
    r363_results: str = DEFAULT_R363_RESULTS,
    r365_summary: str = DEFAULT_R365_SUMMARY,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_adversarial_preflight(
        r362_manifest=r362_manifest,
        r363_results=r363_results,
        r365_summary=r365_summary,
    )
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R368 adversarial verifier preflight.")
    parser.add_argument("--r362_manifest", default=DEFAULT_R362_MANIFEST)
    parser.add_argument("--r363_results", default=DEFAULT_R363_RESULTS)
    parser.add_argument("--r365_summary", default=DEFAULT_R365_SUMMARY)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
