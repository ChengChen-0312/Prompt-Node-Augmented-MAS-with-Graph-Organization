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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r453_appendix_noise_audit_pack_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r453_appendix_noise_audit_pack_report.md"
DEFAULT_APPENDIX_TEX = "paper/appendices/label_audit.tex"


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


def _tex_escape(value: str) -> str:
    return (
        str(value)
        .replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
    )


def _aqua_items(r266: Dict[str, Any]) -> List[Dict[str, str]]:
    task114 = r266.get("task114_audit", {})
    return [
        {
            "task_id": "task_59",
            "status": "excluded_from_audit_clean",
            "reason": "dataset-disagreement/bad-option boundary identified during tail34 audit; kept out of clean claims.",
            "paper_use": "appendix_only",
        },
        {
            "task_id": "task_139",
            "status": "excluded_from_audit_clean",
            "reason": "dataset-disagreement flag from R264/R266; kept out of clean claims.",
            "paper_use": "appendix_only",
        },
        {
            "task_id": "task_228",
            "status": "excluded_from_audit_clean",
            "reason": "dataset-disagreement flag from R264/R266; kept out of clean claims.",
            "paper_use": "appendix_only",
        },
        {
            "task_id": "task_114",
            "status": "sensitivity_boundary",
            "reason": (
                "official label D is not strictly supported under the deterministic interval check; "
                f"R266 deterministic label is {task114.get('deterministic_label', 'C')}."
            ),
            "paper_use": "sensitivity_only",
        },
    ]


def _mmlu_items(r303: Dict[str, Any], r300: Dict[str, Any]) -> List[Dict[str, str]]:
    audit_items = {item["task_id"]: item for item in r300.get("audit_items", [])}
    rows = []
    for task_id in r303.get("excluded_task_ids", []):
        item = audit_items.get(task_id, {})
        rows.append(
            {
                "task_id": task_id,
                "status": item.get("label_verdict", "appendix_only"),
                "reason": r303.get("exclusion_reasons", {}).get(task_id, item.get("evidence_note", "")),
                "paper_use": "excluded_from_training_distillation_and_main97",
                "audit_clean_answer": item.get("audit_clean_answer", ""),
                "source": item.get("source_type", ""),
            }
        )
    return rows


def render_appendix(summary: Dict[str, Any]) -> str:
    rows = [
        r"\section{Audit-Clean Evaluation Details}",
        r"\label{app:label-audit}",
        "",
        (
            "We do not silently rewrite benchmark files or train on corrected test labels. "
            "The main text reports official and audit-clean columns side by side, while this appendix records "
            "which records were excluded or used only for sensitivity analysis."
        ),
        "",
        r"\subsection{AQuA Tail34}",
        "",
        (
            "For AQuA, the audit-clean tail31 result removes task\\_59, task\\_139, and task\\_228. "
            "The conservative tail30 sensitivity result additionally removes task\\_114 as a boundary-label case. "
            "The official labels remain unchanged in the benchmark files."
        ),
        "",
        r"\begin{table}[h]",
        r"\centering",
        r"\small",
        r"\begin{tabular}{llll}",
        r"\toprule",
        r"Task & Status & Paper use & Reason \\",
        r"\midrule",
    ]
    for item in summary["aqua_audit_items"]:
        rows.append(
            f"{_tex_escape(item['task_id'])} & {_tex_escape(item['status'])} & "
            f"{_tex_escape(item['paper_use'])} & {_tex_escape(item['reason'])} \\\\"
        )
    rows.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption{AQuA records handled outside the primary audit-clean claim.}",
            r"\label{tab:aqua-label-audit}",
            r"\end{table}",
            "",
            r"\subsection{MMLU STEM Transfer}",
            "",
            (
                "For MMLU, three records are excluded from further training, distillation, and main97 aggregation. "
                "Two are wrong-groundtruth items identified by the audit protocol; the statistics item is a known "
                "ARG failure used during gate discovery and is therefore appendix-only to avoid tuning to one case."
            ),
            "",
            r"\begin{table}[h]",
            r"\centering",
            r"\small",
            r"\begin{tabular}{llll}",
            r"\toprule",
            r"Task & Status & Clean answer & Paper use \\",
            r"\midrule",
        ]
    )
    for item in summary["mmlu_audit_items"]:
        rows.append(
            f"{_tex_escape(item['task_id'])} & {_tex_escape(item['status'])} & "
            f"{_tex_escape(item.get('audit_clean_answer', ''))} & {_tex_escape(item['paper_use'])} \\\\"
        )
    rows.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption{MMLU records excluded from main97 training/distillation and kept for appendix sensitivity.}",
            r"\label{tab:mmlu-label-audit}",
            r"\end{table}",
            "",
            r"\paragraph{Reporting policy.}",
            (
                "Official and audit-clean numbers must remain paired. The audit-clean column is used to avoid "
                "rewarding systems for matching unsupported labels, but the official benchmark is not edited."
            ),
            "",
        ]
    )
    return "\n".join(rows)


