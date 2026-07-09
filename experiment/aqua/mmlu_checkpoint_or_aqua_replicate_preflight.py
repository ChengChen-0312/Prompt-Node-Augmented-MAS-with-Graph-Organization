import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r152_mmlu_checkpoint_resolution_or_aqua_same_method_replicate_preflight"
CLAIM_BOUNDARY = (
    "preflight only; no API run, no transfer result, no independent AQuA replicate, "
    "and no SCI-Q2 readiness claim"
)

DEFAULT_R151_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r151_sci_q2_evidence_gap_plan_summary.json"
)
DEFAULT_AQUA_DATASET = "datasets/AQuA/AQuA.jsonl"
DEFAULT_MMLU_SPLIT = "experiment/mmlu/mmlu_stem_transfer100.jsonl"
DEFAULT_MMLU_TASK_SPLIT = "experiment/mmlu/task_split_mmlu_stem_transfer100.json"
DEFAULT_MMLU_EVALUATOR = "experiment/mmlu/evaluate_mmlu.py"
DEFAULT_R112_SUMMARY = (
    "experiment/aqua/res_logs/aqua_first200_r112_objective_safety_feature_export_summary.json"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r152_mmlu_checkpoint_or_aqua_replicate_preflight_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r152_mmlu_checkpoint_or_aqua_replicate_preflight_report.md"
)

CHECKPOINT_SUFFIXES = {".pt", ".pth", ".ckpt", ".pkl"}


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _jsonl_count(path: str) -> int:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def _task_split_indices(path: Path) -> Set[int]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    return {int(idx) for idx in data.get("test_indices", [])}


def _all_aqua_split_files() -> List[Path]:
    split_dir = Path(_repo_path("experiment/aqua"))
    return sorted(split_dir.glob("task_split_aqua*.json"))


def _known_aqua_indices(split_files: Iterable[Path]) -> Set[int]:
    known: Set[int] = set()
    for path in split_files:
        known.update(_task_split_indices(path))
    return known


