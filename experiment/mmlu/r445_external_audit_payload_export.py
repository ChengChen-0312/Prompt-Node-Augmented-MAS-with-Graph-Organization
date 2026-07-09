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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r445_external_audit_payload_export_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r445_external_audit_payload_export_report.md"

PAYLOAD_PATHS = {
    "experiment_integrity_audit": "experiment/mmlu/run_logs/mmlu_r445_experiment_integrity_external_payload.md",
    "paper_claim_audit": "experiment/mmlu/run_logs/mmlu_r445_paper_claim_external_payload.md",
    "citation_context_audit": "experiment/mmlu/run_logs/mmlu_r445_citation_context_external_payload.md",
}


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    target = _repo_path(path)
    return json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _read_text_file(path: str) -> str:
    target = _repo_path(path)
    return target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""


def _payload_markdown(name: str, plan: Dict[str, Any]) -> str:
    prompt = _read_text_file(plan["prompt_md"])
    rows = [
        f"# R445 External Audit Payload: {name}",
        "",
        "This payload is prepared for a fresh external reviewer. It has not been submitted by Codex.",
        "",
        "## Audit Prompt",
        "",
        prompt,
        "",
        "## Attached File Contents",
        "",
    ]
    for path in plan.get("files", []):
        text = _read_text_file(path)
        suffix = Path(path).suffix.lstrip(".") or "text"
        rows.extend(
            [
                f"### `{path}`",
                "",
                f"```{suffix}",
                text,
                "```",
                "",
            ]
        )
    return "\n".join(rows)


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R445 External Audit Payload Export",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Payloads",
        "",
    ]
    rows.extend(f"- `{item['audit_name']}`: `{item['payload_md']}`" for item in summary["payloads_created"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_export(
    r444_summary: str = "experiment/mmlu/res_logs/mmlu_r444_external_audit_execution_plan_summary.json",
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    r444 = _load_json(r444_summary)
    plan = r444.get("audit_execution_plan", {})
    created: List[Dict[str, Any]] = []
    for name in r444.get("execution_order", []):
        payload_path = PAYLOAD_PATHS[name]
        text = _payload_markdown(name, plan[name])
        _write_text(payload_path, text)
        created.append(
            {
                "audit_name": name,
                "payload_md": payload_path,
                "bytes": _repo_path(payload_path).stat().st_size,
                "expected_review_output_md": plan[name]["expected_output_md"],
            }
        )

    summary: Dict[str, Any] = {
        "run_id": "R445",
        "title": "External audit payload export",
        "claim_boundary": (
            "R445 prepares local external-audit payloads. It does not transmit manuscript or result files "
            "to a browser, API, or reviewer."
        ),
        "no_api": True,
        "broad_api": False,
        "payloads_created": created,
        "external_reviews_executed": [],
        "browser_submission_performed": False,
        "requires_confirmation_before_transmission": True,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R446_local_tables_and_submission_gaps",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export local payloads for external audits.")
    parser.add_argument("--r444_summary", default="experiment/mmlu/res_logs/mmlu_r444_external_audit_execution_plan_summary.json")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_export(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