def _ensure_main_includes_appendix(appendix_tex: str) -> bool:
    main_path = _repo_path("paper/main.tex")
    text = main_path.read_text(encoding="utf-8")
    input_line = r"\input{appendices/label_audit}"
    if input_line in text:
        return False
    marker = "\\input{sections/8_conclusion}\n\n"
    insert = "\\input{sections/8_conclusion}\n\n\\appendix\n" + input_line + "\n\n"
    if marker not in text:
        raise ValueError("Could not locate conclusion marker in paper/main.tex")
    main_path.write_text(text.replace(marker, insert, 1), encoding="utf-8")
    return True


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R453 Appendix Noise Audit Pack",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Appendix TeX: `{summary['appendix_tex']}`",
        f"- Main TeX updated: `{summary['main_tex_updated']}`",
        f"- Silent benchmark rewrite: `{summary['silent_benchmark_rewrite']}`",
        "",
        "## AQuA Items",
        "",
    ]
    rows.extend(f"- `{item['task_id']}`: `{item['status']}` / `{item['paper_use']}`" for item in summary["aqua_audit_items"])
    rows.extend(["", "## MMLU Items", ""])
    rows.extend(f"- `{item['task_id']}`: `{item['status']}` / `{item['paper_use']}`" for item in summary["mmlu_audit_items"])
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


def run_pack(
    r266_summary: str = "experiment/aqua/res_logs/aqua_r266_audit_clean_rescore_summary.json",
    r303_summary: str = "experiment/mmlu/res_logs/mmlu_r303_audit_exclusion_protocol_summary.json",
    r300_summary: str = "experiment/mmlu/res_logs/mmlu_r300_goal_and_label_audit_summary.json",
    appendix_tex: str = DEFAULT_APPENDIX_TEX,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    r266 = _load_json(r266_summary)
    r303 = _load_json(r303_summary)
    r300 = _load_json(r300_summary)
    summary: Dict[str, Any] = {
        "run_id": "R453",
        "title": "Appendix noise audit pack",
        "claim_boundary": (
            "R453 writes an appendix that documents existing label-audit and audit-clean policies. "
            "It does not edit benchmark data, add new exclusions, or authorize paper claims."
        ),
        "no_api": True,
        "broad_api": False,
        "appendix_tex": appendix_tex,
        "aqua_audit_items": _aqua_items(r266),
        "mmlu_audit_items": _mmlu_items(r303, r300),
        "silent_benchmark_rewrite": False,
        "training_on_corrected_test_labels": False,
        "main_text_policy": "report_official_and_audit_clean_side_by_side",
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R454_reproducibility_artifact_index",
    }
    _write_text(appendix_tex, render_appendix(summary))
    summary["main_tex_updated"] = _ensure_main_includes_appendix(appendix_tex)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write audit-clean appendix pack.")
    parser.add_argument("--r266_summary", default="experiment/aqua/res_logs/aqua_r266_audit_clean_rescore_summary.json")
    parser.add_argument("--r303_summary", default="experiment/mmlu/res_logs/mmlu_r303_audit_exclusion_protocol_summary.json")
    parser.add_argument("--r300_summary", default="experiment/mmlu/res_logs/mmlu_r300_goal_and_label_audit_summary.json")
    parser.add_argument("--appendix_tex", default=DEFAULT_APPENDIX_TEX)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_pack(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
