from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r301_conservative_census_gate import normalize_label, write_json, write_jsonl, write_text
from experiment.mmlu.r305_nonmath_promptnode_library import propose_nonmath_candidate


DEFAULT_MMLU_TEST_DIR = (
    "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/datasets/MMLU/test"
)
DEFAULT_AQUA_R266_SUMMARY = "experiment/aqua/res_logs/aqua_r266_audit_clean_rescore_summary.json"
DEFAULT_MMLU_R304_SUMMARY = "experiment/mmlu/res_logs/mmlu_r304_multi_trigger_safety_gate_summary.json"
DEFAULT_MMLU_R306_SUMMARY = "experiment/mmlu/res_logs/mmlu_r306_nonmath_stack_eval_summary.json"
DEFAULT_MMLU_R309_SUMMARY = "experiment/mmlu/res_logs/mmlu_r309_negative_controls_summary.json"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r310_nonstem_transfer_preflight_records.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r310_transfer_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r310_transfer_preflight_report.md"

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


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _question_from_csv_row(row: List[str]) -> str:
    stem, a, b, c, d = [part.strip() for part in row[:5]]
    return "\n".join(
        [
            stem,
            f"Option A: {a}",
            f"Option B: {b}",
            f"Option C: {c}",
            f"Option D: {d}",
        ]
    )


def load_nonstem_records(mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR, max_per_subject: int = 5) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    root = Path(mmlu_test_dir)
    for subject in NONSTEM_SUBJECTS:
        csv_path = root / f"{subject}_test.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"missing MMLU subject CSV: {csv_path}")
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row_index, row in enumerate(reader):
                if len(row) < 6:
                    continue
                question = _question_from_csv_row(row)
                answer = normalize_label(row[5])
                candidate = propose_nonmath_candidate({"question": question, "arg_prediction": ""})
                records.append(
                    {
                        "run_id": "R310",
                        "dataset": "mmlu_nonstem",
                        "subject": subject,
                        "task_id": f"MMLU-nonstem-{subject}_test-{row_index}",
                        "row_index": row_index,
                        "question": question,
                        "task": question,
                        "true_answer": answer,
                        "answer": answer,
                        "candidate": candidate,
                        "candidate_available": candidate.get("candidate_type") != "none",
                        "candidate_has_answer_label": normalize_label(candidate.get("candidate_label")) in {"A", "B", "C", "D"},
                        "model_visible_features_only": bool(candidate.get("model_visible_features_only", True)),
                        "claim_boundary": (
                            "R310 non-STEM transfer preflight only; no ARG/PromptNode prediction and no accuracy claim."
                        ),
                    }
                )
                if sum(1 for item in records if item["subject"] == subject) >= max_per_subject:
                    break
    return records


