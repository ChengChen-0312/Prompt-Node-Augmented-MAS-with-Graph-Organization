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


DEFAULT_R404_SUMMARY = "experiment/mmlu/res_logs/mmlu_r404_integrity_audit_preflight_summary.json"
DEFAULT_R405_SUMMARY = "experiment/mmlu/res_logs/mmlu_r405_experiment_integrity_local_precheck_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r406_external_integrity_review_package_summary.json"
DEFAULT_PACKAGE_JSON = "experiment/mmlu/run_logs/mmlu_r406_external_integrity_review_package.json"
DEFAULT_PROMPT_MD = "experiment/mmlu/run_logs/mmlu_r406_external_integrity_review_prompt.md"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r406_external_integrity_review_package_report.md"


CRITICAL_RESULTS = [
    "experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json",
    "experiment/mmlu/res_logs/mmlu_r381_option_binding_fresh_eval_analysis_summary.json",
    "experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json",
    "experiment/mmlu/res_logs/mmlu_r401_contrastive_verifier_targeted_analysis_and_goal_audit_summary.json",
    "experiment/mmlu/res_logs/mmlu_r402_result_to_claim_synthesis_for_paper_summary.json",
    "experiment/mmlu/res_logs/mmlu_r405_experiment_integrity_local_precheck_summary.json",
]

CRITICAL_SCRIPTS = [
    "experiment/mmlu/r321_paper_evidence_table_and_training_gate.py",
    "experiment/mmlu/r381_option_binding_fresh_eval_analysis.py",
    "experiment/mmlu/r396_larger_mixed_nonmath_fresh_analysis.py",
    "experiment/mmlu/r401_contrastive_verifier_targeted_analysis_and_goal_audit.py",
    "experiment/mmlu/r402_result_to_claim_synthesis_for_paper.py",
    "experiment/mmlu/r405_experiment_integrity_local_precheck.py",
]


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(_repo_path(path).read_text(encoding="utf-8"))


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _existing(paths: Iterable[str]) -> List[str]:
    return [path for path in paths if _repo_path(path).exists()]


def _bullet_list(paths: Iterable[str]) -> str:
    return "\n".join(f"    - {path}" for path in paths)


def build_review_prompt(artifacts: Dict[str, List[str]], r405_summary: str) -> str:
    critical_eval = _existing(CRITICAL_SCRIPTS)
    critical_results = _existing(CRITICAL_RESULTS)
    paper_claims = artifacts.get("paper_claims", [])
    config_files = artifacts.get("config_files", [])
    return f"""You are an experiment integrity auditor. Start from the assumption that the
evaluation is compromised somewhere - your job is to find where. Be adversarial.
Trust nothing the author tells you - verify everything yourself.

Files to read:
- Critical evaluation scripts:
{_bullet_list(critical_eval)}
- Critical result files:
{_bullet_list(critical_results)}
- Local precheck:
    - {r405_summary}
- Paper claims:
{_bullet_list(paper_claims)}
- Config files:
{_bullet_list(config_files[:30])}

The full artifact manifest is in:
    - experiment/mmlu/run_logs/mmlu_r404_integrity_audit_artifact_manifest.json

## Audit Checklist

### A. Ground Truth Provenance
For each evaluation script:
1. Where does "ground truth" / "reference" / "target" come from?
2. Is it loaded from the dataset, or generated/derived from model outputs?
3. If derived, is it explicitly labeled as proxy evaluation?
4. Are official eval scripts used when available for this benchmark?
FAIL if GT is derived from model outputs without explicit proxy labeling.

### B. Score Normalization
For each metric computation:
1. Is any metric divided by max/min/mean of the model's own output?
2. Are raw scores reported alongside any normalized scores?
3. Are any scores suspiciously close to 1.0 or 100%?
FAIL if normalization denominator comes from prediction statistics.

### C. Result File Existence
For each claim in the paper/narrative:
1. Does the referenced result file actually exist?
2. Does the claimed metric key exist in that file?
3. Does the claimed number match what is in the file?
4. Is the experiment status complete rather than TODO or IN_PROGRESS?
FAIL if claimed results reference nonexistent files or mismatched numbers.

### D. Dead Code Detection
For each metric function defined in eval scripts:
1. Is it actually called in any evaluation pipeline?
2. Does its output appear in any result file?
WARN if metric functions exist but are never called.

### E. Scope Assessment
1. How many datasets, subjects, and configurations were actually tested?
2. How many seeds/runs per configuration?
3. Does the paper use words like "comprehensive", "extensive", "robust", or "general"?
4. Is the actual scope sufficient for those claims?
WARN if scope language exceeds actual evidence.

### F. Evaluation Type Classification
Classify each evaluation as:
- real_gt
- synthetic_proxy
- self_supervised_proxy
- simulation_only
- human_eval

## Output Format

For each check (A-F), report:
- Status: PASS | WARN | FAIL
- Evidence: exact file:line references
- Details: what specifically was found

Overall verdict: PASS | WARN | FAIL
"""


