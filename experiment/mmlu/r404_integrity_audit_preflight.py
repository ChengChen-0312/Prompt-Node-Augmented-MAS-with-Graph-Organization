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


DEFAULT_MANIFEST_JSON = "experiment/mmlu/run_logs/mmlu_r404_integrity_audit_artifact_manifest.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r404_integrity_audit_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r404_integrity_audit_preflight_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _glob(patterns: Iterable[str], limit: int = 400) -> List[str]:
    paths: List[Path] = []
    for pattern in patterns:
        paths.extend(Path(REPO_ROOT).glob(pattern))
    return sorted({_rel(path) for path in paths if path.is_file()})[:limit]


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_audit_preflight() -> Dict[str, Any]:
    artifacts = {
        "evaluation_scripts": _glob(["experiment/**/*eval*.py", "experiment/**/*metric*.py", "experiment/**/r*.py", "tests/test_*.py"]),
        "result_files": _glob(["experiment/**/res_logs/*.json", "experiment/**/run_logs/*.json", "experiment/**/run_logs/*.jsonl", "experiment/**/run_logs/*.csv"]),
        "experiment_tracker": _glob(["EXPERIMENT_TRACKER.md", "EXPERIMENT_LOG.md"]),
        "paper_claims": _glob(["PAPER_PLAN.md", "paper/**/*.tex", "NARRATIVE_REPORT.md"]),
        "config_files": _glob(["**/*.yaml", "**/*.yml", "**/*.toml", "**/config*.json"]),
    }
    counts = {key: len(value) for key, value in artifacts.items()}
    return {
        "run_id": "R404",
        "title": "Experiment integrity audit preflight",
        "claim_boundary": (
            "R404 only collects artifact paths for experiment-audit. It does not perform or pass an integrity audit."
        ),
        "no_api": True,
        "broad_api": False,
        "artifact_counts": counts,
        "artifacts": artifacts,
        "external_review_required": True,
        "external_reviewer_available_in_this_session": False,
        "integrity_audit_complete": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R405_experiment_integrity_local_precheck",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R404 Experiment Integrity Audit Preflight",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Artifact Counts",
        "",
    ]
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["artifact_counts"].items())
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    manifest_json: str = DEFAULT_MANIFEST_JSON,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_audit_preflight()
    summary.update({"manifest_json": manifest_json, "summary_json": summary_json, "report_md": report_md})
    _write_json(manifest_json, {"artifacts": summary["artifacts"]})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect artifact paths for experiment integrity audit.")
    parser.add_argument("--manifest_json", default=DEFAULT_MANIFEST_JSON)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
