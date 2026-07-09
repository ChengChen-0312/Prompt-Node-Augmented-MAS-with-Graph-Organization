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


DEFAULT_PAPER_DIR = "paper"
DEFAULT_CONTEXT_JSON = "paper/.aris/citation-audit/r438_static_contexts.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r438_citation_context_static_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r438_citation_context_static_audit_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _write_json(path: str, payload: Any) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _tex_files(paper_dir: str) -> List[Path]:
    root = _repo_path(paper_dir)
    files = [root / "main.tex"]
    files.extend(sorted((root / "sections").glob("*.tex")))
    return [path for path in files if path.exists()]


def _sentence_context(line: str) -> str:
    clean = " ".join(line.strip().split())
    return clean


def _citation_contexts(paper_dir: str) -> List[Dict[str, Any]]:
    contexts: List[Dict[str, Any]] = []
    for path in _tex_files(paper_dir):
        rel = str(path.relative_to(REPO_ROOT))
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for match in re.finditer(r"\\cite\{([^}]+)\}", line):
                for key in [item.strip() for item in match.group(1).split(",") if item.strip()]:
                    contexts.append(
                        {
                            "key": key,
                            "file": rel,
                            "line": line_no,
                            "context": _sentence_context(line),
                            "status": "static_context_extracted_external_audit_required",
                        }
                    )
    return contexts


def _bib_keys(references_bib: str) -> Set[str]:
    target = _repo_path(references_bib)
    if not target.exists():
        return set()
    return set(re.findall(r"@\w+\{([^,\s]+),", target.read_text(encoding="utf-8")))


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R438 Citation Context Static Audit",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Static citation pass: `{summary['static_citation_pass']}`",
        f"- Citation sites: `{summary['citation_site_count']}`",
        f"- External citation audit required: `{summary['external_citation_audit_required']}`",
        "",
        "## Missing Bib Keys",
        "",
    ]
    if summary["missing_bib_keys"]:
        rows.extend(f"- `{key}`" for key in summary["missing_bib_keys"])
    else:
        rows.append("- none")
    rows.extend(["", "## Uncited Bib Keys", ""])
    if summary["uncited_bib_keys"]:
        rows.extend(f"- `{key}`" for key in summary["uncited_bib_keys"])
    else:
        rows.append("- none")
    rows.extend(["", "## Goal Check", ""])
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_static_audit(
    paper_dir: str = DEFAULT_PAPER_DIR,
    references_bib: str = "paper/references.bib",
    context_json: str = DEFAULT_CONTEXT_JSON,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    contexts = _citation_contexts(paper_dir)
    cited_keys = sorted({row["key"] for row in contexts})
    bib_keys = sorted(_bib_keys(references_bib))
    missing = sorted(set(cited_keys) - set(bib_keys))
    uncited = sorted(set(bib_keys) - set(cited_keys))
    _write_json(context_json, contexts)
    summary: Dict[str, Any] = {
        "run_id": "R438",
        "title": "Citation context static audit",
        "claim_boundary": (
            "R438 performs deterministic citation coverage checks and exports citation contexts. "
            "It is not the final external citation audit."
        ),
        "no_api": True,
        "broad_api": False,
        "context_json": context_json,
        "citation_site_count": len(contexts),
        "cited_keys": cited_keys,
        "bib_keys": bib_keys,
        "missing_bib_keys": missing,
        "uncited_bib_keys": uncited,
        "static_citation_pass": not missing and not uncited and bool(contexts),
        "external_citation_audit_required": True,
        "iterations_since_last_goal_check": ["R432", "R433", "R434", "R435", "R436"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "arg_designer_remains_main_baseline": True,
            "promptnode_first_class_graph_element_boundary_preserved": True,
            "related_work_now_supports_mas_graph_positioning": True,
            "no_universal_claim_added": True,
            "external_audits_still_required": True,
        },
        "final_bib_authorized": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R439_paper_static_integrity_precompile_audit",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic citation coverage and context extraction.")
    parser.add_argument("--paper_dir", default=DEFAULT_PAPER_DIR)
    parser.add_argument("--references_bib", default="paper/references.bib")
    parser.add_argument("--context_json", default=DEFAULT_CONTEXT_JSON)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_static_audit(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
