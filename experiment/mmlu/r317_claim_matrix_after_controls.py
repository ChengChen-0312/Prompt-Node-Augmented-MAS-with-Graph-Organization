from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R313_SUMMARY = "experiment/mmlu/res_logs/mmlu_r313_claim_matrix_summary.json"
DEFAULT_R316_SUMMARY = "experiment/mmlu/res_logs/mmlu_r316_promptedge_cost_controls_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r317_claim_matrix_after_controls_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r317_claim_matrix_after_controls_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _score(item: Dict[str, Any]) -> str:
    return f"{int(item.get('correct', 0))}/{int(item.get('evaluated_records', 0))}"


def build_claim_matrix_summary(
    r313_summary: str = DEFAULT_R313_SUMMARY,
    r316_summary: str = DEFAULT_R316_SUMMARY,
) -> Dict[str, Any]:
    r313 = _load_json(r313_summary)
    r316 = _load_json(r316_summary)
    evidence = dict(r313.get("evidence", {}))
    by_variant = r316.get("by_variant", {})
    arg = by_variant.get("arg_baseline_fixed", {})
    plain = by_variant.get("plain_requery", {})
    node_only = by_variant.get("node_only_no_promptedge_text", {})

    evidence["mmlu_nonstem_plain_requery"] = {
        "baseline": _score(arg),
        "proposed": _score(plain),
        "delta_correct": plain.get("delta_vs_arg"),
        "fix_harm": plain.get("fix_harm"),
        "claim": "cost_matched_plain_requery_ties_arg_but_not_beaten",
    }
    evidence["mmlu_nonstem_node_only_no_edge_text"] = {
        "baseline": _score(arg),
        "proposed": _score(node_only),
        "delta_correct": node_only.get("delta_vs_arg"),
        "fix_harm": node_only.get("fix_harm"),
        "claim": "remove_promptedge_text_harms_nonstem_safety",
    }

    return {
        "run_id": "R317",
        "title": "Claim matrix after promptedge and cost controls",
        "claim_boundary": (
            "R317 updates R313 with R316 controls. It does not broaden claims: non-STEM remains no-harm only "
            "under warning-only lifecycle safety replay."
        ),
        "no_api": True,
        "broad_api": False,
        "evidence": evidence,
        "claim_permissions": {
            "plain_requery_beaten_on_nonstem": int(plain.get("correct", 0)) < int(arg.get("correct", 0)),
            "plain_requery_tied_not_beaten_on_nonstem": int(plain.get("correct", 0)) == int(arg.get("correct", 0)),
            "promptedge_text_needed_for_nonstem_safety": int(node_only.get("harms", 0)) > 0,
            "mmlu_nonstem_improvement_allowed": False,
            "mmlu_nonstem_no_harm_allowed_only_with_lifecycle_safety": True,
            "training_authorized": False,
            "sci_q2_ready": False,
        },
        "paper_guidance": [
            "Do not claim non-STEM improvement: plain requery ties ARG and raw PromptNode harms.",
            "Use non-STEM as a boundary/no-harm result after lifecycle safety replay.",
            "Use no-edge-text harm as evidence that PromptEdges are not just decorative text.",
            "Keep the positive claim on AQuA audit-clean and MMLU STEM until broader held-out validation is run.",
        ],
        "training_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R318_symbolic_family_ablation",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R317 Claim Matrix After Controls",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Slice | Baseline | Proposed | Delta | Fix/Harm | Claim |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name, item in summary["evidence"].items():
        rows.append(
            f"| `{name}` | `{item.get('baseline', '-')}` | `{item.get('proposed', '-')}` | `{item.get('delta_correct', '-')}` | `{item.get('fix_harm', '-')}` | {item.get('claim', '')} |"
        )
    rows.extend(["", "## Paper Guidance", ""])
    rows.extend(f"- {item}" for item in summary["paper_guidance"])
    rows.append("")
    return "\n".join(rows)


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_claim_matrix_summary()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R317 claim matrix after controls.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
