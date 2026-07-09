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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r407_nonmath_promptnode_curriculum_design_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r407_nonmath_promptnode_curriculum_design_report.md"


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


def _node(
    node_type: str,
    identity: str,
    purpose: str,
    outputs: List[str],
    insert_positions: List[str],
    lifecycle: List[str],
) -> Dict[str, Any]:
    return {
        "type": node_type,
        "identity": identity,
        "purpose": purpose,
        "outputs": outputs,
        "insert_positions": insert_positions,
        "permissions": ["read", "write"],
        "lifecycle": lifecycle,
    }


def _edge(edge_type: str, source: str, target: str, contract: str) -> Dict[str, Any]:
    return {
        "type": edge_type,
        "source": source,
        "target": target,
        "prompt_as_edge": True,
        "permissions": ["read", "write", "forward"],
        "contract": contract,
    }


def build_curriculum_design() -> Dict[str, Any]:
    promptnodes = [
        _node(
            "InstructionAmbiguityVerifierPN",
            "Instruction-Verifier",
            "Extracts the operative instruction, scope words, negation, EXCEPT/NOT clauses, and required answer granularity.",
            ["instruction_operator", "scope_term", "ambiguity_flag", "abstain_reason"],
            ["source-consumer", "group boundary"],
            ["update", "compress", "prune"],
        ),
        _node(
            "OptionSemanticConsistencyVerifierPN",
            "Instruction-Verifier",
            "Checks whether each option semantically satisfies the extracted instruction instead of only sounding plausible.",
            ["candidate_label", "option_semantic_match", "nearest_distractor", "evidence_count"],
            ["conflict center", "aggregator pre-checkpoint"],
            ["update", "compress", "upgrade"],
        ),
        _node(
            "ConceptDefinitionAnchorPN",
            "Memory",
            "Creates a compact local definition anchor for philosophy, moral, logic, religion, and social-science terms.",
            ["key_concept", "definition_anchor", "distractor_boundary", "definition_confidence"],
            ["source-consumer", "conflict center"],
            ["write", "compress", "merge", "prune"],
        ),
        _node(
            "ContradictionDetectorPN",
            "Verifier",
            "Detects when a candidate rationale contradicts the option text, the stem operator, or another node's evidence.",
            ["contradiction_count", "contradicted_node", "contradiction_reason", "hard_veto"],
            ["conflict center", "aggregator pre-checkpoint"],
            ["update", "prune", "upgrade"],
        ),
        _node(
            "AdversarialVerifierPN",
            "Agent-like",
            "Attempts to falsify the leading candidate by defending the nearest distractor before the graph forwards an answer.",
            ["challenge_pass", "challenger_label", "rejection_reason", "candidate_survives"],
            ["conflict center", "aggregator pre-checkpoint"],
            ["update", "merge", "upgrade"],
        ),
        _node(
            "ConsensusConflictResolverPN",
            "Agent-like",
            "Aggregates node evidence and forwards only when support, contradiction, and ambiguity contracts are jointly satisfied.",
            ["forward_label", "node_agreement_count", "node_disagreement_count", "forward_decision"],
            ["aggregator pre-checkpoint"],
            ["update", "compress", "prune", "upgrade"],
        ),
        _node(
            "MemoryBridgePN",
            "Memory",
            "Carries a compressed task-intent and definition bridge from early verifiers to late option-binding and resolver nodes.",
            ["bridge_summary", "reusable_evidence", "write_confidence", "staleness_flag"],
            ["source-consumer", "group boundary", "aggregator pre-checkpoint"],
            ["write", "compress", "merge", "prune"],
        ),
    ]
    promptedges = [
        _edge(
            "OptionBindingPromptEdge",
            "OptionSemanticConsistencyVerifierPN",
            "ConsensusConflictResolverPN",
            "Bind exactly one visible option label only when the rationale directly supports that option text.",
        ),
        _edge(
            "AdversarialChallengePromptEdge",
            "AdversarialVerifierPN",
            "ConsensusConflictResolverPN",
            "Forward the candidate only if the adversarial challenge fails to support the nearest distractor.",
        ),
        _edge(
            "DefinitionAnchorPromptEdge",
            "ConceptDefinitionAnchorPN",
            "OptionSemanticConsistencyVerifierPN",
            "Every option judgment must cite or reject the local definition anchor; otherwise mark evidence weak.",
        ),
        _edge(
            "ConflictResolutionPromptEdge",
            "ContradictionDetectorPN",
            "ConsensusConflictResolverPN",
            "A hard contradiction veto blocks forwarding; a soft contradiction increases the learned gate penalty.",
        ),
        _edge(
            "MemoryBridgePromptEdge",
            "MemoryBridgePN",
            "ConsensusConflictResolverPN",
            "Read the compressed task intent and definition bridge, but never treat it as ground truth.",
        ),
    ]
    training_features = [
        "candidate_confidence",
        "candidate_evidence_count",
        "candidate_type",
        "subject_family",
        "node_agreement_count",
        "node_disagreement_count",
        "contradiction_count",
        "ambiguity_flag",
        "definition_anchor_confidence",
        "adversarial_challenge_pass",
        "nearest_distractor_margin",
        "option_binding_contract_pass",
        "memory_bridge_write_confidence",
        "lifecycle_update_count",
        "lifecycle_prune_count",
    ]
    return {
        "run_id": "R407",
        "title": "Nonmath PromptNode curriculum design",
        "claim_boundary": (
            "R407 designs a general nonmath PromptNode/PromptEdge curriculum. It is design/preflight only; "
            "it cannot support a paper result until fresh execution and learned-gate analysis pass."
        ),
        "no_api": True,
        "broad_api": False,
        "math_patch_only": False,
        "promptnodes": promptnodes,
        "promptedges": promptedges,
        "training_plan": {
            "policy": "two_stage_candidate_then_learned_forward_gate",
            "stage_1": "Generate structured evidence from multiple nonmath PromptNodes without exposing labels.",
            "stage_2": "Train a conservative forward gate from model-visible graph features and hard negatives.",
            "features": training_features,
            "target": "forward candidate iff it fixes ARG or preserves an already correct ARG answer without wrong-forward.",
            "hard_negative_wrong_forward_weight": 4.0,
            "positive_fix_weight": 2.0,
            "forbidden_signals": ["true_answer", "task_id", "row_index", "source_ref_hash", "posthoc_correctness"],
            "minimum_success_criteria": {
                "fresh_split_delta_correct": ">= +1",
                "fresh_split_harms": 0,
                "fresh_split_wrong_forward": "<= 1",
                "plain_requery_control_required": True,
            },
        },
        "failure_modes_addressed": {
            "wrong_forward_definition_misbinding": ["ConceptDefinitionAnchorPN", "ContradictionDetectorPN", "AdversarialVerifierPN"],
            "candidate_quality_failure": ["OptionSemanticConsistencyVerifierPN", "AdversarialVerifierPN"],
            "gate_over_pruning_for_option_candidate": ["ConsensusConflictResolverPN", "node_agreement_count", "nearest_distractor_margin"],
            "abstention_or_schema_failure": ["InstructionAmbiguityVerifierPN", "MemoryBridgePN"],
        },
        "api_execution_authorized_next": True,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R408_nonmath_curriculum_fresh_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R407 Nonmath PromptNode Curriculum Design",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- PromptNodes: `{len(summary['promptnodes'])}`",
        f"- PromptEdges: `{len(summary['promptedges'])}`",
        f"- Training policy: `{summary['training_plan']['policy']}`",
        f"- Math patch only: `{summary['math_patch_only']}`",
        "",
        "## PromptNodes",
        "",
    ]
    rows.extend(f"- `{node['type']}`: {node['purpose']}" for node in summary["promptnodes"])
    rows.extend(["", "## PromptEdges", ""])
    rows.extend(f"- `{edge['type']}`: {edge['contract']}" for edge in summary["promptedges"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_curriculum_design()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Design nonmath PromptNode curriculum.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
