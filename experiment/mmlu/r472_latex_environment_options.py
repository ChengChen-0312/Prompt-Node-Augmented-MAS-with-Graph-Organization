from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r472_latex_environment_options_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r472_latex_environment_options_report.md"
DEFAULT_OPTIONS_MD = "paper/artifacts/latex_environment_options.md"


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


def render_options(summary: Dict[str, Any]) -> str:
    rows = [
        "# LaTeX Environment Options",
        "",
        f"- Installation performed: `{summary['installation_performed']}`",
        f"- latexmk: `{summary['engine_probe']['latexmk']}`",
        f"- pdflatex: `{summary['engine_probe']['pdflatex']}`",
        f"- Compile status: `{summary['compile_status']}`",
        "",
        "## Install Options",
        "",
    ]
    for item in summary["install_options"]:
        rows.extend(
            [
                f"### {item['name']}",
                "",
                f"- Command/source: `{item['command_or_source']}`",
                f"- Tradeoff: {item['tradeoff']}",
                "",
            ]
        )
    rows.extend(["## Compile Command After Engine Exists", ""])
    rows.extend(f"- `{cmd}`" for cmd in summary["future_compile_commands"])
    rows.append("")
    return "\n".join(rows)


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R472 LaTeX Environment Options",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Options file: `{summary['options_md']}`",
            f"- Installation performed: `{summary['installation_performed']}`",
            f"- Compile status: `{summary['compile_status']}`",
            "",
            f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run_options(
    options_md: str = DEFAULT_OPTIONS_MD,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    engine_probe = {
        "latexmk": shutil.which("latexmk"),
        "pdflatex": shutil.which("pdflatex"),
        "tectonic": shutil.which("tectonic"),
    }
    engine_available = bool(engine_probe["latexmk"] or engine_probe["pdflatex"] or engine_probe["tectonic"])
    summary: Dict[str, Any] = {
        "run_id": "R472",
        "title": "LaTeX environment options",
        "claim_boundary": (
            "R472 probes local TeX engines and records install options. It does not install software or compile PDF."
        ),
        "no_api": True,
        "broad_api": False,
        "options_md": options_md,
        "engine_probe": engine_probe,
        "engine_available": engine_available,
        "installation_performed": False,
        "compile_status": "engine_available_compile_next" if engine_available else "blocked_no_latex_engine",
        "install_options": [
            {
                "name": "MacTeX",
                "command_or_source": "Install MacTeX from tug.org/mactex or Homebrew cask if acceptable locally.",
                "tradeoff": "Most complete and least likely to miss packages; large install.",
            },
            {
                "name": "TinyTeX",
                "command_or_source": "Install TinyTeX, then add missing packages on demand.",
                "tradeoff": "Smaller footprint; may need iterative package installs.",
            },
            {
                "name": "Tectonic",
                "command_or_source": "Install tectonic for self-contained compilation.",
                "tradeoff": "Convenient for many papers, but journal-specific style compatibility should be checked.",
            },
        ],
        "future_compile_commands": [
            "cd paper && latexmk -pdf -interaction=nonstopmode main.tex",
            "cd paper && pdflatex -interaction=nonstopmode main.tex && bibtex main && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex",
            "cd paper && tectonic main.tex",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R473_compile_command_harness",
    }
    _write_text(options_md, render_options(summary))
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record local LaTeX engine options.")
    parser.add_argument("--options_md", default=DEFAULT_OPTIONS_MD)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_options(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
