from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r473_compile_command_harness_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r473_compile_command_harness_report.md"


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


def _select_command() -> List[str]:
    if shutil.which("latexmk"):
        return ["latexmk", "-pdf", "-interaction=nonstopmode", "main.tex"]
    if shutil.which("tectonic"):
        return ["tectonic", "main.tex"]
    if shutil.which("pdflatex"):
        return ["pdflatex", "-interaction=nonstopmode", "main.tex"]
    return []


def _run_compile(command: List[str]) -> Dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=_repo_path("paper"),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
        check=False,
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "output_tail": proc.stdout[-4000:],
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R473 Compile Command Harness",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Engine available: `{summary['engine_available']}`",
            f"- Compile attempted: `{summary['compile_attempted']}`",
            f"- Compile status: `{summary['compile_status']}`",
            f"- PDF exists: `{summary['pdf_exists']}`",
            f"- PDF verified: `{summary['pdf_verified']}`",
            "",
            f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run_harness(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    command = _select_command()
    engine_available = bool(command)
    compile_result: Dict[str, Any] | None = None
    if engine_available:
        compile_result = _run_compile(command)
    pdf_path = _repo_path("paper/main.pdf")
    pdf_exists = pdf_path.exists()
    compile_attempted = compile_result is not None
    compile_ok = bool(compile_result and compile_result.get("returncode") == 0 and pdf_exists)
    summary: Dict[str, Any] = {
        "run_id": "R473",
        "title": "Compile command harness",
        "claim_boundary": (
            "R473 provides a reusable compile harness. It only verifies a PDF if a TeX engine exists and compilation succeeds."
        ),
        "no_api": True,
        "broad_api": False,
        "selected_command": command,
        "engine_available": engine_available,
        "compile_attempted": compile_attempted,
        "compile_result": compile_result,
        "compile_status": "compiled_pdf_exists" if compile_ok else ("compile_failed" if compile_attempted else "blocked_no_latex_engine"),
        "pdf_path": "paper/main.pdf",
        "pdf_exists": pdf_exists,
        "pdf_verified": compile_ok,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R474_local_smoke_after_latex_harness",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or skip LaTeX compile depending on local engine availability.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_harness(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
