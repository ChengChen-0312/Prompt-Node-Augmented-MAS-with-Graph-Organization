import argparse
import json
import os
import re
import sys
from collections import defaultdict
from typing import Any, Dict, Iterable, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r162_mmlu_arg_transfer_eval"
CLAIM_BOUNDARY = (
    "same-model ARG-Designer checkpoint transfer evaluation on MMLU STEM transfer100 only; "
    "this run establishes a migration/robustness baseline and does not evaluate the "
    "PromptNode/PromptEdge method, AQuA sync20 accuracy, or SCI-Q2 readiness"
)

DEFAULT_SUMMARY_JSONL = "experiment/mmlu/res_logs/mmlu_r162_transfer_eval_summary.jsonl"
DEFAULT_RESULTS_JSONL = "experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl"
DEFAULT_LOG_PATH = "experiment/mmlu/run_logs/mmlu_r162_transfer_eval.log"
DEFAULT_OUTPUT_JSON = "experiment/mmlu/res_logs/mmlu_r162_transfer_eval_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r162_transfer_eval_report.md"
LLM_NAME = "gpt-4o-2024-08-06"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _read_text(path: str) -> str:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return f.read()


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _last_jsonl_row(path: str) -> Dict[str, Any]:
    rows = _read_jsonl(path)
    return rows[-1] if rows else {}


def _detect_errors(text: str) -> List[str]:
    error_patterns = {
        "Traceback": r"\bTraceback\b",
        "RuntimeError": r"\bRuntimeError\b",
        "APIError": r"\bAPIError\b",
        "AuthenticationError": r"\bAuthenticationError\b",
        "HTTP 401": r"\b(?:HTTP\s*)?401\b.*(?:Unauthorized|Authentication|auth)",
        "HTTP 429": r"\b(?:HTTP\s*)?429\b.*(?:quota|rate|limit|insufficient)",
        "insufficient_quota": r"\binsufficient_quota\b",
        "Killed": r"\bKilled\b",
        "NaN": r"\bNaN\b|\bnan\b",
    }
    return [
        name
        for name, pattern in error_patterns.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]


def _subject_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    for row in rows:
        subject = row.get("subject", "unknown")
        counts[subject][1] += 1
        counts[subject][0] += int(bool(row.get("is_correct")))
    subject_stats = [
        {
            "subject": subject,
            "correct": correct,
            "total": total,
            "accuracy_percent": (correct / total * 100.0) if total else 0.0,
        }
        for subject, (correct, total) in counts.items()
    ]
    return sorted(
        subject_stats,
        key=lambda row: (row["accuracy_percent"], -row["total"], row["subject"]),
    )


def _parse_log_final_accuracy_display(text: str) -> str:
    match = re.search(r"Final accuracy \(Pass@1\):\s*([0-9.]+%)", text)
    return match.group(1) if match else ""


def _accuracy_display_interpretation(display: str, pass_at_1: float) -> str:
    expected_display = f"{pass_at_1:.2f}%"
    if display == expected_display and pass_at_1 > 1e-9:
        return f"display_bug_ratio_{pass_at_1:.2f}_equals_{pass_at_1 * 100:.1f}_percent"
    return "display_matches_percent"


