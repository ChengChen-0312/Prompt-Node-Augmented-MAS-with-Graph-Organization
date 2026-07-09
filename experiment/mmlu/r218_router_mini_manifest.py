from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from typing import Any, Dict, List, Tuple


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_mini_manifest(
    records: List[Dict[str, Any]],
    max_abstain_per_switch: int = 2,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    train_switch = [
        row for row in records
        if row.get("split_role") == "train" and row.get("router_action") == "switch_to_objective"
    ]
    train_abstain = [
        row for row in records
        if row.get("split_role") == "train" and row.get("router_action") == "abstain"
    ]
    frozen_eval = [row for row in records if row.get("split_role") == "frozen_eval"]

    abstain_limit = len(train_switch) * max(0, int(max_abstain_per_switch))
    selected_train_abstain = train_abstain[:abstain_limit]
    mini = list(train_switch) + list(selected_train_abstain) + list(frozen_eval)
    action_counts = Counter(row.get("router_action", "") for row in mini)
    split_counts = Counter(row.get("split_role", "") for row in mini)
    summary = {
        "source_records": len(records),
        "mini_records": len(mini),
        "max_abstain_per_switch": max_abstain_per_switch,
        "train_switch_records": len(train_switch),
        "train_abstain_records_available": len(train_abstain),
        "train_abstain_records_selected": len(selected_train_abstain),
        "frozen_eval_records": len(frozen_eval),
        "frozen_eval_switch_records": sum(
            1 for row in frozen_eval if row.get("router_action") == "switch_to_objective"
        ),
        "router_actions": dict(sorted(action_counts.items())),
        "split_roles": dict(sorted(split_counts.items())),
    }
    return mini, summary


def export_mini_manifest(
    input_jsonl: str,
    output_jsonl: str,
    summary_json: str,
    report_md: str,
    max_abstain_per_switch: int = 2,
) -> Dict[str, Any]:
    records = load_jsonl(input_jsonl)
    mini, summary = build_mini_manifest(records, max_abstain_per_switch)
    summary.update(
        {
            "run_id": "R218",
            "title": "Router-final mini-manifest materialization",
            "claim_boundary": "Manifest materialization only; no API and no accuracy claim.",
            "no_api": True,
            "input_jsonl": input_jsonl,
            "output_jsonl": output_jsonl,
        }
    )

    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for row in mini:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))

    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R218 Router-Final Mini-Manifest",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Result",
            "",
            f"- Source records: `{summary['source_records']}`",
            f"- Mini records: `{summary['mini_records']}`",
            f"- Train switch records: `{summary['train_switch_records']}`",
            f"- Train abstain records selected: `{summary['train_abstain_records_selected']}`",
            f"- Frozen eval records: `{summary['frozen_eval_records']}`",
            f"- Frozen eval switch records: `{summary['frozen_eval_switch_records']}`",
            f"- Router actions: `{summary['router_actions']}`",
            f"- Split roles: `{summary['split_roles']}`",
            "",
            "## Boundary",
            "",
            "The mini-manifest keeps all non-abstain train targets, caps train abstain controls, and preserves all frozen-eval rows. It is not an API result.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build router-final mini-manifest.")
    parser.add_argument("--input_jsonl", required=True)
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    parser.add_argument("--max_abstain_per_switch", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = export_mini_manifest(
        input_jsonl=args.input_jsonl,
        output_jsonl=args.output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
        max_abstain_per_switch=args.max_abstain_per_switch,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
