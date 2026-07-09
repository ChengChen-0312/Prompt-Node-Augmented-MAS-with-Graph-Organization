from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_PAPER_DIR = "paper"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r432_paper_main_tex_scaffold_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r432_paper_main_tex_scaffold_report.md"


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


def _existing_sections(paper_dir: str) -> List[str]:
    section_dir = _repo_path(f"{paper_dir}/sections")
    if not section_dir.exists():
        return []
    return [str(path.relative_to(REPO_ROOT)) for path in sorted(section_dir.glob("*.tex"))]


def _main_tex(section_files: List[str]) -> str:
    inputs = []
    for path in section_files:
        tex_path = Path(path)
        inputs.append(rf"\input{{{tex_path.with_suffix('').as_posix().removeprefix('paper/')}}}")
    return "\n".join(
        [
            r"\documentclass[11pt]{article}",
            r"\usepackage[margin=1in]{geometry}",
            r"\usepackage{amsmath,amssymb,amsthm}",
            r"\usepackage{booktabs}",
            r"\usepackage{hyperref}",
            r"\usepackage{xcolor}",
            r"\input{math_commands}",
            "",
            r"\title{PromptNode-Augmented Multi-Agent Graphs for Robust Reasoning}",
            r"\author{Anonymous Authors}",
            r"\date{}",
            "",
            r"\begin{document}",
            r"\maketitle",
            "",
            *inputs,
            "",
            r"\end{document}",
            "",
        ]
    )


def _math_commands_tex() -> str:
    return "\n".join(
        [
            r"% Shared notation for PromptNode-Augmented MAS.",
            r"\newcommand{\PN}{\mathrm{PN}}",
            r"\newcommand{\PE}{\mathrm{PE}}",
            r"\newcommand{\MAS}{\mathrm{MAS}}",
            r"\newcommand{\ARG}{\mathrm{ARG}}",
            r"\newcommand{\AQuA}{\textsc{AQuA}}",
            r"\newcommand{\MMLU}{\textsc{MMLU}}",
            r"\DeclareMathOperator*{\argmax}{arg\,max}",
            "",
        ]
    )


def _references_bib() -> str:
    return "% R432 scaffold only. R433+ must add audited cited entries.\n"


def _maybe_backup_scaffold_targets(paper_dir: str) -> str | None:
    targets = [
        _repo_path(f"{paper_dir}/main.tex"),
        _repo_path(f"{paper_dir}/math_commands.tex"),
        _repo_path(f"{paper_dir}/references.bib"),
    ]
    if not any(path.exists() for path in targets):
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = _repo_path(f"{paper_dir}-backup-r432-{stamp}")
    suffix = 1
    while backup.exists():
        backup = _repo_path(f"{paper_dir}-backup-r432-{stamp}-{suffix}")
        suffix += 1
    shutil.copytree(_repo_path(paper_dir), backup)
    return str(backup.relative_to(REPO_ROOT))


def build_scaffold_summary(paper_dir: str = DEFAULT_PAPER_DIR) -> Dict[str, Any]:
    section_files = _existing_sections(paper_dir)
    referenced = list(section_files)
    stale = sorted(set(section_files) - set(referenced))
    return {
        "run_id": "R432",
        "title": "Paper main.tex scaffold",
        "claim_boundary": (
            "R432 creates a compile-oriented LaTeX scaffold around the bounded draft sections. "
            "It does not create a complete paper draft or authorize paper claims."
        ),
        "no_api": True,
        "broad_api": False,
        "paper_dir": paper_dir,
        "main_tex": f"{paper_dir}/main.tex",
        "math_commands_tex": f"{paper_dir}/math_commands.tex",
        "references_bib": f"{paper_dir}/references.bib",
        "referenced_sections": referenced,
        "stale_section_files": stale,
        "scaffold_links_all_existing_sections": bool(section_files) and not stale,
        "complete_paper_draft": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R433_front_matter_and_related_work_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R432 Paper Main TeX Scaffold",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Main TeX: `{summary['main_tex']}`",
        f"- Math commands: `{summary['math_commands_tex']}`",
        f"- References: `{summary['references_bib']}`",
        f"- Complete paper draft: `{summary['complete_paper_draft']}`",
        "",
        "## Referenced Sections",
        "",
    ]
    rows.extend(f"- `{path}`" for path in summary["referenced_sections"])
    rows.extend(["", "## Stale Sections", ""])
    if summary["stale_section_files"]:
        rows.extend(f"- `{path}`" for path in summary["stale_section_files"])
    else:
        rows.append("- none")
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_scaffold(
    paper_dir: str = DEFAULT_PAPER_DIR,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_scaffold_summary(paper_dir=paper_dir)
    backup = _maybe_backup_scaffold_targets(paper_dir)
    _write_text(summary["main_tex"], _main_tex(summary["referenced_sections"]))
    _write_text(summary["math_commands_tex"], _math_commands_tex())
    _write_text(summary["references_bib"], _references_bib())
    summary["backup_created"] = backup
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create paper/main.tex scaffold for existing draft sections.")
    parser.add_argument("--paper_dir", default=DEFAULT_PAPER_DIR)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_scaffold(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
