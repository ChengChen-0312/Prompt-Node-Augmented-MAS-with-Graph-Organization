from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r457_static_manuscript_audit_after_appendix_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r457_static_manuscript_audit_after_appendix_report.md"
FORBIDDEN_CLAIM_PATTERNS = [
    "submission-ready",
    "universal improvement",
    "broad general improvement",
    "improves all multiple-choice",
    "broad nonmath improvement",
]
TODO_PATTERNS = ["TODO", "FIXME", "XXX", "[VERIFY]"]


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


def _paper_files_from_main(main_text: str) -> List[str]:
    return [_resolve_input(match) for match in re.findall(r"\\input\{([^}]+)\}", main_text)]


def _scan_patterns(files: List[str], patterns: List[str]) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for rel in files:
        path = _repo_path(rel)
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            for pattern in patterns:
                if pattern in line:
                    hits.append({"path": rel, "line": lineno, "pattern": pattern, "text": line.strip()})
    return hits


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R457 Static Manuscript Audit After Appendix",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Appendix integrated: `{summary['appendix_integrated']}`",
        f"- Appendix count: `{summary['appendix_count']}`",
        f"- Missing inputs: `{len(summary['missing_inputs'])}`",
        f"- TODO hits: `{len(summary['todo_hits'])}`",
        f"- Forbidden claim hits: `{len(summary['forbidden_claim_hits'])}`",
        "",
        "## Inputs",
        "",
    ]
    rows.extend(f"- `{path}`" for path in summary["referenced_inputs"])
    rows.extend(["", "## Missing Inputs", ""])
    rows.extend(f"- `{path}`" for path in summary["missing_inputs"]) if summary["missing_inputs"] else rows.append("- none")
    rows.extend(["", "## Forbidden Claim Hits", ""])
    rows.extend(
        f"- `{hit['path']}:{hit['line']}` pattern=`{hit['pattern']}`"
        for hit in summary["forbidden_claim_hits"]
    ) if summary["forbidden_claim_hits"] else rows.append("- none")
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


def run_audit(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    main_path = _repo_path("paper/main.tex")
    main_text = main_path.read_text(encoding="utf-8")
    referenced_inputs = _paper_files_from_main(main_text)
    missing_inputs = [path for path in referenced_inputs if not _repo_path(path).exists()]
    paper_files = ["paper/main.tex"] + referenced_inputs
    summary: Dict[str, Any] = {
        "run_id": "R457",
        "title": "Static manuscript audit after appendix",
        "claim_boundary": (
            "R457 checks static manuscript wiring after appendix insertion. It does not compile PDF or execute audits."
        ),
        "no_api": True,
        "broad_api": False,
        "referenced_inputs": referenced_inputs,
        "missing_inputs": missing_inputs,
        "appendix_integrated": r"\input{appendices/label_audit}" in main_text and r"\appendix" in main_text,
        "appendix_count": main_text.count(r"\appendix"),
        "todo_hits": _scan_patterns(paper_files, TODO_PATTERNS),
        "forbidden_claim_patterns": FORBIDDEN_CLAIM_PATTERNS,
        "forbidden_claim_hits": _scan_patterns(paper_files, FORBIDDEN_CLAIM_PATTERNS),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R458_caption_table_reference_polish",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run static manuscript audit after appendix insertion.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_audit(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
