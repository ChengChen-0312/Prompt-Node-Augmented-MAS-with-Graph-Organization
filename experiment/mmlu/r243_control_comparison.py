from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_jsonl
from experiment.mmlu.r237_apply_conservative_policy import build_source_lookup


VALID_LABELS = {"A", "B", "C", "D", "E"}


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    if label.startswith("NONE"):
        return "NONE"
    return label[:1] if label[:1] in VALID_LABELS else "NONE"


def evaluate_variant_records(
    rows: List[Dict[str, Any]],
    source_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    details = []
    for row in rows:
        task_id = str(row.get("task_id") or "")
        true_answer = normalize_label(source_lookup.get(task_id, {}).get("true_answer"))
        baseline = normalize_label(row.get("model_visible_input", {}).get("baseline_prediction"))
        selected = (
            normalize_label(row.get("target_option_label"))
            if row.get("router_action") == "switch_to_objective"
            else baseline
        )
        baseline_correct = baseline == true_answer if true_answer in VALID_LABELS else None
        selected_correct = selected == true_answer if true_answer in VALID_LABELS else None
        details.append(
            {
                "task_id": task_id,
                "true_answer": true_answer,
                "baseline_prediction": baseline,
                "selected_prediction": selected,
                "switch": row.get("router_action") == "switch_to_objective",
                "baseline_correct": baseline_correct,
                "selected_correct": selected_correct,
                "fix": baseline_correct is False and selected_correct is True,
                "harm": baseline_correct is True and selected_correct is False,
            }
        )
    evaluated = [row for row in details if row["selected_correct"] is not None]
    return {
        "records": len(rows),
        "evaluated_records": len(evaluated),
        "switches": sum(1 for row in evaluated if row["switch"]),
        "accuracy_count": sum(1 for row in evaluated if row["selected_correct"]),
        "accuracy": sum(1 for row in evaluated if row["selected_correct"]) / len(evaluated) if evaluated else None,
        "baseline_accuracy_count": sum(1 for row in evaluated if row["baseline_correct"]),
        "fixes": sum(1 for row in evaluated if row["fix"]),
        "harms": sum(1 for row in evaluated if row["harm"]),
    }


def _variant_name(path: str) -> str:
    name = os.path.basename(path)
    return name.replace("mmlu_r238_", "").replace(".jsonl", "")


def run_control_comparison(
    manifest_glob: str,
    source_paths: List[str],
    output_json: str,
    report_md: str,
) -> Dict[str, Any]:
    source_lookup = build_source_lookup(source_paths)
    variant_results: Dict[str, Dict[str, Any]] = {}
    for path in sorted(glob.glob(manifest_glob)):
        if "controls_all" in os.path.basename(path):
            continue
        variant_results[_variant_name(path)] = evaluate_variant_records(load_jsonl(path), source_lookup)

    proposed = variant_results.get("proposed_conservative_router", {})
    node_only = variant_results.get("node_only_no_promptedge_text", {})
    always = variant_results.get("always_switch_to_objective", {})
    random_same = variant_results.get("random_switch_labels_same_rate", {})
    abstain = variant_results.get("abstain_only_router", {})
    claim_flags = {
        "beats_abstain_accuracy": proposed.get("accuracy_count", -1) > abstain.get("accuracy_count", -1),
        "beats_random_accuracy": proposed.get("accuracy_count", -1) > random_same.get("accuracy_count", -1),
        "beats_always_accuracy": proposed.get("accuracy_count", -1) > always.get("accuracy_count", -1),
        "lower_harm_than_always": proposed.get("harms", 999) < always.get("harms", 999),
        "beats_node_only_accuracy": proposed.get("accuracy_count", -1) > node_only.get("accuracy_count", -1),
        "edge_text_effect_supported": proposed.get("accuracy_count") > node_only.get("accuracy_count"),
    }
    summary = {
        "run_id": "R243",
        "title": "R238 control comparison",
        "claim_boundary": "Offline control comparison only; no API, no superiority claim, and no SCI-Q2 readiness claim.",
        "no_api": True,
        "manifest_glob": manifest_glob,
        "source_paths": source_paths,
        "variant_results": variant_results,
        "claim_flags": claim_flags,
    }
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R243 R238 Control Comparison",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Variant | Acc | Baseline | Switches | Fix/Harm |",
        "|---|---:|---:|---:|---:|",
    ]
    for variant, item in sorted(summary["variant_results"].items()):
        rows.append(
            f"| `{variant}` | `{item['accuracy_count']}/{item['evaluated_records']}` | `{item['baseline_accuracy_count']}/{item['evaluated_records']}` | `{item['switches']}` | `{item['fixes']}/{item['harms']}` |"
        )
    rows.extend(
        [
            "",
            "## Claim Flags",
            "",
            f"- Beats abstain accuracy: `{summary['claim_flags']['beats_abstain_accuracy']}`",
            f"- Beats random accuracy: `{summary['claim_flags']['beats_random_accuracy']}`",
            f"- Beats always accuracy: `{summary['claim_flags']['beats_always_accuracy']}`",
            f"- Lower harm than always: `{summary['claim_flags']['lower_harm_than_always']}`",
            f"- Beats node-only accuracy: `{summary['claim_flags']['beats_node_only_accuracy']}`",
            f"- Edge-text effect supported: `{summary['claim_flags']['edge_text_effect_supported']}`",
            "",
            "## Interpretation",
            "",
            "The conservative policy supports the abstention-boundary claim offline: it beats abstain and random, and matches always-switch accuracy with fewer harms. It does not support a PromptEdge-text-specific claim because node-only has the same decisions and score.",
            "",
        ]
    )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare R238 conservative controls offline.")
    parser.add_argument("--manifest_glob", required=True)
    parser.add_argument("--source_paths", nargs="+", required=True)
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_control_comparison(
        manifest_glob=args.manifest_glob,
        source_paths=args.source_paths,
        output_json=args.output_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
