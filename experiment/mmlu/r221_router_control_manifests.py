from __future__ import annotations

import argparse
import copy
import json
import os
import random
from collections import Counter
from typing import Any, Dict, List


CONTROL_VARIANTS = [
    "abstain_only_router",
    "random_switch_labels_same_rate",
    "always_switch_to_objective",
    "node_only_no_promptedge_text",
]
OPTION_LABELS = {"A", "B", "C", "D", "E"}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _objective_label(row: Dict[str, Any]) -> str:
    label = str(row.get("model_visible_input", {}).get("objective_prediction") or "").strip().upper()
    return label if label in OPTION_LABELS else "NONE"


def _base_control_row(row: Dict[str, Any], variant: str) -> Dict[str, Any]:
    out = copy.deepcopy(row)
    out["control_variant"] = variant
    out["source_router_action"] = row.get("router_action")
    out["source_target_option_label"] = row.get("target_option_label")
    out["control_policy"] = {
        "promptedge_text_enabled": True,
        "randomized": False,
        "uses_objective_prediction": False,
    }
    return out


def _set_abstain(row: Dict[str, Any]) -> None:
    row["router_action"] = "abstain"
    row["target_option_label"] = "NONE"


def _set_switch_to_objective(row: Dict[str, Any]) -> None:
    label = _objective_label(row)
    if label == "NONE":
        _set_abstain(row)
        return
    row["router_action"] = "switch_to_objective"
    row["target_option_label"] = label
    row["control_policy"]["uses_objective_prediction"] = True


def build_control_records(
    records: List[Dict[str, Any]],
    variant: str,
    seed: int = 20260709,
) -> List[Dict[str, Any]]:
    if variant not in CONTROL_VARIANTS:
        raise ValueError(f"Unknown control variant: {variant}")

    control = [_base_control_row(row, variant) for row in records]
    if variant == "abstain_only_router":
        for row in control:
            _set_abstain(row)
        return control

    if variant == "always_switch_to_objective":
        for row in control:
            _set_switch_to_objective(row)
        return control

    if variant == "random_switch_labels_same_rate":
        original_switch_count = sum(
            1 for row in records if row.get("router_action") == "switch_to_objective"
        )
        eligible = [idx for idx, row in enumerate(control) if _objective_label(row) != "NONE"]
        selected = set(random.Random(seed).sample(eligible, min(original_switch_count, len(eligible))))
        for idx, row in enumerate(control):
            row["control_policy"]["randomized"] = True
            if idx in selected:
                _set_switch_to_objective(row)
            else:
                _set_abstain(row)
        return control

    if variant == "node_only_no_promptedge_text":
        for row in control:
            schema = row.setdefault("router_final_schema", {})
            schema["promptedge_text_policy"] = {
                "edge_text_as_prompt": False,
                "source_field": "disabled_control",
                "scope": "Node-only control: PromptEdge text is disabled.",
            }
            row["control_policy"]["promptedge_text_enabled"] = False
        return control

    raise AssertionError("unreachable")


def summarize_controls(control_rows: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    variant_rows = {variant: len(rows) for variant, rows in sorted(control_rows.items())}
    variant_switches = {
        variant: sum(row.get("router_action") == "switch_to_objective" for row in rows)
        for variant, rows in sorted(control_rows.items())
    }
    split_counts: Dict[str, Dict[str, int]] = {}
    for variant, rows in sorted(control_rows.items()):
        split_counts[variant] = dict(sorted(Counter(row.get("split_role", "") for row in rows).items()))
    return {
        "variants": len(control_rows),
        "variant_rows": variant_rows,
        "variant_switches": variant_switches,
        "variant_split_counts": split_counts,
        "total_rows": sum(variant_rows.values()),
    }


def export_control_manifests(
    input_jsonl: str,
    output_dir: str,
    summary_json: str,
    report_md: str,
    seed: int = 20260709,
) -> Dict[str, Any]:
    records = load_jsonl(input_jsonl)
    os.makedirs(output_dir, exist_ok=True)
    control_rows: Dict[str, List[Dict[str, Any]]] = {}
    output_files: Dict[str, str] = {}
    for variant in CONTROL_VARIANTS:
        rows = build_control_records(records, variant, seed=seed)
        path = os.path.join(output_dir, f"mmlu_r221_{variant}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        control_rows[variant] = rows
        output_files[variant] = path

    summary = summarize_controls(control_rows)
    summary.update(
        {
            "run_id": "R221",
            "title": "Router-final negative-control manifest materialization",
            "claim_boundary": "Control manifest materialization only; no API and no accuracy claim.",
            "no_api": True,
            "input_jsonl": input_jsonl,
            "output_dir": output_dir,
            "output_files": output_files,
            "seed": seed,
        }
    )

    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))

    return summary


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R221 Router-Final Control Manifests",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Result",
        "",
        f"- Variants: `{summary['variants']}`",
        f"- Total rows: `{summary['total_rows']}`",
        f"- Seed: `{summary['seed']}`",
        "",
        "| Variant | Rows | Switch labels |",
        "|---|---:|---:|",
    ]
    for variant, count in summary["variant_rows"].items():
        rows.append(f"| `{variant}` | `{count}` | `{summary['variant_switches'][variant]}` |")
    rows.extend(
        [
            "",
            "## Boundary",
            "",
            "These are control manifests only. They do not run the model and do not support accuracy claims.",
            "",
        ]
    )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build router-final negative-control manifests.")
    parser.add_argument("--input_jsonl", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    parser.add_argument("--seed", type=int, default=20260709)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = export_control_manifests(
        input_jsonl=args.input_jsonl,
        output_dir=args.output_dir,
        summary_json=args.summary_json,
        report_md=args.report_md,
        seed=args.seed,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
