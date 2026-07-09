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


DEFAULT_R402_SUMMARY = "experiment/mmlu/res_logs/mmlu_r402_result_to_claim_synthesis_for_paper_summary.json"
DEFAULT_R414_SUMMARY = "experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json"
DEFAULT_PAPER_PLAN = "PAPER_PLAN.md"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r415_update_claim_matrix_after_nonmath_positive_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r415_update_claim_matrix_after_nonmath_positive_report.md"
SECTION_TITLE = "## R415 Nonmath Positive Claim Update"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _replace_or_append_section(text: str, block: str) -> str:
    if SECTION_TITLE not in text:
        return text.rstrip() + "\n\n" + block
    prefix, rest = text.split(SECTION_TITLE, 1)
    next_marker = "\n## "
    if next_marker in rest:
        _, suffix = rest.split(next_marker, 1)
        return prefix.rstrip() + "\n\n" + block.rstrip() + "\n\n## " + suffix.lstrip()
    return prefix.rstrip() + "\n\n" + block


def _new_claim(r414: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": "C6_definition_challenge_fresh_positive",
        "status": "supported_narrow",
        "paper_use": "targeted_nonmath_transfer_result_or_appendix",
        "evidence": (
            f"Fresh DefinitionChallenge split: ARG {r414.get('arg_correct')}/{r414.get('records')} "
            f"vs DefinitionChallenge {r414.get('hybrid_correct')}/{r414.get('records')}; "
            f"candidate pool {r414.get('candidate_correct')}/{r414.get('records')}; "
            f"fix/harm/wrong-forward {r414.get('fixes')}/{r414.get('harms')}/{r414.get('wrong_forward_count')}."
        ),
        "source": DEFAULT_R414_SUMMARY,
    }


def _render_update_block(summary: Dict[str, Any]) -> str:
    rows = [
        SECTION_TITLE,
        "",
        "**Verdict**: `partial+` support for a narrowed SCI-Q2 paper claim after a fresh targeted nonmath result.",
        "",
        "| Claim ID | Status | Paper Use | Evidence |",
        "|---|---|---|---|",
    ]
    for claim in summary["claims"]:
        rows.append(
            f"| `{claim['id']}` | `{claim['status']}` | `{claim['paper_use']}` | {claim['evidence']} |"
        )
    rows.extend(
        [
            "",
            "**Updated allowed framing**:",
            "",
            summary["suggested_claim_revision"],
            "",
            "**Still forbidden**:",
            "",
            "- Do not claim broad nonmath or universal multiple-choice improvement.",
            "- Do not treat the same-split R411 gate ablation as evidence.",
            "- Do not treat the targeted DefinitionChallenge result as a substitute for independent integrity audit.",
            "",
            "**Remaining gaps before submission freeze**:",
            "",
        ]
    )
    rows.extend(f"- {item}" for item in summary["missing_evidence"])
    return "\n".join(rows).strip() + "\n"


def build_claim_update(
    r402_summary: str = DEFAULT_R402_SUMMARY,
    r414_summary: str = DEFAULT_R414_SUMMARY,
) -> Dict[str, Any]:
    r402 = _load_json(r402_summary)
    r414 = _load_json(r414_summary)
    old_claims: List[Dict[str, Any]] = list(r402.get("claims", []))
    claims = old_claims + [_new_claim(r414)]
    return {
        "run_id": "R415",
        "title": "Update claim matrix after nonmath positive result",
        "claim_boundary": (
            "R415 adds R414 as a narrow targeted nonmath positive result. It keeps broad nonmath improvement forbidden."
        ),
        "no_api": True,
        "broad_api": False,
        "skill_used": "result-to-claim",
        "claims": claims,
        "supported_claim_ids": [claim["id"] for claim in claims if claim["status"] in {"supported", "supported_narrow"}],
        "partial_claim_ids": [claim["id"] for claim in claims if claim["status"] == "partial"],
        "unsupported_claim_ids": [claim["id"] for claim in claims if claim["status"] == "unsupported"],
        "suggested_claim_revision": (
            "PromptNode/PromptEdge graph organization improves audited AQuA and MMLU STEM under ARG-Designer-matched "
            "settings, and a targeted DefinitionChallenge PromptNode/PromptEdge gate gives a fresh positive no-harm "
            "result on concept-definition nonmath transfer. Broader nonmath improvement remains unclaimed."
        ),
        "missing_evidence": [
            "Independent experiment integrity audit before paper claim authorization.",
            "Cost-normalized table that includes R065, R306, R413, and plain-requery controls.",
            "A larger nonmath split is still needed before claiming broad nonmath transfer.",
            "Final paper figures/tables updated with exact claim boundaries.",
        ],
        "claim_permissions": {
            "aqua_clean_improvement_claim_allowed": True,
            "mmlu_stem_improvement_claim_allowed": True,
            "mixed_nonmath_no_harm_claim_allowed": True,
            "narrow_definition_challenge_claim_allowed": True,
            "broad_nonmath_claim_allowed": False,
            "broad_general_improvement_claim_allowed": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_plan_update_authorized": True,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R416_cost_normalized_claim_table_and_goal_audit",
    }


def run(
    r402_summary: str = DEFAULT_R402_SUMMARY,
    r414_summary: str = DEFAULT_R414_SUMMARY,
    paper_plan: str = DEFAULT_PAPER_PLAN,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_claim_update(r402_summary=r402_summary, r414_summary=r414_summary)
    block = _render_update_block(summary)
    plan_path = _repo_path(paper_plan)
    original = plan_path.read_text(encoding="utf-8") if plan_path.exists() else "# Paper Plan\n"
    updated = _replace_or_append_section(original, block)
    plan_path.write_text(updated, encoding="utf-8")
    summary.update({"paper_plan": paper_plan, "summary_json": summary_json, "report_md": report_md, "paper_plan_updated": True})
    _write_json(summary_json, summary)
    _write_text(report_md, block)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update claim matrix after R414 nonmath positive result.")
    parser.add_argument("--r402_summary", default=DEFAULT_R402_SUMMARY)
    parser.add_argument("--r414_summary", default=DEFAULT_R414_SUMMARY)
    parser.add_argument("--paper_plan", default=DEFAULT_PAPER_PLAN)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
