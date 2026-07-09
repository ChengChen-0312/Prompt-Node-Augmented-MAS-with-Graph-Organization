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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r340_answer_bearing_candidate_generator_design_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r340_answer_bearing_candidate_generator_design_report.md"


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


def _family(family_id: str, role: str, trigger: str, output_contract: str) -> Dict[str, str]:
    return {
        "id": family_id,
        "role": role,
        "trigger": trigger,
        "output_contract": output_contract,
    }


def build_generator_design() -> Dict[str, Any]:
    families: List[Dict[str, str]] = [
        _family(
            "option_by_option_symbolic_verifier",
            "General option-elimination verifier that checks each visible option against the stem.",
            "Multiple-choice STEM item with formula, numeric, set, or symbolic options.",
            "May emit candidate_label only when at least two independent option checks support the same option and no checked option contradicts it.",
        ),
        _family(
            "coordinate_geometry_verifier",
            "Coordinate transformation and geometry verifier.",
            "Visible item mentions reflection, rotation, translation, slope, distance, polygon, or coordinate pairs.",
            "Derive transformed coordinates from the stem and match against options.",
        ),
        _family(
            "algebraic_structure_verifier",
            "Finite group, vector-space, rank/nullity, polynomial, and abstract algebra verifier.",
            "Visible item mentions group, field, vector space, transformation, null space, quotient, ring, ideal, or polynomial over finite fields.",
            "Construct minimal algebraic invariants and compare with options.",
        ),
        _family(
            "chemistry_balancer_verifier",
            "Stoichiometry, redox, and formula-balance verifier.",
            "Visible item contains chemical species, ions, reaction arrows, oxidation/reduction wording, or coefficient ratios.",
            "Balance or sanity-check the visible reaction and emit an answer only when option agreement is concrete.",
        ),
    ]
    return {
        "run_id": "R340",
        "title": "Answer-bearing candidate generator design",
        "claim_boundary": (
            "R340 designs general answer-bearing verifier families after R339 found no switch candidates. It does not "
            "use true labels, task ids, or API calls."
        ),
        "no_api": True,
        "broad_api": False,
        "candidate_generator_families": families,
        "promptnode_roles": [
            "PN_OptionSemanticConsistency",
            "PN_SymbolicVerifier",
            "PN_ToolResource",
            "PN_InstructionVerifier",
            "PN_SafetyGate",
        ],
        "promptedge_contract": {
            "read": "Read only visible stem and options.",
            "write": "Write compact derivation/evidence with no hidden labels.",
            "forward": "Forward candidate_label only if confidence and evidence-count thresholds are met.",
        },
        "lifecycle_contract": {
            "update": "update candidate evidence",
            "compress": "compress repeated derivations",
            "prune": "prune warning-only or unsupported candidates",
            "merge": "merge agreeing verifier candidates",
            "upgrade": "upgrade repeatable high-confidence verifier family",
        },
        "uses_true_answers": False,
        "uses_dataset_specific_task_rules": False,
        "preflight_authorized_next": True,
        "api_execution_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R341_answer_bearing_candidate_generator_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R340 Answer-Bearing Candidate Generator Design",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Family | Trigger | Contract |",
        "|---|---|---|",
    ]
    for family in summary["candidate_generator_families"]:
        rows.append(f"| `{family['id']}` | {family['trigger']} | {family['output_contract']} |")
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(summary_json: str = DEFAULT_SUMMARY_JSON, report_md: str = DEFAULT_REPORT_MD) -> Dict[str, Any]:
    summary = build_generator_design()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R340 answer-bearing candidate generator design.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
