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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r351_fresh_coverage_promptnode_expansion_design_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r351_fresh_coverage_promptnode_expansion_design_report.md"


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


def _node(node_id: str, identity: str, trigger: str, evidence_contract: str, answer_bearing: bool) -> Dict[str, Any]:
    return {
        "id": node_id,
        "identity": identity,
        "trigger": trigger,
        "evidence_contract": evidence_contract,
        "answer_bearing_allowed": answer_bearing,
        "read_scope": "visible_stem_and_options_only",
        "write_scope": "structured_evidence_and_candidate_when_contract_passes",
        "lifecycle": ["update", "compress", "prune", "merge", "upgrade"],
    }


def build_coverage_expansion_design() -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = [
        _node(
            "PN_NumericWordProblemSolver",
            "Tool-Resource PromptNode",
            "Arithmetic, counting, probability, combinatorics, divisibility, and simple equation word problems.",
            "Build a small symbolic/numeric model from visible quantities and match exactly one option.",
            True,
        ),
        _node(
            "PN_PhysicsFormulaEvaluator",
            "Tool-Resource PromptNode",
            "Capacitor energy, friction stopping distance, idealized kinematics, mole/pressure ratios, and common formula substitution tasks.",
            "Select and execute a named formula only when all variables are visible and exactly one option matches.",
            True,
        ),
        _node(
            "PN_ChemistryConceptAndStoichiometryTool",
            "Tool-Resource PromptNode",
            "Element symbols, mole fractions, periodic-table facts, reaction balancing, and electron-configuration concepts.",
            "Forward only when a deterministic lookup, mole computation, or conservation equation verifies one option.",
            True,
        ),
        _node(
            "PN_PassageEntailmentVerifier",
            "Verifier PromptNode",
            "History, law, or ethics items with an explicit quoted passage or case facts.",
            "Use only passage/fact entailment; forward only if the option is directly supported and alternatives contradict the visible text.",
            True,
        ),
        _node(
            "PN_DefinitionFallacyVerifier",
            "Memory/Verifier PromptNode",
            "Definition-heavy items about fallacies, named theories, rules, or canonical terms.",
            "Use a compact curated definition table; forward only on exact definition match, otherwise write warning-only evidence.",
            True,
        ),
        _node(
            "PN_ClozeSemanticConsistencyVerifier",
            "Verifier PromptNode",
            "Fill-in-the-blank and option semantic consistency tasks.",
            "Check grammatical and semantic consistency across all blanks; forward only when one option satisfies every slot.",
            True,
        ),
        _node(
            "PN_ConsensusConflictResolver",
            "Agent-like PromptNode",
            "Any item where tool and ARG disagree or several PromptNodes produce competing candidates.",
            "Default to KEEP_ARG unless a candidate has machine/textual evidence and no unresolved contradiction.",
            False,
        ),
    ]
    return {
        "run_id": "R351",
        "title": "Fresh coverage PromptNode expansion design",
        "claim_boundary": (
            "R351 expands PromptNode coverage after R349 showed zero fresh coverage. The R349 split is now treated "
            "as a coverage-development set, not as a main-claim evaluation set."
        ),
        "no_api": True,
        "broad_api": False,
        "r349_reclassified_as_coverage_dev_set": True,
        "uses_r349_for_main_claim": False,
        "expanded_promptnodes": nodes,
        "promptedge_contracts": [
            "read_visible_problem_only",
            "write_structured_evidence",
            "forward_exact_single_option_match_only",
            "reject_if_no_machine_or_textual_evidence",
            "reject_if_multiple_or_conflicting_candidates",
            "record_lifecycle_action_and_evidence_source",
        ],
        "coverage_targets": {
            "stem_numeric_or_formula": "increase deterministic local coverage",
            "nonstem_semantic": "add evidence-writing and guarded answer-bearing coverage",
            "fresh_formal_eval": "must use a later split excluding R349/R352 development tasks",
        },
        "target_min_forwarded_candidates_next": 8,
        "api_execution_authorized_next": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R352_fresh_coverage_promptnode_expansion_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R351 Fresh Coverage PromptNode Expansion Design",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| PromptNode | Trigger | Evidence Contract |",
        "|---|---|---|",
    ]
    for node in summary["expanded_promptnodes"]:
        rows.append(f"| `{node['id']}` | {node['trigger']} | {node['evidence_contract']} |")
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(summary_json: str = DEFAULT_SUMMARY_JSON, report_md: str = DEFAULT_REPORT_MD) -> Dict[str, Any]:
    summary = build_coverage_expansion_design()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R351 fresh coverage PromptNode expansion design.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
