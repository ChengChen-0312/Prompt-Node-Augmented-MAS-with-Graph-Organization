from __future__ import annotations

import argparse
import json
import math
import os
from typing import Any, Dict, Iterable, List, Set


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_ARG_JSONL = os.path.join(SCRIPT_DIR, "aqua_tail34_arg_baseline_results.jsonl")
DEFAULT_R065_JSONL = os.path.join(SCRIPT_DIR, "aqua_tail34_objective_guided_selector_results.jsonl")
DEFAULT_SUMMARY_JSON = os.path.join(SCRIPT_DIR, "res_logs", "aqua_r266_audit_clean_rescore_summary.json")
DEFAULT_REPORT_MD = os.path.join(SCRIPT_DIR, "run_logs", "aqua_r266_audit_clean_rescore.md")
DEFAULT_MANIFEST_JSON = os.path.join(SCRIPT_DIR, "res_logs", "aqua_r266_audit_clean_manifest.json")
BAD_TASKS_REQUESTED = {"task_59", "task_139", "task_228"}


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    return label[:1] if label[:1] in {"A", "B", "C", "D", "E"} else "NONE"


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def audit_task114_literal_formula(samples: int = 3600) -> Dict[str, Any]:
    def value(n: float) -> float:
        return (n**2 + 2 * math.sqrt(n) * (n + 4) + 16) / (n + 4 * math.sqrt(n) + 4)

    points = [(36 + i * (72 - 36) / samples, value(36 + i * (72 - 36) / samples)) for i in range(samples + 1)]
    min_n, min_x = min(points, key=lambda item: item[1])
    max_n, max_x = max(points, key=lambda item: item[1])
    option_ranges = {
        "A": (20.0, 54.0),
        "B": (23.0, 58.0),
        "C": (25.0, 64.0),
        "D": (28.0, 60.0),
    }
    support = {
        label: {
            "strict_supported": lower < min_x and max_x < upper,
            "lower_ok": lower < min_x,
            "upper_ok": max_x < upper,
        }
        for label, (lower, upper) in option_ranges.items()
    }
    supported = [label for label, item in support.items() if item["strict_supported"]]
    deterministic_label = supported[0] if len(supported) == 1 else "UNKNOWN"
    return {
        "task_id": "task_114",
        "official_label": "D",
        "deterministic_label": deterministic_label,
        "official_label_supported_strict": support["D"]["strict_supported"],
        "deterministic_label_supported_strict": deterministic_label != "UNKNOWN",
        "error_category": (
            "official_label_boundary_error"
            if deterministic_label == "C" and not support["D"]["strict_supported"]
            else "needs_manual_review"
        ),
        "literal_formula": "(n^2 + 2*sqrt(n)*(n+4) + 16) / (n + 4*sqrt(n) + 4)",
        "n_range": "36 <= n <= 72",
        "min": {"n": round(min_n, 6), "x": round(min_x, 12)},
        "max": {"n": round(max_n, 6), "x": round(max_x, 12)},
        "option_support": support,
        "reason": "At n=36, x=28 exactly, so strict option D (28 < x < 60) is false; option C contains the full sampled range.",
    }


def score_rows(
    rows: List[Dict[str, Any]],
    excluded_task_ids: Set[str],
    corrected_labels: Dict[str, str],
) -> Dict[str, Any]:
    scored_rows: List[Dict[str, Any]] = []
    for row in rows:
        task_id = str(row.get("task_id"))
        if task_id in excluded_task_ids:
            continue
        official_answer = normalize_label(row.get("true_answer"))
        effective_answer = normalize_label(corrected_labels.get(task_id, official_answer))
        predicted = normalize_label(row.get("predicted_answer"))
        scored_rows.append(
            {
                "task_id": task_id,
                "official_answer": official_answer,
                "effective_answer": effective_answer,
                "predicted_answer": predicted,
                "correct": predicted == effective_answer,
            }
        )
    correct = sum(1 for row in scored_rows if row["correct"])
    total = len(scored_rows)
    return {
        "accuracy": f"{correct}/{total}",
        "correct": correct,
        "total": total,
        "rate": correct / total if total else None,
        "excluded_task_ids": sorted(excluded_task_ids),
        "corrected_labels": dict(sorted(corrected_labels.items())),
        "rows": scored_rows,
    }


def _paired_delta(arg_score: Dict[str, Any], r065_score: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "delta_correct": int(r065_score["correct"]) - int(arg_score["correct"]),
        "delta_rate": (
            float(r065_score["rate"]) - float(arg_score["rate"])
            if r065_score.get("rate") is not None and arg_score.get("rate") is not None
            else None
        ),
    }


