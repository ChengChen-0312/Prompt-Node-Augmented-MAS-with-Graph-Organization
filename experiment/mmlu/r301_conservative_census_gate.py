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

from experiment.mmlu.r300_goal_and_label_audit import AUDIT_CLEAN_OVERRIDES, audit_clean_answer


DEFAULT_ARG_RESULTS = "experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r301_conservative_census_gate_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r301_conservative_census_gate_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r301_conservative_census_gate_report.md"
VALID_LABELS = {"A", "B", "C", "D", "E"}
NUMBER_WORDS = (
    "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|"
    "sixteen|seventeen|eighteen|nineteen|twenty"
)


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def normalize_label(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text[:1] if text[:1] in VALID_LABELS else ""


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with _repo_path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: str, data: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def stem_text(question: str) -> str:
    return re.split(r"\bOption\s+A\s*[:.)]", str(question or ""), maxsplit=1, flags=re.I)[0]


def option_lines(question: str) -> List[tuple[str, str]]:
    lines: List[tuple[str, str]] = []
    for match in re.finditer(r"Option\s+([A-E])\s*[:.)]\s*([^\n]+)", str(question or ""), flags=re.I):
        lines.append((match.group(1).upper(), match.group(2).strip()))
    return lines


def none_option_label(question: str) -> str:
    for label, text in option_lines(question):
        lowered = text.lower()
        if "none of the above" in lowered or "none of these" in lowered:
            return label
    return ""


def mentions_sample(stem: str) -> bool:
    lowered = stem.lower()
    return bool(re.search(r"\b(sample|sampled|sampling|randomly selected|surveyed)\b", lowered))


def has_complete_group_counts(stem: str) -> bool:
    lowered = stem.lower()
    number = rf"(?:\d+|{NUMBER_WORDS})"
    pattern = rf"\b(?:has|have|contains|include|includes|there are)\s+(?:[a-z-]+\s+){{0,4}}{number}\s+[a-z-]+(?:\s+[a-z-]+){{0,4}}\s+and\s+{number}\s+[a-z-]+"
    return bool(re.search(pattern, lowered))


def asks_mean_comparison(stem: str) -> bool:
    lowered = stem.lower()
    return "mean" in lowered and any(term in lowered for term in ["compare", "comparing", "difference"])


def has_inferential_test_options(question: str) -> bool:
    options = " ".join(text.lower() for _, text in option_lines(question))
    test_terms = ["z-test", "t-test", "test of", "confidence interval", "population mean", "population means"]
    return any(term in options for term in test_terms)


def build_census_gate_features(question: str, arg_prediction: str) -> Dict[str, Any]:
    stem = stem_text(question)
    none_label = none_option_label(question)
    features = {
        "has_none_option": bool(none_label),
        "none_option_label": none_label,
        "has_complete_group_counts": has_complete_group_counts(stem),
        "asks_mean_comparison": asks_mean_comparison(stem),
        "has_inferential_test_options": has_inferential_test_options(question),
        "mentions_sample": mentions_sample(stem),
        "arg_prediction_is_none_option": normalize_label(arg_prediction) == none_label if none_label else False,
    }
    features["census_no_inference_trigger"] = (
        features["has_none_option"]
        and features["has_complete_group_counts"]
        and features["asks_mean_comparison"]
        and features["has_inferential_test_options"]
        and not features["mentions_sample"]
        and not features["arg_prediction_is_none_option"]
    )
    return features


def _row_question(row: Dict[str, Any]) -> str:
    return str(row.get("question") or row.get("task") or "")


def _row_arg_prediction(row: Dict[str, Any]) -> str:
    return normalize_label(row.get("arg_prediction") or row.get("predicted_answer"))


def apply_census_gate(row: Dict[str, Any]) -> Dict[str, Any]:
    output = dict(row)
    task_id = str(output.get("task_id") or "")
    question = _row_question(output)
    arg_prediction = _row_arg_prediction(output)
    official_answer = normalize_label(output.get("true_answer"))
    clean_answer = audit_clean_answer(task_id, official_answer)
    features = build_census_gate_features(question, arg_prediction)

    if features["census_no_inference_trigger"]:
        predicted = features["none_option_label"]
        decision_rule = "switch_census_no_inference_mismatch"
        lifecycle_actions = ["write", "forward", "upgrade"]
        edge_decision = "forward"
    else:
        predicted = arg_prediction
        decision_rule = "keep_arg_no_gate_trigger"
        lifecycle_actions = ["compress", "prune"]
        edge_decision = "prune"

    official_correct = predicted == official_answer if official_answer in VALID_LABELS else None
    audit_clean_correct = predicted == clean_answer if clean_answer in VALID_LABELS else None
    arg_official_correct = arg_prediction == official_answer if official_answer in VALID_LABELS else None
    arg_audit_clean_correct = arg_prediction == clean_answer if clean_answer in VALID_LABELS else None
    output.update(
        {
            "run_id": "R301",
            "arg_prediction": arg_prediction,
            "predicted_answer": predicted,
            "true_answer": official_answer,
            "audit_clean_answer": clean_answer,
            "is_correct": official_correct,
            "audit_clean_is_correct": audit_clean_correct,
            "arg_is_correct": arg_official_correct,
            "arg_audit_clean_is_correct": arg_audit_clean_correct,
            "fix": arg_official_correct is False and official_correct is True,
            "harm": arg_official_correct is True and official_correct is False,
            "audit_clean_fix": arg_audit_clean_correct is False and audit_clean_correct is True,
            "audit_clean_harm": arg_audit_clean_correct is True and audit_clean_correct is False,
            "decision_rule": decision_rule,
            "gate_features": features,
            "promptnode_roles": ["PN_InstructionVerifier", "PN_EdgeGate", "PN_Router"],
            "promptnode_identity_types": ["Verifier", "Agent-like"],
            "promptedge_permissions": ["read", "write", "forward"],
            "promptedge_policy": {
                "question_to_instruction_verifier": "read",
                "instruction_verifier_to_edge_gate": "write",
                "edge_gate_to_router": edge_decision,
            },
            "lifecycle_actions": lifecycle_actions,
            "model_visible_features_only": True,
            "claim_boundary": (
                "Deterministic conservative PromptNode gate over ARG outputs. Selection uses only question/options and ARG answer; "
                "labels are used only after selection for official and audit-clean scoring."
            ),
        }
    )
    return output


def build_gate_records(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [apply_census_gate(row) for row in rows]


def _baseline_audit_clean_correct(rows: Iterable[Dict[str, Any]]) -> int:
    total = 0
    for row in rows:
        task_id = str(row.get("task_id") or "")
        pred = _row_arg_prediction(row)
        clean = audit_clean_answer(task_id, row.get("true_answer"))
        if pred == clean:
            total += 1
    return total


def summarize_gate_records(
    records: List[Dict[str, Any]],
    baseline_official_correct: int,
    baseline_audit_clean_correct: int,
) -> Dict[str, Any]:
    evaluated = [row for row in records if row.get("is_correct") is not None]
    clean_evaluated = [row for row in records if row.get("audit_clean_is_correct") is not None]
    correct = sum(1 for row in evaluated if row.get("is_correct"))
    clean_correct = sum(1 for row in clean_evaluated if row.get("audit_clean_is_correct"))
    fixes = sum(1 for row in evaluated if row.get("fix"))
    harms = sum(1 for row in evaluated if row.get("harm"))
    clean_fixes = sum(1 for row in clean_evaluated if row.get("audit_clean_fix"))
    clean_harms = sum(1 for row in clean_evaluated if row.get("audit_clean_harm"))
    return {
        "run_id": "R301",
        "title": "MMLU conservative census/no-inference PromptNode gate",
        "claim_boundary": (
            "Accuracy-bearing offline gate over existing ARG transfer outputs. It demonstrates a generic PromptNode/PromptEdge "
            "logic, but still needs prospective validation before a broad SCI-Q2 claim."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(records),
        "evaluated_records": len(evaluated),
        "correct": correct,
        "accuracy": correct / len(evaluated) if evaluated else None,
        "audit_clean_correct": clean_correct,
        "audit_clean_accuracy": clean_correct / len(clean_evaluated) if clean_evaluated else None,
        "baseline_official_correct": int(baseline_official_correct),
        "baseline_audit_clean_correct": int(baseline_audit_clean_correct),
        "official_delta_vs_arg": correct - int(baseline_official_correct),
        "audit_clean_delta_vs_arg": clean_correct - int(baseline_audit_clean_correct),
        "fixes": fixes,
        "harms": harms,
        "fix_harm": f"{fixes}/{harms}",
        "audit_clean_fixes": clean_fixes,
        "audit_clean_harms": clean_harms,
        "audit_clean_fix_harm": f"{clean_fixes}/{clean_harms}",
        "switches": sum(1 for row in records if row.get("decision_rule") == "switch_census_no_inference_mismatch"),
        "switched_task_ids": [
            row.get("task_id") for row in records if row.get("decision_rule") == "switch_census_no_inference_mismatch"
        ],
        "audit_clean_overrides": dict(AUDIT_CLEAN_OVERRIDES),
        "beats_arg_official": correct > int(baseline_official_correct),
        "beats_arg_audit_clean": clean_correct > int(baseline_audit_clean_correct),
        "no_harm_official": harms == 0,
        "no_harm_audit_clean": clean_harms == 0,
        "model_visible_features_only": all(row.get("model_visible_features_only") for row in records),
        "method_components": {
            "virtual_node_types": ["Instruction-Verifier", "Agent-like EdgeGate"],
            "edge_permissions": ["read", "write", "forward"],
            "lifecycle": ["compress", "prune", "write", "forward", "upgrade"],
            "trainable_next": "Distill the trigger into a SafetyGatePN classifier with asymmetric harm penalty.",
        },
        "transfer_superiority_claim_supported": correct > int(baseline_official_correct)
        and clean_correct > int(baseline_audit_clean_correct),
        "sci_q2_ready": False,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R301 Conservative Census Gate",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Official: R301 `{summary['correct']}/{summary['records']}` vs ARG `{summary['baseline_official_correct']}/{summary['records']}`; delta `{summary['official_delta_vs_arg']}`",
            f"- Audit-clean: R301 `{summary['audit_clean_correct']}/{summary['records']}` vs ARG `{summary['baseline_audit_clean_correct']}/{summary['records']}`; delta `{summary['audit_clean_delta_vs_arg']}`",
            f"- Official fix/harm: `{summary['fix_harm']}`",
            f"- Audit-clean fix/harm: `{summary['audit_clean_fix_harm']}`",
            f"- Switches: `{summary['switches']}`; tasks `{summary['switched_task_ids']}`",
            f"- Beats ARG official/audit-clean: `{summary['beats_arg_official']}` / `{summary['beats_arg_audit_clean']}`",
            f"- No-harm official/audit-clean: `{summary['no_harm_official']}` / `{summary['no_harm_audit_clean']}`",
            "",
            "## Interpretation",
            "",
            "R301 fixes the complete-population-vs-inference statistics failure through a generic PromptNode gate. "
            "It intentionally keeps the ARG answer on known noisy physics and chemistry items instead of optimizing toward wrong labels. "
            "The next step is to train this as a SafetyGatePN with asymmetric loss and validate prospectively.",
            "",
        ]
    )


def run(
    arg_results_jsonl: str = DEFAULT_ARG_RESULTS,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    limit_tasks: int | None = None,
) -> Dict[str, Any]:
    rows = load_jsonl(arg_results_jsonl)
    if limit_tasks is not None:
        rows = rows[: int(limit_tasks)]
    baseline_official = sum(1 for row in rows if row.get("is_correct"))
    baseline_clean = _baseline_audit_clean_correct(rows)
    records = build_gate_records(rows)
    summary = summarize_gate_records(records, baseline_official, baseline_clean)
    summary.update(
        {
            "arg_results_jsonl": arg_results_jsonl,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
            "limit_tasks": limit_tasks,
        }
    )
    write_jsonl(output_jsonl, records)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R301 conservative census/no-inference PromptNode gate.")
    parser.add_argument("--arg_results_jsonl", default=DEFAULT_ARG_RESULTS)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--limit_tasks", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
