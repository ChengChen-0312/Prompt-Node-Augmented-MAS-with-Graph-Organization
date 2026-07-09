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


DEFAULT_R306_JSONL = "experiment/mmlu/run_logs/mmlu_r306_nonmath_stack_eval_results.jsonl"
DEFAULT_R306_SUMMARY = "experiment/mmlu/res_logs/mmlu_r306_nonmath_stack_eval_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r422_mmlu_stem_cost_reconstruction_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r422_mmlu_stem_cost_reconstruction_preflight_report.md"


TOKEN_KEYS = {"prompt_tokens", "completion_tokens", "total_tokens", "api_cost", "cost"}
MESSAGE_KEYS = {"model_visible_messages", "messages", "prompt_messages"}


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


def build_cost_reconstruction_preflight(
    r306_jsonl: str = DEFAULT_R306_JSONL,
    r306_summary: str = DEFAULT_R306_SUMMARY,
) -> Dict[str, Any]:
    rows = _load_jsonl(r306_jsonl)
    summary = _load_json(r306_summary)
    all_keys = set().union(*(row.keys() for row in rows)) if rows else set()
    token_fields = sorted(all_keys & TOKEN_KEYS)
    message_fields = sorted(all_keys & MESSAGE_KEYS)
    exact_possible = bool(token_fields and ("api_cost" in token_fields or {"prompt_tokens", "completion_tokens"} <= set(token_fields)))
    approximate_possible = bool(rows and "question" in all_keys and "raw_answer" in all_keys)
    return {
        "run_id": "R422",
        "title": "MMLU STEM cost reconstruction preflight",
        "claim_boundary": (
            "R422 checks whether exact MMLU STEM cost can be reconstructed from existing logs. It does not estimate "
            "submission costs as evidence."
        ),
        "no_api": True,
        "broad_api": False,
        "source_jsonl": r306_jsonl,
        "source_summary": r306_summary,
        "source_results_found": bool(rows and summary),
        "source_records": len(rows),
        "summary_main_score": f"{summary.get('main_correct')}/{summary.get('main_records')}" if summary else "missing",
        "token_fields_found": bool(token_fields),
        "token_fields": token_fields,
        "message_fields_found": bool(message_fields),
        "message_fields": message_fields,
        "exact_cost_reconstruction_possible": exact_possible,
        "approximate_cost_estimate_possible": approximate_possible,
        "approximate_cost_allowed_for_submission": False,
        "cost_probe_authorized_next": bool(rows and not exact_possible),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R423_mmlu_stem_cost_probe_manifest",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R422 MMLU STEM Cost Reconstruction Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Source found/records: `{summary['source_results_found']}/{summary['source_records']}`",
            f"- Summary main score: `{summary['summary_main_score']}`",
            f"- Token fields found: `{summary['token_fields_found']}` `{summary['token_fields']}`",
            f"- Message fields found: `{summary['message_fields_found']}` `{summary['message_fields']}`",
            f"- Exact reconstruction possible: `{summary['exact_cost_reconstruction_possible']}`",
            f"- Cost probe authorized next: `{summary['cost_probe_authorized_next']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r306_jsonl: str = DEFAULT_R306_JSONL,
    r306_summary: str = DEFAULT_R306_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_cost_reconstruction_preflight(r306_jsonl=r306_jsonl, r306_summary=r306_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether R306 MMLU STEM cost can be reconstructed exactly.")
    parser.add_argument("--r306_jsonl", default=DEFAULT_R306_JSONL)
    parser.add_argument("--r306_summary", default=DEFAULT_R306_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
