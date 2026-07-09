from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_ARG_RESULTS = "experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r300_goal_and_label_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r300_goal_and_label_audit_report.md"

AUDIT_CLEAN_OVERRIDES = {
    "MMLU-high_school_physics_test-67": "C",
    "MMLU-college_chemistry_test-62": "A",
}

AUDIT_ITEMS: List[Dict[str, Any]] = [
    {
        "task_id": "MMLU-high_school_statistics_test-32",
        "dataset_label": "D",
        "arg_prediction": "B",
        "audit_clean_answer": "D",
        "label_verdict": "label_correct_after_option_compression",
        "source_type": "external_answer_explanation",
        "source_url": "https://www.crackap.com/ap/statistics/question-331.html",
        "evidence_note": "Original five-option item has E=None; local four-option compression maps None to D.",
    },
    {
        "task_id": "MMLU-high_school_physics_test-67",
        "dataset_label": "A",
        "arg_prediction": "C",
        "audit_clean_answer": "C",
        "label_verdict": "dataset_label_wrong_groundtruth",
        "source_type": "mmlu_redux_2_0_and_external_answer_explanation",
        "source_url": "https://www.crackap.com/ap/physics-1/question-45-answer-and-explanation.html",
        "mmlu_redux_error_type": "wrong_groundtruth",
        "evidence_note": "Ohm's law makes increased voltage plus decreased resistance the always-increase option.",
    },
    {
        "task_id": "MMLU-abstract_algebra_test-53",
        "dataset_label": "C",
        "arg_prediction": "A",
        "audit_clean_answer": "C",
        "label_verdict": "label_kept_expert_checked_no_override",
        "source_type": "mmlu_redux_2_0",
        "source_url": "https://huggingface.co/datasets/edinburgh-dawg/mmlu-redux-2.0",
        "mmlu_redux_error_type": "expert",
        "evidence_note": "Redux keeps the original answer index while noting expert review nuance; no clean override used.",
    },
    {
        "task_id": "MMLU-college_mathematics_test-26",
        "dataset_label": "D",
        "arg_prediction": "C",
        "audit_clean_answer": "D",
        "label_verdict": "label_correct",
        "source_type": "mmlu_redux_2_0_expert",
        "source_url": "https://huggingface.co/datasets/edinburgh-dawg/mmlu-redux-2.0",
        "mmlu_redux_error_type": "ok",
        "evidence_note": "Redux marks the item ok with D as the answer.",
    },
    {
        "task_id": "MMLU-high_school_statistics_test-127",
        "dataset_label": "D",
        "arg_prediction": "C",
        "audit_clean_answer": "D",
        "label_verdict": "label_correct",
        "source_type": "external_answer_explanation",
        "source_url": "https://www.crackap.com/ap/statistics/question-21.html",
        "evidence_note": "Expected value is 20/36 minus the 2 dollar cost, so the loss is about 1.44.",
    },
    {
        "task_id": "MMLU-machine_learning_test-81",
        "dataset_label": "C",
        "arg_prediction": "A",
        "audit_clean_answer": "C",
        "label_verdict": "label_correct",
        "source_type": "mmlu_redux_2_0_and_cmu_exam_source",
        "source_url": "https://www.cs.cmu.edu/~aarti/Class/10701/exams/final2006-solution.pdf",
        "mmlu_redux_error_type": "ok",
        "evidence_note": "Junction tree and variable elimination are both exact; conditional independence does not imply d-separation in an arbitrary graph.",
    },
    {
        "task_id": "MMLU-conceptual_physics_test-41",
        "dataset_label": "D",
        "arg_prediction": "B",
        "audit_clean_answer": "D",
        "label_verdict": "label_correct_by_domain_evidence",
        "source_type": "open_textbook_concept_evidence",
        "source_url": "https://chem.libretexts.org/Courses/Madera_Community_College/Concepts_of_Physical_Science/04%3A_Fluid_Mechanics_and_Waves/4.07%3A_Properties_of_Waves/4.7.04%3A_When_Waves_Sources_Move-_Doppler_effects_and_Bow_Wakes",
        "evidence_note": "Bow wakes arise when a source moves faster than wave speed and involve constructive superposition.",
    },
    {
        "task_id": "MMLU-college_chemistry_test-62",
        "dataset_label": "B",
        "arg_prediction": "A",
        "audit_clean_answer": "A",
        "label_verdict": "dataset_label_wrong_groundtruth",
        "source_type": "mmlu_redux_2_0",
        "source_url": "https://huggingface.co/datasets/edinburgh-dawg/mmlu-redux-2.0",
        "mmlu_redux_error_type": "wrong_groundtruth",
        "evidence_note": "Redux flags the original B label as wrong and gives A as corrected answer.",
    },
    {
        "task_id": "MMLU-college_mathematics_test-67",
        "dataset_label": "D",
        "arg_prediction": "B",
        "audit_clean_answer": "D",
        "label_verdict": "label_correct",
        "source_type": "mmlu_redux_2_0_expert",
        "source_url": "https://huggingface.co/datasets/edinburgh-dawg/mmlu-redux-2.0",
        "mmlu_redux_error_type": "ok",
        "evidence_note": "The sum and intersection of two-sided ideals are ideals; the simple product set need not be.",
    },
    {
        "task_id": "MMLU-college_chemistry_test-97",
        "dataset_label": "C",
        "arg_prediction": "B",
        "audit_clean_answer": "C",
        "label_verdict": "label_correct",
        "source_type": "mmlu_redux_2_0_and_nmr_constant",
        "source_url": "https://huggingface.co/datasets/edinburgh-dawg/mmlu-redux-2.0",
        "mmlu_redux_error_type": "ok",
        "evidence_note": "31P gyromagnetic ratio near 17.235 MHz/T gives about 345 MHz at 20 T.",
    },
    {
        "task_id": "MMLU-elementary_mathematics_test-222",
        "dataset_label": "D",
        "arg_prediction": "A",
        "audit_clean_answer": "D",
        "label_verdict": "label_correct",
        "source_type": "state_practice_test_question",
        "source_url": "https://doe.louisiana.gov/docs/default-source/assessment/practice-test-math-grade-5.pdf?sfvrsn=9d36a69a_0",
        "evidence_note": "Adult ticket revenue minus youth ticket revenue is (467 x 7) - (215 x 3).",
    },
    {
        "task_id": "MMLU-college_mathematics_test-92",
        "dataset_label": "C",
        "arg_prediction": "B",
        "audit_clean_answer": "C",
        "label_verdict": "label_correct",
        "source_type": "mmlu_redux_2_0_expert",
        "source_url": "https://huggingface.co/datasets/edinburgh-dawg/mmlu-redux-2.0",
        "mmlu_redux_error_type": "ok",
        "evidence_note": "Area calculation gives P(x<y)=5/8.",
    },
]


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with _repo_path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def normalize_label(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text[:1] if text[:1] in {"A", "B", "C", "D", "E"} else ""


def audit_clean_answer(task_id: str, official_answer: Any) -> str:
    return AUDIT_CLEAN_OVERRIDES.get(str(task_id), normalize_label(official_answer))


def _count_correct(rows: Iterable[Dict[str, Any]], clean: bool = False) -> int:
    correct = 0
    for row in rows:
        target = audit_clean_answer(row.get("task_id", ""), row.get("true_answer")) if clean else normalize_label(row.get("true_answer"))
        if normalize_label(row.get("predicted_answer")) == target:
            correct += 1
    return correct


def build_label_audit_summary(arg_results_jsonl: str = DEFAULT_ARG_RESULTS) -> Dict[str, Any]:
    rows = load_jsonl(arg_results_jsonl)
    first24 = rows[:24]
    wrong_groundtruth = [
        item for item in AUDIT_ITEMS if item.get("label_verdict") == "dataset_label_wrong_groundtruth"
    ]
    return {
        "run_id": "R300",
        "title": "MMLU transfer100 ARG wrong-case goal and label audit",
        "claim_boundary": (
            "Goal audit plus label audit only. Clean overrides come from MMLU-Redux 2.0 or external answer explanations; "
            "no PromptNode accuracy claim is made by this run."
        ),
        "no_api": True,
        "broad_api": False,
        "arg_results_jsonl": arg_results_jsonl,
        "audited_wrong_items": len(AUDIT_ITEMS),
        "wrong_groundtruth_count": len(wrong_groundtruth),
        "audit_clean_overrides": dict(AUDIT_CLEAN_OVERRIDES),
        "arg_r162_official_correct": _count_correct(rows, clean=False),
        "arg_r162_audit_clean_correct": _count_correct(rows, clean=True),
        "arg_r162_records": len(rows),
        "arg_r162_first24_official_correct": _count_correct(first24, clean=False),
        "arg_r162_first24_audit_clean_correct": _count_correct(first24, clean=True),
        "mmlu_redux_2_0_used": True,
        "official_vs_audit_clean_policy": "Report both columns; do not optimize toward known wrong-groundtruth labels.",
        "goal_alignment": {
            "still_targeting_sci_q2": True,
            "mmlu_transfer_target": "PromptNode gate must beat ARG under official and audit-clean accounting, then be validated prospectively.",
            "r299_lesson": "LLM self-confidence is not a safe no-harm gate; switch authority must be conservative and learnable.",
            "next_run": "R301 conservative census/no-inference PromptNode gate",
        },
        "audit_items": AUDIT_ITEMS,
        "transfer_superiority_claim_supported": False,
        "sci_q2_ready": False,
    }


def write_json(path: str, data: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R300 MMLU Goal And Label Audit",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- ARG official: `{summary['arg_r162_official_correct']}/{summary['arg_r162_records']}`",
        f"- ARG audit-clean: `{summary['arg_r162_audit_clean_correct']}/{summary['arg_r162_records']}`",
        f"- ARG first24 official/audit-clean: `{summary['arg_r162_first24_official_correct']}/24` / `{summary['arg_r162_first24_audit_clean_correct']}/24`",
        f"- Wrong-groundtruth overrides: `{summary['audit_clean_overrides']}`",
        f"- R299 lesson: {summary['goal_alignment']['r299_lesson']}",
        "",
        "## Audited Wrong Items",
        "",
        "| Task | Official | ARG | Clean | Verdict | Source |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for item in summary["audit_items"]:
        rows.append(
            "| `{task_id}` | `{dataset_label}` | `{arg_prediction}` | `{audit_clean_answer}` | {label_verdict} | {source_type} |".format(
                **item
            )
        )
    rows.extend(
        [
            "",
            "## Next",
            "",
            "R301 should only allow a virtual node to override ARG when a label-free, dataset-agnostic trigger is present. "
            "The immediate safe target is the census-versus-inference statistics item; noisy physics and chemistry labels must not be optimized as errors.",
            "",
        ]
    )
    return "\n".join(rows)


def run(
    arg_results_jsonl: str = DEFAULT_ARG_RESULTS,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_label_audit_summary(arg_results_jsonl)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R300 MMLU goal and label audit.")
    parser.add_argument("--arg_results_jsonl", default=DEFAULT_ARG_RESULTS)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