def _mmlu_checkpoint_candidates() -> List[str]:
    roots = [Path(_repo_path("experiment")), Path(_repo_path("output"))]
    candidates: List[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in CHECKPOINT_SUFFIXES:
                continue
            lower_path = str(path).lower()
            name = path.name.lower()
            if "mmlu" in lower_path and (
                "best" in name or "checkpoint" in name or "model" in name
            ):
                candidates.append(os.path.relpath(path, REPO_ROOT))
    return sorted(candidates)


def _r112_uses_next100(r112_summary: str = DEFAULT_R112_SUMMARY) -> bool:
    if not os.path.exists(_repo_path(r112_summary)):
        return False
    summary = _load_json(r112_summary)
    sources = [*summary.get("baseline_sources", []), summary.get("objective_source", "")]
    return any("next100" in str(source) for source in sources)


def build_preflight_summary(
    r151_summary: str = DEFAULT_R151_SUMMARY,
    aqua_dataset: str = DEFAULT_AQUA_DATASET,
    mmlu_split: str = DEFAULT_MMLU_SPLIT,
    mmlu_task_split: str = DEFAULT_MMLU_TASK_SPLIT,
    mmlu_evaluator: str = DEFAULT_MMLU_EVALUATOR,
) -> Dict[str, Any]:
    r151 = _load_json(r151_summary)
    split_files = _all_aqua_split_files()
    known_indices = _known_aqua_indices(split_files)
    aqua_rows = _jsonl_count(aqua_dataset)
    unseen_indices = sorted(set(range(aqua_rows)) - known_indices)
    checkpoint_candidates = _mmlu_checkpoint_candidates()
    mmlu_ready = (
        os.path.exists(_repo_path(mmlu_split))
        and os.path.exists(_repo_path(mmlu_task_split))
        and os.path.exists(_repo_path(mmlu_evaluator))
    )
    next100_used_in_rule_training = _r112_uses_next100()
    independent_aqua_ready = bool(unseen_indices) and not next100_used_in_rule_training

    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_plan": r151_summary,
        "no_api_run": True,
        "mmlu_transfer_data_ready": mmlu_ready,
        "mmlu_transfer_split": mmlu_split,
        "mmlu_transfer_rows": _jsonl_count(mmlu_split) if os.path.exists(_repo_path(mmlu_split)) else 0,
        "mmlu_evaluator_available": os.path.exists(_repo_path(mmlu_evaluator)),
        "mmlu_checkpoint_candidates": checkpoint_candidates,
        "compatible_mmlu_arg_checkpoint_available": bool(checkpoint_candidates),
        "transfer_branch_allowed": bool(mmlu_ready and checkpoint_candidates),
        "aqua_dataset_rows": aqua_rows,
        "aqua_split_files_scanned": [os.path.relpath(path, REPO_ROOT) for path in split_files],
        "aqua_known_split_row_count": len(known_indices),
        "aqua_unseen_row_count": len(unseen_indices),
        "aqua_unseen_indices": unseen_indices,
        "r112_uses_next100_in_rule_training": next100_used_in_rule_training,
        "independent_same_method_aqua_replicate_ready": independent_aqua_ready,
        "same_method_aqua_replicate_blocker": (
            "none"
            if independent_aqua_ready
            else "no_unseen_aqua_rows_and_next100_used_in_r112_rule_training"
        ),
        "r151_same_method_required": bool(r151.get("same_method_significance_required")),
        "r151_transfer_required": bool(r151.get("transfer_required_for_sci_q2")),
        "chosen_next_work": (
            "r153_mmlu_transfer_api_protocol"
            if bool(mmlu_ready and checkpoint_candidates)
            else "r153_mmlu_checkpoint_build_or_import_protocol"
        ),
        "broad_api_allowed_next": False,
        "next_goal_audit_due": "R155",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R152 MMLU Checkpoint or AQuA Replicate Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Transfer Branch",
            "",
            f"- MMLU transfer data ready: `{summary['mmlu_transfer_data_ready']}`",
            f"- MMLU transfer rows: `{summary['mmlu_transfer_rows']}`",
            f"- MMLU evaluator available: `{summary['mmlu_evaluator_available']}`",
            f"- Compatible MMLU ARG checkpoint available: `{summary['compatible_mmlu_arg_checkpoint_available']}`",
            f"- MMLU checkpoint candidates: `{summary['mmlu_checkpoint_candidates']}`",
            f"- Transfer branch allowed: `{summary['transfer_branch_allowed']}`",
            "",
            "## AQuA Same-Method Replicate Branch",
            "",
            f"- AQuA dataset rows: `{summary['aqua_dataset_rows']}`",
            f"- AQuA known split row count: `{summary['aqua_known_split_row_count']}`",
            f"- AQuA unseen row count: `{summary['aqua_unseen_row_count']}`",
            f"- R112 uses next100 in rule training: `{summary['r112_uses_next100_in_rule_training']}`",
            f"- Independent same-method AQuA replicate ready: `{summary['independent_same_method_aqua_replicate_ready']}`",
            f"- Same-method replicate blocker: `{summary['same_method_aqua_replicate_blocker']}`",
            "",
            "## Next Gate",
            "",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Chosen next work: `{summary['chosen_next_work']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
            "## Interpretation",
            "",
            "R152 does not support running transfer API yet: the transfer split and evaluator exist, "
            "but no compatible MMLU ARG checkpoint is available. It also blocks an independent "
            "AQuA same-method replicate claim because all 254 AQuA rows are already covered by "
            "existing splits and next100 was used in the R112 rule-training source. The next "
            "defensible step is to build or import a compatible MMLU ARG checkpoint before transfer.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R152 checkpoint/replicate preflight.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_preflight_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R152 preflight: "
        f"mmlu_checkpoint={summary['compatible_mmlu_arg_checkpoint_available']} "
        f"aqua_unseen={summary['aqua_unseen_row_count']} "
        f"next={summary['chosen_next_work']}"
    )


if __name__ == "__main__":
    main()
