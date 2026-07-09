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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r470_current_status_digest_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r470_current_status_digest_report.md"
DEFAULT_DIGEST_MD = "paper/artifacts/current_status_digest.md"


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


def render_digest(summary: Dict[str, Any]) -> str:
    rows = [
        "# Current Status Digest",
        "",
        "## Main Evidence",
        "",
        "- AQuA audit-clean: 31/31 vs 28/31.",
        "- AQuA conservative remove-task114: 30/30 vs 28/30.",
        "- MMLU STEM: 95/97 vs 88/97 with fix/harm 7/0.",
        "- Mixed non-STEM: 41/48 vs 41/48, no broad positive claim.",
        "- DefinitionChallenge: 22/24 vs 21/24 with fix/harm/wrong-forward 1/0/0.",
        "",
        "## Locally Ready",
        "",
    ]
    rows.extend(f"- {item}" for item in summary["local_ready_items"])
    rows.extend(["", "## Still Blocked", ""])
    rows.extend(f"- {item}" for item in summary["blocked_items"])
    rows.extend(
        [
            "",
            "Bottom line: local manuscript artifacts are organized, but external audits pending, official JCR verification pending, and PDF compilation pending.",
            "",
        ]
    )
    return "\n".join(rows)


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R470 Current Status Digest",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Digest: `{summary['digest_md']}`",
        f"- Local artifacts ready: `{summary['local_artifacts_ready']}`",
        "",
        f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
        f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run_digest(
    digest_md: str = DEFAULT_DIGEST_MD,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    r468 = _load_json("experiment/mmlu/res_logs/mmlu_r468_submission_readiness_matrix_summary.json")
    matrix = r468.get("readiness_matrix", {})
    local_ready = [name for name, item in matrix.items() if item.get("status") == "ready_local"]
    blocked = [name.replace("_", " ") + " pending" for name, item in matrix.items() if item.get("status") == "blocked"]
    summary: Dict[str, Any] = {
        "run_id": "R470",
        "title": "Current status digest",
        "claim_boundary": (
            "R470 writes a concise status digest from existing evidence and readiness files. "
            "It does not add experiments or authorize submission claims."
        ),
        "no_api": True,
        "broad_api": False,
        "digest_md": digest_md,
        "local_ready_items": local_ready,
        "blocked_items": blocked,
        "local_artifacts_ready": bool(local_ready) and "external audits pending" in blocked,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R471_five_run_goal_audit_after_readiness_planning",
    }
    _write_text(digest_md, render_digest(summary))
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write concise current-status digest.")
    parser.add_argument("--digest_md", default=DEFAULT_DIGEST_MD)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_digest(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
