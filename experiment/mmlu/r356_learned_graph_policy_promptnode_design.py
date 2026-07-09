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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r356_learned_graph_policy_promptnode_design_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r356_learned_graph_policy_promptnode_design_report.md"


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


def build_learned_policy_design() -> Dict[str, Any]:
    return {
        "run_id": "R356",
        "title": "Learned graph-policy PromptNode design",
        "claim_boundary": (
            "R356 redirects from hand-written template expansion to a learned graph policy. The policy treats "
            "PromptNodes and PromptEdges as first-class graph actions and requires a fresh evaluation after training."
        ),
        "no_api": True,
        "broad_api": False,
        "policy_type": "learned_graph_policy",
        "uses_promptnode_as_first_class_graph_object": True,
        "graph_actions": [
            "KEEP_ARG",
            "ADD_PROMPT_NODE",
            "ADD_PROMPT_EDGE",
            "UPDATE_PROMPT_NODE",
            "MERGE_PROMPT_NODES",
            "PRUNE_PROMPT_NODE",
            "FORWARD_CANDIDATE",
        ],
        "promptnode_families": [
            "MemoryBridge",
            "InstructionAmbiguityVerifier",
            "OptionSemanticConsistencyVerifier",
            "ContradictionDetector",
            "ToolResourceVerifier",
            "PassageEntailmentVerifier",
            "DefinitionFallacyVerifier",
            "ConsensusConflictResolver",
            "SafetyGate",
        ],
        "promptedge_types": [
            "read_visible_problem",
            "write_structured_evidence",
            "forward_candidate_if_contract_passes",
            "block_forward_if_warning_only",
            "merge_agreeing_evidence",
        ],
        "feature_groups": [
            "dataset_family_subject_and_question_shape",
            "option_format_numeric_symbolic_semantic_passage",
            "baseline_confidence_and_requery_disagreement",
            "candidate_evidence_type_and_contract_pass",
            "lifecycle_state_update_compress_prune_merge_upgrade",
        ],
        "training_sources": ["R322", "R325", "R327", "R329", "R347", "R352"],
        "negative_control_sources": ["R316", "R324", "R354"],
        "target_labels": {
            "add_node": "which PromptNode family should be instantiated",
            "add_edge": "which read/write/forward PromptEdge contract should connect nodes",
            "forward": "whether candidate evidence is allowed to override ARG",
            "prune": "whether a warning-only or unsupported node should be removed",
        },
        "model_candidates": [
            "logistic_regression_or_linear_svm_for_transparency",
            "gradient_boosted_trees_for_feature_interactions",
            "small_mlp_optional_if_data_grows",
        ],
        "requires_fresh_eval_after_training": True,
        "api_execution_authorized_next": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R357_learned_graph_policy_training_manifest",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R356 Learned Graph-Policy PromptNode Design",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Policy type: `{summary['policy_type']}`",
        "",
        "## Graph Actions",
        "",
    ]
    rows.extend(f"- `{action}`" for action in summary["graph_actions"])
    rows.extend(["", "## PromptNode Families", ""])
    rows.extend(f"- `{family}`" for family in summary["promptnode_families"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(summary_json: str = DEFAULT_SUMMARY_JSON, report_md: str = DEFAULT_REPORT_MD) -> Dict[str, Any]:
    summary = build_learned_policy_design()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R356 learned graph-policy PromptNode design.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
