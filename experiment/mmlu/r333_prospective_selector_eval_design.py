from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r333_prospective_selector_eval_design_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r333_prospective_selector_eval_design_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_prospective_eval_design() -> Dict[str, Any]:
    return {
        "run_id": "R333",
        "title": "Prospective selector evaluation design",
        "claim_boundary": (
            "R333 freezes the prospective selector-evaluation protocol only. It does not construct prompts or call APIs."
        ),
        "no_api": True,
        "broad_api": False,
        "protocol": {
            "eval_name": "prospective_mmlu_selector_heldout",
            "model": "gpt-4o-2024-08-06",
            "baseline": "ARG-Designer-compatible fixed ARG output where available, otherwise direct ARG-style baseline prompt",
            "selector_policy_source": "experiment/mmlu/res_logs/mmlu_r327_augmented_selector_retraining_dry_run_summary.json",
            "exclude_training_manifest_hashes": True,
            "candidate_pool": [
                "MMLU STEM held-out items not present in R322/R325 manifests",
                "MMLU non-STEM held-out items not present in R310-R316 transfer/control runs",
            ],
            "target_size": {
                "stem": 24,
                "nonstem": 24,
            },
            "variants": [
                "arg_baseline_fixed_or_direct",
                "selector_promptnode_promptedge_policy",
                "cost_matched_plain_requery_control",
            ],
        },
        "leakage_forbidden_prompt_fields": [
            "task_id",
            "true_answer",
            "gold_answer",
            "is_correct",
            "evaluation_only",
            "source_ref_hash",
        ],
        "success_criteria": [
            "beat_arg_on_clean_stem_or_aqua_like_slice",
            "no_harm_on_nonstem",
            "fix_harm_nonnegative",
            "cost_not_worse_than_plain_requery",
            "no_label_audit_exclusions_in_main_metric_without_appendix_report",
        ],
        "estimated_budget": {
            "records": 48,
            "variants_with_api": 2,
            "max_api_calls": 96,
            "reason": "Bounded smoke-scale prospective check before larger held-out evaluation.",
        },
        "preflight_authorized_next": True,
        "api_execution_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R334_prospective_selector_eval_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R333 Prospective Selector Eval Design",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Protocol: `{summary['protocol']['eval_name']}`",
            f"- Target size: `{summary['protocol']['target_size']}`",
            f"- Variants: `{summary['protocol']['variants']}`",
            f"- Success criteria: `{summary['success_criteria']}`",
            f"- Estimated budget: `{summary['estimated_budget']}`",
            f"- API execution authorized next: `{summary['api_execution_authorized_next']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(summary_json: str = DEFAULT_SUMMARY_JSON, report_md: str = DEFAULT_REPORT_MD) -> Dict[str, Any]:
    summary = build_prospective_eval_design()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R333 prospective selector eval design.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
