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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r330_paper_tables_and_figures_plan_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r330_paper_tables_and_figures_plan_report.md"


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


def _table(
    table_id: str,
    title: str,
    source: str,
    placement: str,
    purpose: str,
) -> Dict[str, str]:
    return {
        "id": table_id,
        "title": title,
        "source": source,
        "placement": placement,
        "purpose": purpose,
    }


def _figure(figure_id: str, title: str, source: str, placement: str, purpose: str) -> Dict[str, str]:
    return {
        "id": figure_id,
        "title": title,
        "source": source,
        "placement": placement,
        "purpose": purpose,
    }


def build_paper_tables_and_figures_plan() -> Dict[str, Any]:
    tables: List[Dict[str, str]] = [
        _table(
            "main_results",
            "Main accuracy, clean audit, fix/harm, and cost-normalized results",
            "experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json",
            "main",
            "Show AQuA audit-clean and MMLU STEM gains, plus non-STEM no-harm boundary.",
        ),
        _table(
            "ablation_controls",
            "Component and negative-control ablations",
            "experiment/mmlu/res_logs/mmlu_r319_ablation_table_update_summary.json",
            "main",
            "Answer reviewer questions about SafetyGate, lifecycle, PromptEdge text, symbolic/nonmath families, and cost-matched requery.",
        ),
        _table(
            "selector_training_gate",
            "Offline selector manifest, hard negatives, and PromptEdge safety feature",
            "experiment/mmlu/res_logs/mmlu_r328_selector_policy_claim_update_summary.json",
            "main_or_appendix",
            "Support train-time graph-policy feasibility without overclaiming external accuracy.",
        ),
        _table(
            "case_studies",
            "Mechanism case studies",
            "experiment/mmlu/res_logs/mmlu_r329_case_study_extraction_summary.json",
            "main_and_appendix",
            "Explain verifier repair, MemoryBridge pruning, PromptEdge false-forward block, and lifecycle cost control.",
        ),
        _table(
            "label_audit_appendix",
            "Audit-clean exclusions and sensitivity analysis",
            "experiment/mmlu/res_logs/mmlu_r313_claim_matrix_summary.json",
            "appendix",
            "Document noisy-label exclusions for AQuA and MMLU without hiding the official-score boundary.",
        ),
    ]
    figures = [
        _figure(
            "promptnode_augmented_graph_workflow",
            "PromptNode-Augmented MAS workflow",
            "/Users/chencheng/Downloads/论文/update2.docx plus R329 cases",
            "main",
            "Show PromptNode insertion, read/write/forward edges, lifecycle update/compress/prune/merge/upgrade, and final aggregation.",
        ),
        _figure(
            "selector_training_pipeline",
            "Leakage-safe graph-policy selector training pipeline",
            "R322-R328",
            "main",
            "Show manifest construction, hard-negative augmentation, transparent selector, and claim gate.",
        ),
        _figure(
            "accuracy_cost_tradeoff",
            "Accuracy and cost-normalized control comparison",
            "R309/R315/R319",
            "main_or_appendix",
            "Show why always-forward/no-lifecycle is not a good substitute for routed PromptNodes.",
        ),
        _figure(
            "case_study_graphs",
            "Case-study graph transitions",
            "R329",
            "appendix",
            "Visualize verifier repair, MemoryBridge prune, and PromptEdge block.",
        ),
    ]
    return {
        "run_id": "R330",
        "title": "Paper tables and figures plan",
        "claim_boundary": (
            "R330 plans paper artifacts from existing evidence. It does not add new claims or mark the paper submission-ready."
        ),
        "no_api": True,
        "broad_api": False,
        "tables": tables,
        "figures": figures,
        "ready_to_draft_sections": [
            "method",
            "experiments",
            "ablation",
            "case_study",
            "limitations",
        ],
        "missing_before_sci_q2_submission": [
            "prospective selector evaluation",
            "larger held-out transfer or a second non-AQuA dataset with positive/no-harm result",
            "complete related-work synthesis",
            "paper claim audit against raw logs",
            "citation audit",
        ],
        "sci_q2_ready": False,
        "next_required_run": "R331_paper_outline_scaffold",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R330 Paper Tables And Figures Plan",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Tables",
        "",
        "| ID | Placement | Source | Purpose |",
        "|---|---|---|---|",
    ]
    for table in summary["tables"]:
        rows.append(f"| `{table['id']}` | `{table['placement']}` | `{table['source']}` | {table['purpose']} |")
    rows.extend(["", "## Figures", "", "| ID | Placement | Source | Purpose |", "|---|---|---|---|"])
    for figure in summary["figures"]:
        rows.append(f"| `{figure['id']}` | `{figure['placement']}` | `{figure['source']}` | {figure['purpose']} |")
    rows.extend(["", "## Missing Before SCI-Q2 Submission", ""])
    rows.extend(f"- {item}" for item in summary["missing_before_sci_q2_submission"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(summary_json: str = DEFAULT_SUMMARY_JSON, report_md: str = DEFAULT_REPORT_MD) -> Dict[str, Any]:
    summary = build_paper_tables_and_figures_plan()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R330 paper table and figure plan.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
