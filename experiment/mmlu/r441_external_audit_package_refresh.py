from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r441_external_audit_package_refresh_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r441_external_audit_package_refresh_report.md"

EXPERIMENT_RESULT_FILES = [
    "experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json",
    "experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json",
    "experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json",
    "experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json",
    "experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json",
    "experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json",
    "experiment/mmlu/res_logs/mmlu_r440_paper_claim_number_static_audit_summary.json",
]

PAPER_FILES = [
    "paper/main.tex",
    "paper/sections/0_abstract.tex",
    "paper/sections/1_introduction.tex",
    "paper/sections/2_related_work.tex",
    "paper/sections/3_method.tex",
    "paper/sections/4_experimental_setup.tex",
    "paper/sections/5_results.tex",
    "paper/sections/6_case_studies.tex",
    "paper/sections/7_limitations.tex",
    "paper/sections/8_conclusion.tex",
    "paper/references.bib",
]


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


def _existing(paths: List[str]) -> List[str]:
    return [path for path in paths if _repo_path(path).exists()]


def _prompt(title: str, instructions: str, files: List[str]) -> str:
    rows = [
        f"# {title}",
        "",
        instructions,
        "",
        "## Files To Inspect",
        "",
    ]
    rows.extend(f"- `{path}`" for path in files)
    rows.extend(["", "## Required Output", "", "Return PASS/WARN/FAIL with file:line evidence and concrete fixes."])
    return "\n".join(rows)


def build_packages() -> Dict[str, Dict[str, Any]]:
    experiment_prompt = "experiment/mmlu/run_logs/mmlu_r441_experiment_integrity_audit_prompt.md"
    citation_prompt = "experiment/mmlu/run_logs/mmlu_r441_citation_context_audit_prompt.md"
    claim_prompt = "experiment/mmlu/run_logs/mmlu_r441_paper_claim_audit_prompt.md"
    experiment_files = _existing(EXPERIMENT_RESULT_FILES)
    paper_files = _existing(PAPER_FILES)
    citation_files = _existing(
        [
            "paper/references.bib",
            "paper/sections/2_related_work.tex",
            "paper/.aris/citation-audit/r438_static_contexts.json",
            ".aris/verify-papers/r436_citation_metadata.json",
        ]
    )

    _write_text(
        experiment_prompt,
        _prompt(
            "R441 External Experiment Integrity Audit Prompt",
            (
                "Audit whether the reported PromptNode-Augmented MAS results are grounded in result files, "
                "use ARG-Designer as the baseline, and avoid broad nonmath/general claims."
            ),
            experiment_files,
        ),
    )
    _write_text(
        citation_prompt,
        _prompt(
            "R441 External Citation Context Audit Prompt",
            (
                "Audit each related-work citation for existence, metadata correctness, and whether the cited "
                "paper supports the exact surrounding sentence."
            ),
            citation_files,
        ),
    )
    _write_text(
        claim_prompt,
        _prompt(
            "R441 External Paper Claim Audit Prompt",
            (
                "Audit every number and comparison in the paper against the raw/result JSON files. "
                "Do not use executor summaries as evidence except as file lists."
            ),
            [*paper_files, *experiment_files],
        ),
    )
    return {
        "experiment_integrity_audit": {
            "prompt_md": experiment_prompt,
            "files": experiment_files,
            "required": True,
            "executed": False,
        },
        "citation_context_audit": {
            "prompt_md": citation_prompt,
            "files": citation_files,
            "required": True,
            "executed": False,
        },
        "paper_claim_audit": {
            "prompt_md": claim_prompt,
            "files": [*paper_files, *experiment_files],
            "required": True,
            "executed": False,
        },
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R441 External Audit Package Refresh",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Packages",
        "",
    ]
    for name, package in summary["audit_packages"].items():
        rows.append(f"- `{name}`: `{package['prompt_md']}`; executed=`{package['executed']}`")
    rows.extend(["", "## Goal Check", ""])
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_refresh(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    packages = build_packages()
    summary: Dict[str, Any] = {
        "run_id": "R441",
        "title": "External audit package refresh",
        "claim_boundary": (
            "R441 refreshes external audit prompts and performs the five-run goal checkpoint. "
            "It does not execute external reviewer audits."
        ),
        "no_api": True,
        "broad_api": False,
        "audit_packages": packages,
        "external_reviews_executed": [],
        "iterations_since_last_goal_check": ["R437", "R438", "R439", "R440", "R441"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "complete_initial_paper_draft_now_exists": True,
            "arg_designer_remains_main_baseline": True,
            "promptnode_virtual_node_not_answer_patch": True,
            "audits_not_faked": True,
            "submission_blockers_explicit": True,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R442_local_smoke_test_suite",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh external audit packages for the paper draft.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_refresh(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
