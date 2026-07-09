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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r454_reproducibility_artifact_index_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r454_reproducibility_artifact_index_report.md"
DEFAULT_ARTIFACT_INDEX_MD = "paper/artifacts/reproducibility_index.md"


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


def _primary_result_files() -> List[Dict[str, str]]:
    return [
        {
            "path": "experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json",
            "role": "AQuA official and audit-clean claim table.",
        },
        {
            "path": "experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json",
            "role": "MMLU STEM main97 evidence and training-gate status.",
        },
        {
            "path": "experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json",
            "role": "Mixed non-STEM no-harm boundary.",
        },
        {
            "path": "experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json",
            "role": "Targeted DefinitionChallenge positive transfer result.",
        },
        {
            "path": "experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json",
            "role": "Cost table with MMLU STEM probe-estimate caveat.",
        },
        {
            "path": "experiment/mmlu/res_logs/mmlu_r453_appendix_noise_audit_pack_summary.json",
            "role": "Audit-clean appendix manifest.",
        },
    ]


def _local_verification_commands() -> List[str]:
    return [
        "python -m unittest tests.test_r440_paper_claim_number_static_audit",
        "python -m unittest tests.test_r447_local_smoke_after_tables",
        "python -m unittest tests.test_r452_five_run_goal_audit_and_compile_probe",
        "python -m unittest tests.test_r453_appendix_noise_audit_pack",
        "python -m unittest tests.test_r454_reproducibility_artifact_index",
    ]


def render_artifact_index(summary: Dict[str, Any]) -> str:
    rows = [
        "# Reproducibility Artifact Index",
        "",
        "This index records how to locate the current evidence package for the PromptNode-Augmented MAS paper draft.",
        "",
        "## Model And Environment",
        "",
        "- Main API model for fresh evidence runs: `gpt-4o-2024-08-06`.",
        "- ARG-Designer is the primary baseline and should be run with matched settings wherever fresh API reproduction is needed.",
        f"- API environment file path: `{summary['env_file_path']}`.",
        "- API key values are intentionally redacted and must not be committed, printed, or pasted into manuscripts.",
        "",
        "## Primary Result Files",
        "",
    ]
    for item in summary["primary_result_files"]:
        rows.append(f"- `{item['path']}`: {item['role']}")
    rows.extend(
        [
            "",
            "## Audit-Clean Policy",
            "",
            "- Do not edit benchmark files silently.",
            "- Report official and audit-clean columns side by side.",
            "- Do not train or distill on corrected test labels.",
            "- Keep AQuA task_59/task_139/task_228 and MMLU audited items in appendix-only handling.",
            "",
            "## Local Verification Commands",
            "",
        ]
    )
    rows.extend(f"- `{cmd}`" for cmd in summary["local_verification_commands"])
    rows.extend(
        [
            "",
            "## Pending External Checks",
            "",
            "- External experiment-integrity audit.",
            "- External paper-claim audit.",
            "- External citation-context audit.",
            "- PDF compile and visual inspection once a LaTeX engine is available.",
            "",
        ]
    )
    return "\n".join(rows)


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R454 Reproducibility Artifact Index",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Artifact index: `{summary['artifact_index_md']}`",
        f"- Primary result files: `{len(summary['primary_result_files'])}`",
        f"- API key values redacted: `{summary['api_key_values_redacted']}`",
        "",
        "## Verification Commands",
        "",
    ]
    rows.extend(f"- `{cmd}`" for cmd in summary["local_verification_commands"])
    rows.extend(
        [
            "",
            f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )
    return "\n".join(rows)


def run_index(
    artifact_index_md: str = DEFAULT_ARTIFACT_INDEX_MD,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "run_id": "R454",
        "title": "Reproducibility artifact index",
        "claim_boundary": (
            "R454 writes a local artifact index for reproducibility. It does not read, expose, or validate API key values."
        ),
        "no_api": True,
        "broad_api": False,
        "artifact_index_md": artifact_index_md,
        "env_file_path": "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env",
        "api_key_values_redacted": True,
        "primary_result_files": _primary_result_files(),
        "local_verification_commands": _local_verification_commands(),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R455_full_local_smoke_after_appendix_artifact",
    }
    _write_text(artifact_index_md, render_artifact_index(summary))
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write reproducibility artifact index.")
    parser.add_argument("--artifact_index_md", default=DEFAULT_ARTIFACT_INDEX_MD)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_index(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