def build_review_package(
    r404_summary: str = DEFAULT_R404_SUMMARY,
    r405_summary: str = DEFAULT_R405_SUMMARY,
) -> Dict[str, Any]:
    r404 = _load_json(r404_summary)
    r405 = _load_json(r405_summary)
    artifacts = r404.get("artifacts", {})
    artifact_counts = r404.get("artifact_counts", {key: len(value) for key, value in artifacts.items()})
    review_prompt = build_review_prompt(artifacts, r405_summary)
    return {
        "run_id": "R406",
        "title": "External integrity review package and five-run goal checkpoint",
        "claim_boundary": (
            "R406 packages evidence for independent audit and checks goal alignment after R402-R406. "
            "It does not execute the external review and does not authorize paper claims."
        ),
        "no_api": True,
        "broad_api": False,
        "artifact_counts": artifact_counts,
        "critical_evaluation_scripts": _existing(CRITICAL_SCRIPTS),
        "critical_result_files": _existing(CRITICAL_RESULTS),
        "r405_local_precheck_status": r405.get("local_precheck_status"),
        "review_prompt": review_prompt,
        "external_review_required": True,
        "external_review_executed": False,
        "integrity_audit_complete": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "iterations_since_last_goal_check": ["R402", "R403", "R404", "R405", "R406"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "arg_designer_remains_main_baseline": True,
            "promptnode_first_class_boundary_preserved": True,
            "transfer_and_no_harm_evidence_recorded": True,
            "broad_general_improvement_not_claimed": True,
            "overclaiming_blocked": True,
            "next_gap": "Either obtain independent audit or add stronger positive nonmath transfer evidence.",
        },
        "next_required_run": "R407_external_audit_or_nonmath_positive_evidence",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R406 External Integrity Review Package",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- R405 local precheck: `{summary['r405_local_precheck_status']}`",
        f"- External review executed: `{summary['external_review_executed']}`",
        f"- Integrity audit complete: `{summary['integrity_audit_complete']}`",
        f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
        "",
        "## Artifact Counts",
        "",
    ]
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["artifact_counts"].items())
    rows.extend(["", "## Goal Check", ""])
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r404_summary: str = DEFAULT_R404_SUMMARY,
    r405_summary: str = DEFAULT_R405_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    package_json: str = DEFAULT_PACKAGE_JSON,
    prompt_md: str = DEFAULT_PROMPT_MD,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_review_package(r404_summary=r404_summary, r405_summary=r405_summary)
    summary.update({"summary_json": summary_json, "package_json": package_json, "prompt_md": prompt_md, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_json(package_json, {"review_prompt": summary["review_prompt"], "critical_result_files": summary["critical_result_files"]})
    _write_text(prompt_md, summary["review_prompt"])
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build external experiment integrity review package.")
    parser.add_argument("--r404_summary", default=DEFAULT_R404_SUMMARY)
    parser.add_argument("--r405_summary", default=DEFAULT_R405_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--package_json", default=DEFAULT_PACKAGE_JSON)
    parser.add_argument("--prompt_md", default=DEFAULT_PROMPT_MD)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
