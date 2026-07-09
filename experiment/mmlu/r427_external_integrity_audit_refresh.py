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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r427_external_integrity_audit_refresh_summary.json"
DEFAULT_PROMPT_MD = "experiment/mmlu/run_logs/mmlu_r427_external_integrity_audit_refresh_prompt.md"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r427_external_integrity_audit_refresh_report.md"


CRITICAL_RESULT_FILES = [
    "experiment/mmlu/res_logs/mmlu_r402_result_to_claim_synthesis_for_paper_summary.json",
    "experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json",
    "experiment/mmlu/res_logs/mmlu_r415_update_claim_matrix_after_nonmath_positive_summary.json",
    "experiment/mmlu/res_logs/mmlu_r416_cost_normalized_claim_table_and_goal_audit_summary.json",
    "experiment/mmlu/res_logs/mmlu_r425_analyze_mmlu_stem_cost_probe_summary.json",
    "experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json",
    "experiment/mmlu/run_logs/mmlu_r413_definition_challenge_gate_api_results.jsonl",
    "experiment/mmlu/run_logs/mmlu_r419_lifecycle_trace_events.jsonl",
    "experiment/mmlu/run_logs/mmlu_r424_mmlu_stem_cost_probe_api_results.jsonl",
    "experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json",
    "PAPER_PLAN.md",
]

CRITICAL_SCRIPT_FILES = [
    "experiment/mmlu/r413_definition_challenge_gate_api_execution.py",
    "experiment/mmlu/r414_definition_challenge_gate_analysis.py",
    "experiment/mmlu/r416_cost_normalized_claim_table_and_goal_audit.py",
    "experiment/mmlu/r419_lifecycle_trace_replay.py",
    "experiment/mmlu/r424_mmlu_stem_cost_probe_api_execution.py",
    "experiment/mmlu/r426_update_cost_table_with_stem_probe_and_goal_audit.py",
]


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _existing(paths: List[str]) -> List[str]:
    return [path for path in paths if _repo_path(path).exists()]


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _bullet(paths: List[str]) -> str:
    return "\n".join(f"- {path}" for path in paths)


def build_review_prompt(result_files: List[str], script_files: List[str]) -> str:
    return f"""You are an experiment integrity auditor. Be adversarial and verify the updated PromptNode-Augmented MAS evidence after R413-R426.

Critical result files:
{_bullet(result_files)}

Critical scripts:
{_bullet(script_files)}

Specific claims to verify:
- AQuA audit-clean and official claims remain scoped to R271/R321.
- MMLU STEM R306 remains a positive accuracy result, but its cost row is now a R424/R425 probe estimate.
- The probe estimate must be treated as probe_estimate_not_exact, never exact R306 cost.
- DefinitionChallenge R413/R414 is a fresh targeted nonmath positive result: ARG 21/24 vs DefinitionChallenge 22/24, fix/harm/wrong-forward 1/0/0.
- R419 lifecycle traces are replay artifacts from R413 outputs, not new accuracy evidence.
- Broad nonmath and universal multiple-choice improvement remain forbidden.

Audit checklist:
1. Ground Truth Provenance: check that labels come from dataset/evaluation_only and are not model-generated references.
2. Score Normalization: check that no metric is normalized by model output statistics.
3. Result File Existence: every cited number must exist in the listed result files.
4. Dead Code / Phantom Result: scripts that define claimed metrics must actually write the result files.
5. Scope: verify that DefinitionChallenge is described as targeted/narrow, not broad nonmath.
6. Cost Evidence: distinguish direct API costs, allocated control costs, and probe estimates.

Output PASS/WARN/FAIL for each checklist item and an overall verdict. Include file:line evidence where possible.
"""


def build_audit_refresh() -> Dict[str, Any]:
    result_files = _existing(CRITICAL_RESULT_FILES)
    script_files = _existing(CRITICAL_SCRIPT_FILES)
    prompt = build_review_prompt(result_files, script_files)
    return {
        "run_id": "R427",
        "title": "External integrity audit refresh",
        "claim_boundary": (
            "R427 refreshes the external audit package after new nonmath, lifecycle, and cost-probe evidence. It does not "
            "execute the external review."
        ),
        "no_api": True,
        "broad_api": False,
        "critical_result_files": result_files,
        "critical_script_files": script_files,
        "review_prompt": prompt,
        "external_review_required": True,
        "external_review_executed": False,
        "integrity_audit_complete": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R428_updated_local_claim_integrity_precheck",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R427 External Integrity Audit Refresh",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Critical result files: `{len(summary['critical_result_files'])}`",
            f"- Critical script files: `{len(summary['critical_script_files'])}`",
            f"- External review executed: `{summary['external_review_executed']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    prompt_md: str = DEFAULT_PROMPT_MD,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_audit_refresh()
    summary.update({"summary_json": summary_json, "prompt_md": prompt_md, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(prompt_md, summary["review_prompt"])
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh external integrity audit package.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--prompt_md", default=DEFAULT_PROMPT_MD)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
