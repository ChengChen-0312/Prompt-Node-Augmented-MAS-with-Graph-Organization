import argparse
import glob
import json
import math
import os
import sys
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r148_tail34_replay_statistical_audit_and_transfer_preflight"
CLAIM_BOUNDARY = (
    "statistical audit and transfer preflight only; no new API, fresh full-run, "
    "transfer, robustness, or SCI-readiness claim"
)

DEFAULT_R147_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r147_frozen_selector_replay_summary.json"
DEFAULT_MMLU_TRANSFER_JSONL = "experiment/mmlu/mmlu_stem_transfer100.jsonl"
DEFAULT_MMLU_TASK_SPLIT = "experiment/mmlu/task_split_mmlu_stem_transfer100.json"
DEFAULT_MMLU_EVALUATOR = "experiment/mmlu/evaluate_mmlu.py"
DEFAULT_MMLU_SPLIT_SUMMARY = "experiment/mmlu/res_logs/mmlu_stem_transfer_split_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r148_statistical_audit_transfer_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r148_statistical_audit_transfer_preflight_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _jsonl_count(path: str) -> int:
    if not os.path.exists(_repo_path(path)):
        return 0
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def _wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> List[float]:
    if total <= 0:
        return [0.0, 0.0]
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half_width = (
        z
        * math.sqrt((p * (1 - p) / total) + (z * z / (4 * total * total)))
        / denominator
    )
    return [round(max(0.0, center - half_width), 6), round(min(1.0, center + half_width), 6)]


def _mcnemar_exact_p_two_sided(improvements: int, regressions: int) -> float:
    discordant = improvements + regressions
    if discordant == 0:
        return 1.0
    smaller = min(improvements, regressions)
    tail = sum(math.comb(discordant, k) for k in range(smaller + 1)) * (0.5 ** discordant)
    return round(min(1.0, 2 * tail), 6)


def _checkpoint_candidates() -> List[str]:
    patterns = [
        "output/**/*mmlu*.pth",
        "../**/*mmlu*best*.pth",
    ]
    candidates: List[str] = []
    for pattern in patterns:
        candidates.extend(glob.glob(_repo_path(pattern), recursive=True))
    return sorted({path for path in candidates if "mmlu" in path.lower()})


