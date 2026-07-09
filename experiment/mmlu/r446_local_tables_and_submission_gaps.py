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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r446_local_tables_and_submission_gaps_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r446_local_tables_and_submission_gaps_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    target = _repo_path(path)
    return json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _main_rows() -> List[Dict[str, str]]:
    r321 = _load_json("experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json")
    rows = list(r321.get("paper_main_results", []))
    r414 = _load_json("experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json")
    rows.append(
        {
            "slice": "MMLU_DefinitionChallenge_fresh24",
            "baseline": f"{r414.get('arg_correct')}/{r414.get('records')}",
            "promptnode": f"{r414.get('hybrid_correct')}/{r414.get('records')}",
            "delta_correct": r414.get("delta_correct"),
            "fix_harm": f"{r414.get('fixes')}/{r414.get('harms')}/{r414.get('wrong_forward_count')}",
            "paper_claim": "targeted_nonmath_positive_no_harm",
            "note": "Fresh targeted concept-definition split; not broad non-STEM.",
        }
    )
    return rows


def _main_results_table(rows: List[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        slice_name = row["slice"].replace("_", r"\_")
        claim_role = row["paper_claim"].replace("_", r"\_")
        body.append(
            f"{slice_name} & {row['baseline']} & {row['promptnode']} & {row['delta_correct']} & {row['fix_harm']} & {claim_role} \\\\"
        )
    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            r"\small",
            r"\caption{Main scoped results. Fix/harm/wrong-forward is reported where available; a dash denotes an audit-clean aggregate without per-item switch accounting in the table source.}",
            r"\label{tab:main-results}",
            r"\begin{tabular}{lcccll}",
            r"\toprule",
            r"Slice & ARG & PromptNode & $\Delta$ & Fix/Harm & Claim role \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )


def _cost_results_table(rows: List[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        row_id = row["id"].replace("_", r"\_")
        evidence = row.get("cost_evidence", "").replace("_", r"\_")
        body.append(
            f"{row_id} & {row['score']} & {row['cost']} & {row['cost_per_task']} & {evidence} \\\\"
        )
    return "\n".join(
        [
            r"\begin{table}[t]",
            r"\centering",
            r"\small",
            r"\caption{Cost-normalized evidence rows. MMLU STEM cost is a probe estimate, not original exact R306 accounting.}",
            r"\label{tab:cost-results}",
            r"\begin{tabular}{lcccl}",
            r"\toprule",
            r"Row & Score & Cost & Cost/task & Evidence \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )


def _update_results_section() -> None:
    path = _repo_path("paper/sections/5_results.tex")
    text = path.read_text(encoding="utf-8")
    inserts = "\n\\input{tables/main_results}\n\\input{tables/cost_results}\n"
    if r"\input{tables/main_results}" in text:
        return
    marker = "\\label{sec:results}\n"
    text = text.replace(marker, marker + inserts, 1)
    path.write_text(text, encoding="utf-8")


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R446 Local Tables And Submission Gaps",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Tables",
        "",
    ]
    rows.extend(f"- `{path}`" for path in summary["tables_created"])
    rows.extend(["", "## Submission Gaps", ""])
    rows.extend(f"- `{gap}`" for gap in summary["submission_gaps"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_tables(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    main_rows = _main_rows()
    cost_rows = _load_json("experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json").get("cost_rows", [])
    _write_text("paper/tables/main_results.tex", _main_results_table(main_rows))
    _write_text("paper/tables/cost_results.tex", _cost_results_table(cost_rows))
    _update_results_section()
    summary: Dict[str, Any] = {
        "run_id": "R446",
        "title": "Local tables and submission gaps",
        "claim_boundary": (
            "R446 creates local LaTeX result tables from result files. It does not replace external audits "
            "or PDF compilation."
        ),
        "no_api": True,
        "broad_api": False,
        "tables_created": ["paper/tables/main_results.tex", "paper/tables/cost_results.tex"],
        "main_result_rows": len(main_rows),
        "cost_rows": len(cost_rows),
        "submission_gaps": [
            "external_audits_pending",
            "latex_compile_pending",
            "final_caption_polish_pending",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R447_local_smoke_after_tables",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate local LaTeX result and cost tables.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_tables(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
