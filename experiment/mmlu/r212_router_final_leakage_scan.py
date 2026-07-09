from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from typing import Any, Dict, List


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def scan_manifest(path: str) -> Dict[str, Any]:
    rows = load_jsonl(path)
    missing_schema = 0
    violations: List[Dict[str, Any]] = []
    schema_versions: Counter[str] = Counter()
    router_actions: Counter[str] = Counter()
    target_labels: Counter[str] = Counter()

    for idx, row in enumerate(rows):
        schema = row.get("router_final_schema")
        if not isinstance(schema, dict):
            missing_schema += 1
            continue

        schema_versions[str(schema.get("schema_version", ""))] += 1
        router_actions[str(schema.get("router_action", ""))] += 1
        target_labels[str(schema.get("target_option_label", ""))] += 1

        model_visible = set(schema.get("model_visible_fields", []))
        forbidden = set(schema.get("forbidden_model_visible_fields", []))
        overlap = sorted(model_visible & forbidden)
        if overlap:
            violations.append(
                {
                    "row_index": idx,
                    "reason": "model_visible_forbidden_intersection",
                    "fields": overlap,
                }
            )
        if schema.get("gold_answer_used") is not False:
            violations.append(
                {
                    "row_index": idx,
                    "reason": "gold_answer_used_not_false",
                    "value": schema.get("gold_answer_used"),
                }
            )

    action_counts = dict(sorted(router_actions.items()))
    summary = {
        "rows": len(rows),
        "manifest": path,
        "missing_schema": missing_schema,
        "schema_versions": dict(sorted(schema_versions.items())),
        "router_actions": action_counts,
        "target_option_labels": dict(sorted(target_labels.items())),
        "abstain_only": action_counts == {"abstain": len(rows)} if rows else False,
        "schema_pass": missing_schema == 0,
        "leakage_violations": len(violations),
        "leakage_pass": len(violations) == 0,
        "violations": violations,
    }
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R212 Router-Final Leakage Scan",
            "",
            "**Claim boundary**: leakage scan only. No API evaluation and no accuracy claim.",
            "",
            "## Result",
            "",
            f"- Manifest: `{summary['manifest']}`",
            f"- Rows: `{summary['rows']}`",
            f"- Missing schema: `{summary['missing_schema']}`",
            f"- Schema pass: `{summary['schema_pass']}`",
            f"- Leakage violations: `{summary['leakage_violations']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            f"- Router actions: `{summary['router_actions']}`",
            f"- Abstain only: `{summary['abstain_only']}`",
            "",
            "## Boundary",
            "",
            "This scan only verifies field-level leakage for router-final training targets. It does not prove answer-changing router quality.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan router-final target manifest for leakage.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = scan_manifest(args.manifest)
    summary.update(
        {
            "run_id": "R212",
            "title": "Router-final PromptEdge leakage scan",
            "no_api": True,
            "claim_boundary": "Leakage scan only; no accuracy claim.",
        }
    )

    os.makedirs(os.path.dirname(args.summary_json), exist_ok=True)
    with open(args.summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(args.report_md), exist_ok=True)
    with open(args.report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
