from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Sequence

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

DEFAULT_ENV_FILE = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env"
DEFAULT_MODEL = "gpt-4o-2024-08-06"
DEFAULT_COST_CAP = 0.45
FORBIDDEN_PROMPT_MARKERS = [
    "task_id",
    "true_answer",
    "gold_answer",
    "target_option_label",
    "is_correct",
    "correctness",
    "audit_label",
]


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def inspect_env_keys(lines_or_path: Sequence[str] | str) -> Dict[str, Any]:
    if isinstance(lines_or_path, str):
        with open(lines_or_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = list(lines_or_path)

    loaded_keys: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key:
            loaded_keys.append(key)

    key_set = set(loaded_keys)
    return {
        "loaded_keys": sorted(key_set),
        "has_api_key": bool(key_set.intersection({"API_KEY", "OPENAI_API_KEY"})),
        "has_base_url": "BASE_URL" in key_set,
    }


def _prompt_text(messages: Iterable[Dict[str, Any]]) -> str:
    return "\n".join(str(message.get("content", "")) for message in messages)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _scan_prompt_markers(messages: List[Dict[str, Any]]) -> List[str]:
    text = _prompt_text(messages).lower()
    return [marker for marker in FORBIDDEN_PROMPT_MARKERS if marker.lower() in text]


def audit_preflight_records(
    records: List[Dict[str, Any]],
    env_key_status: Dict[str, Any],
    required_model: str = DEFAULT_MODEL,
    cost_cap: float = DEFAULT_COST_CAP,
) -> Dict[str, Any]:
    blockers: List[str] = []
    warnings: List[str] = []
    total_cost = round(sum(float(row.get("estimated_cost") or 0.0) for row in records), 6)
    api_records = [row for row in records if row.get("api_required")]
    deterministic_records = [row for row in records if not row.get("api_required")]

    if not env_key_status.get("has_api_key"):
        blockers.append("missing_api_key")
    if not api_records:
        blockers.append("no_api_records")
    if total_cost > float(cost_cap):
        blockers.append("cost_over_cap")

    model_mismatch = [row for row in records if row.get("model") != required_model]
    if model_mismatch:
        blockers.append("model_mismatch")

    source_missing = [row for row in records if not row.get("source_available")]
    if source_missing:
        blockers.append("source_missing")

    leakage_rows = [
        row
        for row in records
        if not row.get("leakage_pass")
        or int(row.get("manifest_leakage_violations", 0)) > 0
        or int(row.get("prompt_leakage_violations", 0)) > 0
    ]
    prompt_marker_violations = []
    prompt_sha_mismatches = []
    api_missing_messages = []
    deterministic_has_messages = []
    for row in records:
        messages = list(row.get("model_visible_messages") or [])
        if row.get("api_required") and not messages:
            api_missing_messages.append(row)
        if not row.get("api_required") and messages:
            deterministic_has_messages.append(row)
        if messages:
            markers = _scan_prompt_markers(messages)
            if markers:
                prompt_marker_violations.append({"task_id": row.get("task_id"), "markers": markers})
            expected_sha = row.get("model_visible_prompt_sha256")
            actual_sha = _sha256_text(_prompt_text(messages))
            if expected_sha and expected_sha != actual_sha:
                prompt_sha_mismatches.append(row)

    if leakage_rows or prompt_marker_violations:
        blockers.append("leakage_violations")
    if api_missing_messages:
        blockers.append("api_missing_prompt_messages")
    if prompt_sha_mismatches:
        blockers.append("prompt_sha_mismatch")
    if deterministic_has_messages:
        warnings.append("deterministic_records_have_messages")

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    preflight_pass = not blockers
    return {
        "records": len(records),
        "api_required": len(api_records),
        "deterministic_records": len(deterministic_records),
        "variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in records).items())),
        "api_variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in api_records).items())),
        "estimated_cost": total_cost,
        "cost_cap": float(cost_cap),
        "env_key_status": env_key_status,
        "required_model": required_model,
        "preflight_pass": preflight_pass,
        "api_status": "authorized_tiny_diagnostic" if preflight_pass else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "source_missing": len(source_missing),
        "model_mismatch": len(model_mismatch),
        "leakage_rows": len(leakage_rows),
        "prompt_marker_violations": prompt_marker_violations,
        "prompt_sha_mismatches": len(prompt_sha_mismatches),
        "api_missing_messages": len(api_missing_messages),
    }


def run_preflight_audit(
    records_jsonl: str,
    r231_summary_json: str,
    env_file: str,
    output_json: str,
    report_md: str,
    required_model: str = DEFAULT_MODEL,
    cost_cap: float = DEFAULT_COST_CAP,
) -> Dict[str, Any]:
    records = load_jsonl(records_jsonl)
    r231_summary = load_json(r231_summary_json)
    env_status = inspect_env_keys(env_file)
    audit = audit_preflight_records(
        records,
        env_key_status=env_status,
        required_model=required_model,
        cost_cap=cost_cap,
    )
    audit.update(
        {
            "run_id": "R232",
            "title": "Tiny diagnostic preflight audit",
            "claim_boundary": "Preflight audit only; no API, no accuracy claim, and no SCI-Q2 readiness claim.",
            "no_api": True,
            "records_jsonl": records_jsonl,
            "r231_summary_json": r231_summary_json,
            "r231_reported_cost": r231_summary.get("estimated_cost"),
            "env_file": env_file,
            "env_values_logged": False,
        }
    )
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(audit))
    return audit


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R232 Tiny Diagnostic Preflight Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Result",
            "",
            f"- Preflight pass: `{summary['preflight_pass']}`",
            f"- API status: `{summary['api_status']}`",
            f"- Records: `{summary['records']}`",
            f"- API-required records: `{summary['api_required']}`",
            f"- Estimated cost: `${summary['estimated_cost']:.6f}` / cap `${summary['cost_cap']:.6f}`",
            f"- Source missing: `{summary['source_missing']}`",
            f"- Model mismatches: `{summary['model_mismatch']}`",
            f"- Leakage rows: `{summary['leakage_rows']}`",
            f"- Prompt SHA mismatches: `{summary['prompt_sha_mismatches']}`",
            f"- Env has API key: `{summary['env_key_status']['has_api_key']}`",
            f"- Env loaded key names: `{summary['env_key_status']['loaded_keys']}`",
            f"- Blockers: `{summary['blockers']}`",
            f"- Warnings: `{summary['warnings']}`",
            "",
            "## Boundary",
            "",
            "The audit records only environment key names and booleans. It does not print or store API key values, and it does not call any model.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit R231 tiny diagnostic preflight.")
    parser.add_argument("--records_jsonl", required=True)
    parser.add_argument("--r231_summary_json", required=True)
    parser.add_argument("--env_file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--report_md", required=True)
    parser.add_argument("--required_model", default=DEFAULT_MODEL)
    parser.add_argument("--cost_cap", type=float, default=DEFAULT_COST_CAP)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_preflight_audit(
        records_jsonl=args.records_jsonl,
        r231_summary_json=args.r231_summary_json,
        env_file=args.env_file,
        output_json=args.output_json,
        report_md=args.report_md,
        required_model=args.required_model,
        cost_cap=args.cost_cap,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