def build_transfer_eval_summary(
    summary_jsonl: str = DEFAULT_SUMMARY_JSONL,
    results_jsonl: str = DEFAULT_RESULTS_JSONL,
    log_path: str = DEFAULT_LOG_PATH,
) -> Dict[str, Any]:
    summary_row = _last_jsonl_row(summary_jsonl)
    result_rows = _read_jsonl(results_jsonl)
    log_text = _read_text(log_path)
    correct = sum(int(bool(row.get("is_correct"))) for row in result_rows)
    total = len(result_rows)
    pass_at_1 = float(summary_row.get("pass_at_1", correct / total if total else 0.0))
    log_display = _parse_log_final_accuracy_display(log_text)
    subject_stats = _subject_rows(result_rows)
    llm_name = summary_row.get("llm_name", "")
    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "summary_jsonl": _repo_path(summary_jsonl),
        "results_jsonl": _repo_path(results_jsonl),
        "log_path": _repo_path(log_path),
        "transfer_result": True,
        "promptnode_result": False,
        "same_model_as_argdesigner": llm_name == LLM_NAME,
        "checkpoint_loaded": "Loading pretrained model:" in log_text,
        "dataset": summary_row.get("dataset", "mmlu"),
        "model_path": summary_row.get("model_path", ""),
        "llm_name": llm_name,
        "total_tasks": int(summary_row.get("total_tasks", total)),
        "result_rows": total,
        "correct": correct,
        "pass_at_1": pass_at_1,
        "accuracy_percent": pass_at_1 * 100.0,
        "cost": float(summary_row.get("cost", 0.0)),
        "prompt_tokens": int(float(summary_row.get("prompt_tokens", 0))),
        "completion_tokens": int(float(summary_row.get("completion_tokens", 0))),
        "decision_method": result_rows[0].get("decision_method", "") if result_rows else "",
        "subject_results": subject_stats,
        "weakest_subjects": subject_stats[:5],
        "log_final_accuracy_display": log_display,
        "log_final_accuracy_interpretation": _accuracy_display_interpretation(
            log_display,
            pass_at_1,
        ),
        "errors_detected": _detect_errors(log_text),
        "mmlu_transfer_accuracy_claim_supported": True,
        "aqua_accuracy_claim_supported": False,
        "promptnode_accuracy_claim_supported": False,
        "robustness_claim_supported": False,
        "sci_q2_ready": False,
        "next_protocol": "r163_promptnode_promptedge_transfer_or_aqua_matched_comparison",
        "next_goal_audit_due": "R165",
    }


def render_report(summary: Dict[str, Any]) -> str:
    subject_rows = [
        f"| `{row['subject']}` | `{row['correct']}/{row['total']}` | `{row['accuracy_percent']:.1f}%` |"
        for row in summary["subject_results"]
    ]
    return "\n".join(
        [
            "# R162 MMLU ARG Transfer Evaluation",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Raw Result",
            "",
            f"- Dataset: `{summary['dataset']}`",
            f"- LLM: `{summary['llm_name']}`",
            f"- Model path: `{summary['model_path']}`",
            f"- Decision method: `{summary['decision_method']}`",
            f"- Total tasks: `{summary['total_tasks']}`",
            f"- Correct: `{summary['correct']}`",
            f"- Pass@1: `{summary['pass_at_1']:.4f}`",
            f"- Accuracy: `{summary['accuracy_percent']:.1f}%`",
            f"- Cost: `${summary['cost']:.6f}`",
            f"- Prompt tokens: `{summary['prompt_tokens']}`",
            f"- Completion tokens: `{summary['completion_tokens']}`",
            "",
            "## Integrity",
            "",
            f"- Checkpoint loaded: `{summary['checkpoint_loaded']}`",
            f"- Same model as ARG-Designer setting: `{summary['same_model_as_argdesigner']}`",
            f"- Errors detected: `{summary['errors_detected']}`",
            f"- Log final accuracy display: `{summary['log_final_accuracy_display']}`",
            f"- Log display interpretation: `{summary['log_final_accuracy_interpretation']}`",
            "",
            "## Subject Results",
            "",
            "| Subject | Raw accuracy | Percent |",
            "| --- | ---: | ---: |",
            *subject_rows,
            "",
            "## Claim Gate",
            "",
            f"- MMLU transfer accuracy claim supported: `{summary['mmlu_transfer_accuracy_claim_supported']}`",
            f"- PromptNode result: `{summary['promptnode_result']}`",
            f"- PromptNode accuracy claim supported: `{summary['promptnode_accuracy_claim_supported']}`",
            f"- AQuA accuracy claim supported: `{summary['aqua_accuracy_claim_supported']}`",
            f"- Robustness claim supported: `{summary['robustness_claim_supported']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
            "## Interpretation",
            "",
            "R162 establishes a same-LLM ARG-Designer checkpoint transfer baseline on MMLU STEM "
            "transfer100. The result is strong but uneven across subjects, so the next method "
            "iteration should test first-class PromptNode plus PromptEdge control on the same "
            "budget and report per-subject deltas instead of only a single aggregate score.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R162 MMLU transfer evaluation report.")
    parser.add_argument("--summary-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_transfer_eval_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R162 MMLU transfer eval report: "
        f"accuracy={summary['accuracy_percent']:.1f}% "
        f"correct={summary['correct']}/{summary['total_tasks']} "
        f"cost=${summary['cost']:.6f} "
        f"errors={summary['errors_detected']}"
    )


if __name__ == "__main__":
    main()
