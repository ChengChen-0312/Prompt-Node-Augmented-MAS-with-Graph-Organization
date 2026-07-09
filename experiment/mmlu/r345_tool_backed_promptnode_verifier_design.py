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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r345_tool_backed_promptnode_verifier_design_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r345_tool_backed_promptnode_verifier_design_report.md"


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
    node_id: str,
    trigger: str,
    evidence_contract: str,
    lifecycle: List[str],
) -> Dict[str, Any]:
    return {
        "id": node_id,
        "identity": "Tool-Resource PromptNode",
        "executor_type": "deterministic_local_tool",
        "trigger": trigger,
        "read_scope": "visible_stem_and_options_only",
        "write_scope": "candidate_label_with_machine_checkable_evidence",
        "forward_scope": "forward_only_if_exact_option_match_and_consistency_checks_pass",
        "evidence_contract": evidence_contract,
        "lifecycle": lifecycle,
    }


def build_tool_backed_design() -> Dict[str, Any]:
    nodes = [
        _node(
            "PN_CoordinateTransformer",
            "Coordinate geometry item with points, vertices, reflection, rotation, translation, or line symmetry.",
            "Parse coordinate pairs, apply the named transformation, and forward only if a transformed point exactly matches one visible option.",
            ["update_transformed_points", "compress_duplicate_points", "prune_if_parse_incomplete"],
        ),
        _node(
            "PN_FiniteAbelianGroupEnumerator",
            "Finite abelian group counting item with order, exponent/property, and answer options as small integers.",
            "Enumerate integer partitions/classification invariants under the visible constraint, then match the count to an option.",
            ["update_group_invariants", "merge_equivalent_partitions", "prune_if_order_or_constraint_missing"],
        ),
        _node(
            "PN_FiniteFieldDerivativeAnalyzer",
            "Polynomial-over-finite-field item asking derivative/nullity/range/rank dimensions.",
            "Analyze derivative coefficients modulo field characteristic and compare the resulting dimensions with each option.",
            ["update_kernel_basis", "compress_range_basis", "prune_if_field_or_degree_missing"],
        ),
        _node(
            "PN_RedoxBalanceLinearSolver",
            "Chemistry reaction item with ionic species, reaction arrow, coefficient ratios, or redox balancing.",
            "Solve element and charge conservation equations and forward only if the balanced coefficients verify exactly one option.",
            ["update_balance_equations", "compress_coefficients", "prune_if_species_parse_incomplete"],
        ),
    ]
    return {
        "run_id": "R345",
        "title": "Tool-backed PromptNode verifier design",
        "claim_boundary": (
            "R345 is a no-API design step after R343 showed prompt-only answer-bearing verifiers followed ARG errors. "
            "The new nodes are general executable PromptNodes with PromptEdge contracts, not task-specific answer patches."
        ),
        "no_api": True,
        "broad_api": False,
        "tool_backed_promptnodes": nodes,
        "promptedge_contracts": [
            "read_visible_problem_only",
            "write_machine_checkable_evidence",
            "forward_exact_single_option_match_only",
            "reject_if_unparsed_or_inconsistent",
            "reject_if_multiple_options_or_no_option_match",
            "record_tool_family_and_lifecycle_action",
        ],
        "selector_policy_change": {
            "before": "LLM verifier could emit answer-bearing candidates from prose rationale.",
            "after": "Selector may switch only when a tool-backed PromptNode forwards exact evidence through a PromptEdge contract.",
        },
        "uses_true_answers": False,
        "uses_task_ids_or_known_wrong_items": False,
        "local_preflight_authorized_next": True,
        "api_execution_authorized_next": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R346_tool_backed_promptnode_local_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R345 Tool-Backed PromptNode Verifier Design",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| PromptNode | Trigger | Evidence Contract |",
        "|---|---|---|",
    ]
    for node in summary["tool_backed_promptnodes"]:
        rows.append(f"| `{node['id']}` | {node['trigger']} | {node['evidence_contract']} |")
    rows.extend(["", "## PromptEdge Contracts", ""])
    rows.extend(f"- `{contract}`" for contract in summary["promptedge_contracts"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(summary_json: str = DEFAULT_SUMMARY_JSON, report_md: str = DEFAULT_REPORT_MD) -> Dict[str, Any]:
    summary = build_tool_backed_design()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R345 tool-backed PromptNode verifier design.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
