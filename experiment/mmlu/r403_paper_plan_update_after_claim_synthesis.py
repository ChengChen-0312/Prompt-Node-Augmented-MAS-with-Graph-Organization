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


DEFAULT_R402_SUMMARY = "experiment/mmlu/res_logs/mmlu_r402_result_to_claim_synthesis_for_paper_summary.json"
DEFAULT_PAPER_PLAN = "PAPER_PLAN.md"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r403_paper_plan_update_after_claim_synthesis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r403_paper_plan_update_after_claim_synthesis_report.md"
SECTION_TITLE = "## R402 Claim Synthesis Update"


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


def _render_update_block(r402: Dict[str, Any]) -> str:
    rows = [
        SECTION_TITLE,
        "",
        f"**Verdict**: `{r402.get('overall_claim_supported', 'partial')}` support for a narrowed SCI-Q2 paper claim.",
        "",
        "| Claim ID | Status | Paper Use | Evidence |",
        "|---|---|---|---|",
    ]
    for claim in r402.get("claims", []):
        rows.append(
            f"| `{claim['id']}` | `{claim['status']}` | `{claim['paper_use']}` | {claim['evidence']} |"
        )
    rows.extend(
        [
            "",
            "**Allowed main text framing**:",
            "",
            r402.get("suggested_claim_revision", ""),
            "",
            "**Forbidden framing**:",
            "",
            "- Do not claim broad general improvement across all nonmath/multiple-choice tasks.",
            "- Do not treat the R380 history pilot as a main transfer result.",
            "- Do not integrate the failed R400 contrastive branch.",
            "",
            "**Missing before submission freeze**:",
            "",
        ]
    )
    rows.extend(f"- {item}" for item in r402.get("missing_evidence", []))
    return "\n".join(rows).strip() + "\n"


def _replace_or_append_section(text: str, block: str) -> str:
    if SECTION_TITLE not in text:
        return text.rstrip() + "\n\n" + block
    prefix, rest = text.split(SECTION_TITLE, 1)
    next_marker = "\n## "
    if next_marker in rest:
        _, suffix = rest.split(next_marker, 1)
        return prefix.rstrip() + "\n\n" + block.rstrip() + "\n\n## " + suffix.lstrip()
    return prefix.rstrip() + "\n\n" + block


def build_plan_update(r402_summary: str = DEFAULT_R402_SUMMARY) -> Dict[str, Any]:
    r402 = _load_json(r402_summary)
    block = _render_update_block(r402)
    claim_ids = [claim.get("id") for claim in r402.get("claims", [])]
    return {
        "run_id": "R403",
        "title": "Paper plan update after claim synthesis",
        "claim_boundary": "R403 writes R402's narrowed claim boundary into PAPER_PLAN.md.",
        "no_api": True,
        "broad_api": False,
        "claim_ids": claim_ids,
        "update_block": block,
        "claim_permissions": r402.get("claim_permissions", {}),
        "paper_plan_update_authorized": True,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R404_integrity_audit_preflight",
    }


def run(
    r402_summary: str = DEFAULT_R402_SUMMARY,
    paper_plan: str = DEFAULT_PAPER_PLAN,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_plan_update(r402_summary=r402_summary)
    plan_path = _repo_path(paper_plan)
    original = plan_path.read_text(encoding="utf-8") if plan_path.exists() else "# Paper Plan\n"
    updated = _replace_or_append_section(original, summary["update_block"])
    plan_path.write_text(updated, encoding="utf-8")
    summary.update({"paper_plan": paper_plan, "summary_json": summary_json, "report_md": report_md, "paper_plan_updated": True})
    _write_json(summary_json, summary)
    _write_text(report_md, summary["update_block"])
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update PAPER_PLAN.md after R402 claim synthesis.")
    parser.add_argument("--r402_summary", default=DEFAULT_R402_SUMMARY)
    parser.add_argument("--paper_plan", default=DEFAULT_PAPER_PLAN)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