def build_tail34_statistical_audit_transfer_preflight_summary(
    r147_summary: str = DEFAULT_R147_SUMMARY,
    mmlu_transfer_jsonl: str = DEFAULT_MMLU_TRANSFER_JSONL,
    mmlu_task_split: str = DEFAULT_MMLU_TASK_SPLIT,
    mmlu_evaluator: str = DEFAULT_MMLU_EVALUATOR,
    mmlu_split_summary: str = DEFAULT_MMLU_SPLIT_SUMMARY,
) -> Dict[str, Any]:
    r147 = _load_json(r147_summary)
    rows = r147["rows"]
    improvements = sum(1 for row in rows if row["fix"])
    regressions = sum(1 for row in rows if row["harm"])
    total = int(r147["total_tasks"])
    baseline_correct = sum(1 for row in rows if row["baseline_is_solved"])
    selected_correct = sum(1 for row in rows if row["selected_is_solved"])
    mmlu_split = _load_json(mmlu_split_summary) if os.path.exists(_repo_path(mmlu_split_summary)) else {}
    checkpoints = _checkpoint_candidates()

    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_summary": r147_summary,
        "baseline_accuracy": r147["baseline_accuracy"],
        "selected_accuracy": r147["selected_accuracy"],
        "baseline_accuracy_wilson_95": _wilson_interval(baseline_correct, total),
        "selected_accuracy_wilson_95": _wilson_interval(selected_correct, total),
        "accuracy_delta": round(r147["selected_accuracy_rate"] - r147["baseline_accuracy_rate"], 6),
        "paired_improvements": improvements,
        "paired_regressions": regressions,
        "discordant_pairs": improvements + regressions,
        "mcnemar_exact_p_two_sided": _mcnemar_exact_p_two_sided(improvements, regressions),
        "statistically_significant_at_0_05": (
            _mcnemar_exact_p_two_sided(improvements, regressions) < 0.05
        ),
        "baseline_correct_per_dollar": r147["baseline_correct_per_dollar"],
        "selected_correct_per_dollar": r147["selected_correct_per_dollar"],
        "cost_normalized_superiority_supported": (
            r147["selected_correct_per_dollar"] > r147["baseline_correct_per_dollar"]
        ),
        "mmlu_transfer_jsonl_exists": os.path.exists(_repo_path(mmlu_transfer_jsonl)),
        "mmlu_transfer_rows": _jsonl_count(mmlu_transfer_jsonl),
        "mmlu_task_split_exists": os.path.exists(_repo_path(mmlu_task_split)),
        "mmlu_evaluator_exists": os.path.exists(_repo_path(mmlu_evaluator)),
        "mmlu_subject_count": mmlu_split.get("subject_count", 0),
        "mmlu_arg_checkpoint_available": bool(checkpoints),
        "mmlu_checkpoint_candidates": checkpoints,
        "transfer_api_allowed_next": False,
        "broad_api_allowed_next": False,
        "next_protocol": "r149_transfer_checkpoint_or_aqua_replicate_protocol",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R148 Tail34 Statistical Audit and Transfer Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Tail34 Replay Statistics",
            "",
            f"- Baseline accuracy: `{summary['baseline_accuracy']}`",
            f"- Selected accuracy: `{summary['selected_accuracy']}`",
            f"- Accuracy delta: `{summary['accuracy_delta']}`",
            f"- Baseline Wilson 95% CI: `{summary['baseline_accuracy_wilson_95']}`",
            f"- Selected Wilson 95% CI: `{summary['selected_accuracy_wilson_95']}`",
            f"- Paired improvements: `{summary['paired_improvements']}`",
            f"- Paired regressions: `{summary['paired_regressions']}`",
            f"- McNemar exact two-sided p: `{summary['mcnemar_exact_p_two_sided']}`",
            f"- Significant at 0.05: `{summary['statistically_significant_at_0_05']}`",
            f"- Baseline correct per dollar: `{summary['baseline_correct_per_dollar']}`",
            f"- Selected correct per dollar: `{summary['selected_correct_per_dollar']}`",
            f"- Cost-normalized superiority supported: `{summary['cost_normalized_superiority_supported']}`",
            "",
            "## Transfer Preflight",
            "",
            f"- MMLU transfer JSONL exists: `{summary['mmlu_transfer_jsonl_exists']}`",
            f"- MMLU transfer rows: `{summary['mmlu_transfer_rows']}`",
            f"- MMLU task split exists: `{summary['mmlu_task_split_exists']}`",
            f"- MMLU evaluator exists: `{summary['mmlu_evaluator_exists']}`",
            f"- MMLU subject count: `{summary['mmlu_subject_count']}`",
            f"- MMLU ARG checkpoint available: `{summary['mmlu_arg_checkpoint_available']}`",
            f"- Transfer API allowed next: `{summary['transfer_api_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Interpretation",
            "",
            "The R147 replay improves accuracy by two paired fixes and zero regressions, but "
            "with only two discordant pairs the exact McNemar p-value is `0.5`; the result "
            "is not statistically significant. Transfer data and evaluator scaffolding exist, "
            "but no compatible local MMLU ARG checkpoint was found, so transfer API remains "
            "blocked until the checkpoint path is supplied or a new compatible checkpoint is produced.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build R148 statistical audit and transfer preflight."
    )
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_tail34_statistical_audit_transfer_preflight_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R148 statistical audit: "
        f"delta={summary['accuracy_delta']} p={summary['mcnemar_exact_p_two_sided']} "
        f"transfer_checkpoint={summary['mmlu_arg_checkpoint_available']}"
    )


if __name__ == "__main__":
    main()
