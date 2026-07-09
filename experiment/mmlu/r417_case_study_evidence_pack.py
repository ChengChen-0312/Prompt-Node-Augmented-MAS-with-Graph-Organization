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


DEFAULT_R413_JSONL = "experiment/mmlu/run_logs/mmlu_r413_definition_challenge_gate_api_results.jsonl"
DEFAULT_R414_SUMMARY = "experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r417_case_study_evidence_pack_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r417_case_study_evidence_pack_report.md"


GRAPH_ELEMENTS = [
    "InstructionAmbiguityVerifierPN",
    "ConceptDefinitionAnchorPN",
    "OptionSemanticConsistencyVerifierPN",
    "AdversarialVerifierPN",
    "ContradictionDetectorPN",
    "ConsensusConflictResolverPN",
    "DefinitionAnchorPromptEdge",
    "AdversarialChallengePromptEdge",
    "ConflictResolutionPromptEdge",
    "OptionBindingPromptEdge",
]


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    p = _repo_path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _find(rows: List[Dict[str, Any]], task_id: str) -> Dict[str, Any]:
    for row in rows:
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def _case_from_row(case_id: str, row: Dict[str, Any], evidence_file: str, mechanism: str, caveat: str = "") -> Dict[str, Any]:
    parsed = row.get("candidate_parsed_response") or {}
    return {
        "case_id": case_id,
        "task_id": row.get("task_id"),
        "subject": row.get("subject"),
        "mechanism": mechanism,
        "transition": {
            "arg_prediction": row.get("arg_prediction"),
            "candidate_label": row.get("candidate_label"),
            "final_prediction": row.get("final_prediction"),
            "true_answer": row.get("true_answer"),
            "arg_correct": row.get("arg_correct"),
            "candidate_correct": row.get("candidate_correct"),
            "final_correct": row.get("final_correct"),
            "gate_forward": row.get("gate_forward"),
            "gate_block_reasons": row.get("gate_block_reasons"),
        },
        "graph_elements": GRAPH_ELEMENTS,
        "node_evidence": {
            "confidence": parsed.get("confidence"),
            "node_agreement_count": parsed.get("node_agreement_count"),
            "contradiction_count": parsed.get("contradiction_count"),
            "definition_anchor_confidence": parsed.get("definition_anchor_confidence"),
            "adversarial_challenge_pass": parsed.get("adversarial_challenge_pass"),
            "nearest_distractor_margin": parsed.get("nearest_distractor_margin"),
            "rationale": parsed.get("rationale"),
            "promptnode_outputs": parsed.get("promptnode_outputs"),
        },
        "evidence_file": evidence_file,
        "caveat": caveat,
    }


def build_case_study_pack(
    r413_jsonl: str = DEFAULT_R413_JSONL,
    r414_summary: str = DEFAULT_R414_SUMMARY,
) -> Dict[str, Any]:
    rows = _load_jsonl(r413_jsonl)
    r414 = _load_json(r414_summary)
    fix_row = _find(rows, "MMLU-nonstem-moral_disputes_test-14")
    prune_row = _find(rows, "MMLU-nonstem-logical_fallacies_test-12")
    case_studies = [
        _case_from_row(
            "definition_challenge_fix",
            fix_row,
            r413_jsonl,
            "DefinitionChallenge gate forwards a candidate that fixes ARG without harm.",
        ),
        _case_from_row(
            "verifier_pruned_candidate_harm",
            prune_row,
            r413_jsonl,
            "Conflict-resolution and gate contracts block a candidate that would have harmed an already-correct ARG answer.",
            caveat=(
                "The blocked row also exposes parser/contract fragility: the raw rationale contains embedded JSON. "
                "Use this as a safety-prune case, not as a pure semantic-verifier proof."
            ),
        ),
        {
            "case_id": "gate_beats_candidate_pool",
            "task_id": "R413_aggregate",
            "subject": "logical_fallacies+moral_disputes+philosophy",
            "mechanism": "The gate improves over both ARG and the raw candidate pool by forwarding selectively.",
            "transition": {
                "arg_correct": r414.get("arg_correct"),
                "candidate_correct": r414.get("candidate_correct"),
                "hybrid_correct": r414.get("hybrid_correct"),
                "fixes": r414.get("fixes"),
                "harms": r414.get("harms"),
                "wrong_forward_count": r414.get("wrong_forward_count"),
                "pruned_candidate_harms": (r414.get("selection_contribution") or {}).get("pruned_candidate_harms"),
            },
            "graph_elements": GRAPH_ELEMENTS,
            "node_evidence": r414.get("selection_contribution"),
            "evidence_file": r414_summary,
            "caveat": "Aggregate mechanism case; use alongside task-level cases.",
        },
    ]
    return {
        "run_id": "R417",
        "title": "Case study evidence pack",
        "claim_boundary": (
            "R417 extracts reproducible case-study evidence. It supports mechanism discussion only, not new accuracy claims."
        ),
        "no_api": True,
        "broad_api": False,
        "case_studies": case_studies,
        "case_study_sections_allowed": [
            "Verifier/gate suppresses a harmful candidate",
            "Definition anchor plus adversarial edge repairs ARG",
            "Selective gate beats candidate pool",
        ],
        "lifecycle_trace_status": "partial_needs_explicit_runtime_logging",
        "missing_case_evidence": [
            "Explicit runtime logs for lifecycle update/compress/prune/merge/upgrade are still needed.",
            "A clean semantic-verifier-only suppressed-harm case should be collected if available.",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R418_lifecycle_trace_instrumentation_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R417 Case Study Evidence Pack",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
    ]
    for case in summary["case_studies"]:
        rows.extend(
            [
                f"## {case['case_id']}",
                "",
                f"- Task: `{case['task_id']}`",
                f"- Mechanism: {case['mechanism']}",
                f"- Transition: `{case['transition']}`",
                f"- Evidence file: `{case['evidence_file']}`",
                f"- Caveat: {case['caveat'] or 'none'}",
                "",
            ]
        )
    rows.extend(["## Missing Case Evidence", ""])
    rows.extend(f"- {item}" for item in summary["missing_case_evidence"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r413_jsonl: str = DEFAULT_R413_JSONL,
    r414_summary: str = DEFAULT_R414_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_case_study_pack(r413_jsonl=r413_jsonl, r414_summary=r414_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R417 case study evidence pack.")
    parser.add_argument("--r413_jsonl", default=DEFAULT_R413_JSONL)
    parser.add_argument("--r414_summary", default=DEFAULT_R414_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