def build_manifest(task114_audit: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "run_id": "R266",
        "title": "AQuA tail34 audit-clean manifest",
        "do_not_modify_original_dataset": True,
        "exclude_from_clean_eval": {
            "task_59": {
                "category": "question_rationale_mismatch",
                "reason": "Question says 5 consecutive odd numbers; official rationale solves a 4-number condition.",
            },
            "task_139": {
                "category": "no_exact_option_official_arithmetic_error",
                "reason": "Equation x/10+x/5=1 gives x=10/3; official rationale rounds/solves to E=2.",
            },
            "task_228": {
                "category": "option_label_mismatch",
                "reason": "Official rationale and external GMAT source support II only; released options map II only to C while official label is B.",
            },
        },
        "task114_audit": task114_audit,
        "recommended_reporting": [
            "Main text may report audit-clean results with this manifest.",
            "Appendix should list excluded/corrected items and deterministic checks.",
            "Original official AQuA scores must remain available for baseline comparability.",
        ],
    }


def build_rescore_summary(
    arg_rows: List[Dict[str, Any]],
    r065_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    task114 = audit_task114_literal_formula()
    scenarios = {
        "official_tail34": {
            "description": "Original AQuA labels, no exclusions.",
            "excluded": set(),
            "corrections": {},
        },
        "exclude_59_139_228": {
            "description": "User-requested clean filter: remove task_59/task_139/task_228 only.",
            "excluded": set(BAD_TASKS_REQUESTED),
            "corrections": {},
        },
        "exclude_59_139_228_correct_114": {
            "description": "Sensitivity: remove the three bad tasks and correct task_114 from D to C.",
            "excluded": set(BAD_TASKS_REQUESTED),
            "corrections": {"task_114": task114["deterministic_label"]},
        },
        "exclude_59_139_228_114": {
            "description": "Conservative clean filter: remove the three bad tasks and remove task_114 as boundary-label noise.",
            "excluded": set(BAD_TASKS_REQUESTED) | {"task_114"},
            "corrections": {},
        },
    }
    scored: Dict[str, Any] = {}
    for name, scenario in scenarios.items():
        arg_score = score_rows(arg_rows, scenario["excluded"], scenario["corrections"])
        r065_score = score_rows(r065_rows, scenario["excluded"], scenario["corrections"])
        scored[name] = {
            "description": scenario["description"],
            "ARG": {k: v for k, v in arg_score.items() if k != "rows"},
            "R065": {k: v for k, v in r065_score.items() if k != "rows"},
            "delta": _paired_delta(arg_score, r065_score),
        }
    return {
        "run_id": "R266",
        "title": "AQuA tail34 audit-clean rescore",
        "claim_boundary": "No API; post-hoc rescore over existing ARG and R065 predictions. Original data is unchanged.",
        "bad_tasks_removed_by_user_request": sorted(BAD_TASKS_REQUESTED),
        "task114_audit": task114,
        "scenarios": scored,
        "paper_guidance": {
            "main_text": "Report official and audit-clean scores side by side.",
            "appendix": "Explain excluded/corrected tasks with deterministic checks and source links.",
            "warning": "Do not silently edit the benchmark or train on corrected test labels.",
        },
    }


def render_report(summary: Dict[str, Any]) -> str:
    lines = [
        "# R266 AQuA Tail34 Audit-Clean Rescore",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Score Table",
        "",
        "| Scenario | ARG | R065 | Delta | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for name, item in summary["scenarios"].items():
        lines.append(
            f"| `{name}` | `{item['ARG']['accuracy']}` | `{item['R065']['accuracy']}` | `{item['delta']['delta_correct']}` | {item['description']} |"
        )
    t114 = summary["task114_audit"]
    lines.extend(
        [
            "",
            "## Task 114 Audit",
            "",
            f"- Official label: `{t114['official_label']}`",
            f"- Deterministic strict label: `{t114['deterministic_label']}`",
            f"- Error category: `{t114['error_category']}`",
            f"- Range: min `{t114['min']}`, max `{t114['max']}`",
            f"- Reason: {t114['reason']}",
            "",
            "## Paper Guidance",
            "",
            "- Keep the original AQuA score for comparability.",
            "- Use the audit-clean score as the primary robustness table only if the appendix discloses the exclusion/correction manifest.",
            "- Do not train toward these corrected test labels; use them for evaluation reporting only.",
            "",
        ]
    )
    return "\n".join(lines)


def run_rescore(arg_jsonl: str, r065_jsonl: str, summary_json: str, report_md: str, manifest_json: str) -> Dict[str, Any]:
    arg_rows = load_jsonl(arg_jsonl)
    r065_rows = load_jsonl(r065_jsonl)
    summary = build_rescore_summary(arg_rows, r065_rows)
    manifest = build_manifest(summary["task114_audit"])
    write_json(summary_json, summary)
    write_json(manifest_json, manifest)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="R266 AQuA audit-clean rescore.")
    parser.add_argument("--arg_jsonl", default=DEFAULT_ARG_JSONL)
    parser.add_argument("--r065_jsonl", default=DEFAULT_R065_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--manifest_json", default=DEFAULT_MANIFEST_JSON)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_rescore(
        arg_jsonl=args.arg_jsonl,
        r065_jsonl=args.r065_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
        manifest_json=args.manifest_json,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