def _candidate_type_counts(records: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in records:
        ctype = str(row.get("candidate", {}).get("candidate_type") or "none")
        counts[ctype] = counts.get(ctype, 0) + 1
    return dict(sorted(counts.items()))


def _aqua_transfer_summary(aqua_r266: Dict[str, Any]) -> Dict[str, Any]:
    scenarios = aqua_r266.get("scenarios", {})
    clean = scenarios.get("exclude_59_139_228", {})
    conservative = scenarios.get("exclude_59_139_228_114", {})
    sensitivity = scenarios.get("exclude_59_139_228_correct_114", {})
    arg_clean = clean.get("ARG", {}).get("accuracy", "unknown")
    r065_clean = clean.get("R065", {}).get("accuracy", "unknown")
    return {
        "status": "positive_existing_evidence",
        "source_run": "R266/R065",
        "arg": arg_clean,
        "r065": r065_clean,
        "delta_correct": clean.get("delta", {}).get("delta_correct"),
        "conservative_remove_114": {
            "arg": conservative.get("ARG", {}).get("accuracy", "unknown"),
            "r065": conservative.get("R065", {}).get("accuracy", "unknown"),
        },
        "correct_114_sensitivity": {
            "arg": sensitivity.get("ARG", {}).get("accuracy", "unknown"),
            "r065": sensitivity.get("R065", {}).get("accuracy", "unknown"),
        },
        "claim_boundary": "Existing audit-clean AQuA evidence; no new API in R310.",
    }


def _mmlu_stem_summary(r304: Dict[str, Any], r306: Dict[str, Any], r309: Dict[str, Any]) -> Dict[str, Any]:
    reference = r309.get("reference", {})
    controls = r309.get("controls", {})
    main_records = int(r306.get("main_records", r304.get("main_records", 97)))
    arg_main_correct = int(r304.get("main_baseline_official_correct", r304.get("baseline_official_correct", 0)))
    return {
        "status": "positive_existing_evidence_with_controls",
        "source_run": "R306/R309",
        "arg": f"{arg_main_correct}/{main_records}",
        "r304": f"{r306.get('r304_main_correct', 0)}/{main_records}",
        "r306": reference.get("r306_main97", f"{r306.get('main_correct', 0)}/{main_records}"),
        "r306_delta_vs_r304": r306.get("main_delta_vs_r304"),
        "r306_delta_vs_arg": 7,
        "cheap_control_matches_or_beats_r306": bool(r309.get("cheap_control_matches_or_beats_r306")),
        "equal_accuracy_more_cost_controls": r309.get("equal_accuracy_more_cost_controls", []),
        "no_safety_gate": {
            "main97": controls.get("no_safety_gate_unsafe_forward", {}).get("main97", "unknown"),
            "fix_harm": controls.get("no_safety_gate_unsafe_forward", {}).get("main_fix_harm", "unknown"),
        },
        "claim_boundary": "MMLU STEM main97 diagnostic evidence; non-STEM evaluation still required.",
    }


def summarize_nonstem_preflight(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    candidate_records = [row for row in records if row.get("candidate_available")]
    answer_candidate_records = [row for row in records if row.get("candidate_has_answer_label")]
    subject_counts: Dict[str, int] = {}
    for row in records:
        subject = str(row.get("subject") or "")
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
    return {
        "status": "split_and_candidate_preflight_only",
        "records": len(records),
        "subject_count": len(subject_counts),
        "subject_counts": dict(sorted(subject_counts.items())),
        "candidate_records": len(candidate_records),
        "answer_candidate_records": len(answer_candidate_records),
        "candidate_type_counts": _candidate_type_counts(records),
        "accuracy_available": False,
        "api_required_for_accuracy": True,
        "model_required": "gpt-4o-2024-08-06",
        "same_arg_checkpoint_required": True,
    }


def build_transfer_preflight_summary(
    mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR,
    aqua_r266_summary: str = DEFAULT_AQUA_R266_SUMMARY,
    mmlu_r304_summary: str = DEFAULT_MMLU_R304_SUMMARY,
    mmlu_r306_summary: str = DEFAULT_MMLU_R306_SUMMARY,
    mmlu_r309_summary: str = DEFAULT_MMLU_R309_SUMMARY,
    max_per_subject: int = 5,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    records = load_nonstem_records(mmlu_test_dir=mmlu_test_dir, max_per_subject=max_per_subject)
    aqua_r266 = _load_json(aqua_r266_summary)
    r304 = _load_json(mmlu_r304_summary)
    r306 = _load_json(mmlu_r306_summary)
    r309 = _load_json(mmlu_r309_summary)
    summary = {
        "run_id": "R310",
        "title": "Transfer preflight after negative controls",
        "claim_boundary": (
            "R310 freezes transfer evidence and creates a fixed MMLU non-STEM preflight split. "
            "It does not run ARG/PromptNode inference on non-STEM and therefore does not support a non-STEM accuracy claim."
        ),
        "no_api": True,
        "broad_api": False,
        "transfer_splits": {
            "aqua_tail34_audit_clean": _aqua_transfer_summary(aqua_r266),
            "mmlu_stem_main97": _mmlu_stem_summary(r304, r306, r309),
            "mmlu_nonstem_preflight": {
                "status": "prepared_no_accuracy_yet",
                "records": len(records),
            },
        },
        "nonstem_preflight": summarize_nonstem_preflight(records),
        "claim_permissions": {
            "aqua_clean_claim_allowed": True,
            "mmlu_stem_diagnostic_claim_allowed": True,
            "mmlu_nonstem_accuracy_claim_allowed": False,
            "transfer_accuracy_claim_allowed": False,
            "training_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "authorized_api_next": True,
        "training_authorized_next": False,
        "next_required_run": "R311_nonstem_arg_promptnode_eval",
        "next_required_actions": [
            "Run ARG baseline and expanded PromptNode/PromptEdge graph on the fixed R310 non-STEM split using gpt-4o-2024-08-06.",
            "Score official accuracy, fix/harm, token cost, and cost-normalized accuracy.",
            "If non-STEM is no-harm or positive, then proceed to ablations; if it is negative, narrow the paper claim to STEM/math-plus-semantic multiple choice.",
        ],
    }
    return records, summary


def render_report(summary: Dict[str, Any]) -> str:
    aqua = summary["transfer_splits"]["aqua_tail34_audit_clean"]
    stem = summary["transfer_splits"]["mmlu_stem_main97"]
    nonstem = summary["nonstem_preflight"]
    rows = [
        "# R310 Transfer Preflight",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Existing Evidence",
        "",
        f"- AQuA audit-clean: R065 `{aqua['r065']}` vs ARG `{aqua['arg']}`",
        f"- MMLU STEM main97: R306 `{stem['r306']}` vs R304 `{stem['r304']}`; cheap control threat `{stem['cheap_control_matches_or_beats_r306']}`",
        "",
        "## Non-STEM Preflight",
        "",
        f"- Records: `{nonstem['records']}` across `{nonstem['subject_count']}` subjects",
        f"- Candidate records: `{nonstem['candidate_records']}`",
        f"- Candidate type counts: `{nonstem['candidate_type_counts']}`",
        f"- Accuracy available: `{nonstem['accuracy_available']}`",
        "",
        "## Claim Permissions",
        "",
    ]
    rows.extend(f"- `{name}`: `{value}`" for name, value in summary["claim_permissions"].items())
    rows.extend(["", "## Next", ""])
    rows.extend(f"- {action}" for action in summary["next_required_actions"])
    rows.append("")
    return "\n".join(rows)


def run(
    mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR,
    aqua_r266_summary: str = DEFAULT_AQUA_R266_SUMMARY,
    mmlu_r304_summary: str = DEFAULT_MMLU_R304_SUMMARY,
    mmlu_r306_summary: str = DEFAULT_MMLU_R306_SUMMARY,
    mmlu_r309_summary: str = DEFAULT_MMLU_R309_SUMMARY,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    max_per_subject: int = 5,
) -> Dict[str, Any]:
    records, summary = build_transfer_preflight_summary(
        mmlu_test_dir=mmlu_test_dir,
        aqua_r266_summary=aqua_r266_summary,
        mmlu_r304_summary=mmlu_r304_summary,
        mmlu_r306_summary=mmlu_r306_summary,
        mmlu_r309_summary=mmlu_r309_summary,
        max_per_subject=max_per_subject,
    )
    summary.update(
        {
            "mmlu_test_dir": mmlu_test_dir,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
            "max_per_subject": max_per_subject,
        }
    )
    write_jsonl(output_jsonl, records)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R310 transfer preflight and non-STEM split.")
    parser.add_argument("--mmlu_test_dir", default=DEFAULT_MMLU_TEST_DIR)
    parser.add_argument("--aqua_r266_summary", default=DEFAULT_AQUA_R266_SUMMARY)
    parser.add_argument("--mmlu_r304_summary", default=DEFAULT_MMLU_R304_SUMMARY)
    parser.add_argument("--mmlu_r306_summary", default=DEFAULT_MMLU_R306_SUMMARY)
    parser.add_argument("--mmlu_r309_summary", default=DEFAULT_MMLU_R309_SUMMARY)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--max_per_subject", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
