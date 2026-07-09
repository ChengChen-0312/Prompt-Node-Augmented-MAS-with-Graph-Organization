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


DEFAULT_R365_SUMMARY = "experiment/mmlu/res_logs/mmlu_r365_wrong_forward_and_missed_fix_analysis_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r367_adversarial_candidate_verifier_design_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r367_adversarial_candidate_verifier_design_report.md"


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


def _node(node_id: str, role: str, purpose: str, forward_contract: str) -> Dict[str, str]:
    return {
        "id": node_id,
        "role": role,
        "purpose": purpose,
        "forward_contract": forward_contract,
    }


def build_adversarial_verifier_design(r365_summary: str = DEFAULT_R365_SUMMARY) -> Dict[str, Any]:
    r365 = _load_json(r365_summary)
    nodes: List[Dict[str, str]] = [
        _node(
            "PN_AdversarialCandidateVerifier",
            "Verifier PromptNode",
            "Try to falsify a high-confidence single candidate before it can override ARG.",
            "Write contradiction evidence; forward block signal if an independent contradiction is found.",
        ),
        _node(
            "PN_ChemPhysicsVerifier",
            "Tool/Verifier PromptNode",
            "Generate candidates for chemistry and physics missed-fix clusters using formula, conservation, and concept checks.",
            "Forward only with explicit equation/concept evidence and candidate_label.",
        ),
        _node(
            "PN_PassageHistoryEntailmentVerifier",
            "Verifier PromptNode",
            "Generate candidates for history/passage missed-fix tasks using visible quote entailment.",
            "Forward only when the option is directly supported by quoted or visible source text.",
        ),
        _node(
            "PN_AbstractMathCounterexampleVerifier",
            "Verifier PromptNode",
            "Challenge abstract math candidates with counterexamples, theorem condition checks, and option-by-option negation.",
            "Block candidate if theorem assumptions are misstated or a counterexample supports another option.",
        ),
    ]
    return {
        "run_id": "R367",
        "title": "Adversarial candidate verifier design",
        "claim_boundary": (
            "R367 designs candidate-quality improvements after R363/R365. It does not relax the R360 gate and does "
            "not authorize API execution."
        ),
        "no_api": True,
        "broad_api": False,
        "new_promptnodes": nodes,
        "new_promptedges": [
            "challenge_candidate_before_forward",
            "write_adversarial_contradiction",
            "block_forward_on_independent_contradiction",
            "route_domain_missed_fix_to_specialized_verifier",
            "merge_candidate_and_adversarial_evidence_before_gate",
        ],
        "target_wrong_forward_task_ids": r365.get("wrong_forward_task_ids", []),
        "target_missed_fix_count": int(r365.get("missed_fix_count", 0)),
        "target_missed_fix_subject_counts": r365.get("missed_fix_subject_counts", {}),
        "relax_gate_threshold": False,
        "api_execution_authorized_next": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R368_adversarial_verifier_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R367 Adversarial Candidate Verifier Design",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| PromptNode | Purpose | Contract |",
        "|---|---|---|",
    ]
    for node in summary["new_promptnodes"]:
        rows.append(f"| `{node['id']}` | {node['purpose']} | {node['forward_contract']} |")
    rows.extend(["", "## PromptEdges", ""])
    rows.extend(f"- `{edge}`" for edge in summary["new_promptedges"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r365_summary: str = DEFAULT_R365_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_adversarial_verifier_design(r365_summary=r365_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R367 adversarial candidate verifier design.")
    parser.add_argument("--r365_summary", default=DEFAULT_R365_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
