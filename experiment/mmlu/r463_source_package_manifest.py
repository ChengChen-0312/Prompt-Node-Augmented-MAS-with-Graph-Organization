from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r463_source_package_manifest_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r463_source_package_manifest_report.md"
DEFAULT_MANIFEST_MD = "paper/artifacts/source_package_manifest.md"


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


def _resolve_input(raw: str) -> str:
    path = raw if raw.endswith(".tex") else f"{raw}.tex"
    return path if path.startswith("paper/") else f"paper/{path}"


def _collect_inputs(start: str = "paper/main.tex") -> List[str]:
    seen: Set[str] = set()
    stack = [start]
    while stack:
        rel = stack.pop()
        if rel in seen:
            continue
        seen.add(rel)
        path = _repo_path(rel)
        if not path.exists() or path.suffix != ".tex":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for raw in re.findall(r"\\input\{([^}]+)\}", text):
            child = _resolve_input(raw)
            if child not in seen:
                stack.append(child)
    return sorted(seen)


def render_manifest(summary: Dict[str, Any]) -> str:
    rows = [
        "# Source Package Manifest",
        "",
        "This manifest lists the local source files needed for journal-template conversion or manual external review.",
        "",
        "## Include",
        "",
    ]
    rows.extend(f"- `{path}`" for path in summary["package_sources"])
    rows.extend(["", "## Exclude", ""])
    rows.extend(f"- `{pattern}`" for pattern in summary["excluded_patterns"])
    rows.extend(
        [
            "",
            "## Packaging Notes",
            "",
            "- Do not include API key values or local `.env` files.",
            "- Do not treat this package as submission-ready until external audits and PDF compilation are complete.",
            "- Keep the current article scaffold as the editable source until JAIR or KAIS template conversion is explicitly performed.",
            "",
        ]
    )
    return "\n".join(rows)


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R463 Source Package Manifest",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Manifest: `{summary['manifest_md']}`",
        f"- Package source count: `{len(summary['package_sources'])}`",
        f"- Missing sources: `{len(summary['missing_sources'])}`",
        "",
        f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
        f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run_manifest(
    manifest_md: str = DEFAULT_MANIFEST_MD,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    package_sources = _collect_inputs()
    extras = [
        "paper/references.bib",
        "paper/artifacts/reproducibility_index.md",
        "paper/artifacts/journal_template_probe.md",
    ]
    for extra in extras:
        if extra not in package_sources:
            package_sources.append(extra)
    package_sources = sorted(package_sources)
    summary: Dict[str, Any] = {
        "run_id": "R463",
        "title": "Source package manifest",
        "claim_boundary": (
            "R463 lists source files for future template conversion or external review. "
            "It does not create an archive, include secrets, or certify submission readiness."
        ),
        "no_api": True,
        "broad_api": False,
        "manifest_md": manifest_md,
        "package_sources": package_sources,
        "missing_sources": [path for path in package_sources if not _repo_path(path).exists()],
        "excluded_patterns": [
            ".env",
            "*.key",
            "*api_key*",
            "run_logs/*_api_results.jsonl",
            "__pycache__",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R464_external_audit_authorization_checklist",
    }
    _write_text(manifest_md, render_manifest(summary))
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build source package manifest.")
    parser.add_argument("--manifest_md", default=DEFAULT_MANIFEST_MD)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_manifest(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
