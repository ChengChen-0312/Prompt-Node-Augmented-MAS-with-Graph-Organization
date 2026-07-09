from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import Counter
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_jsonl
from experiment.mmlu.r236_conservative_abstention_policy import policy_switches


VALID_LABELS = ["A", "B", "C", "D", "E"]


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    if label.startswith("NONE"):
        return "NONE"
    return label[:1] if label[:1] in VALID_LABELS else "NONE"


def _objective_label(row: Dict[str, Any]) -> str:
    return normalize_label(row.get("model_visible_input", {}).get("objective_prediction"))


def _set_promptedge_policy(row: Dict[str, Any], enabled: bool, source_field: str, scope: str) -> None:
    schema = row.setdefault("router_final_schema", {})
    schema["promptedge_text_policy"] = {
        "edge_text_as_prompt": bool(enabled),
        "source_field": source_field,
        "scope": scope,
    }


def build_conservative_record(row: Dict[str, Any], policy: str) -> Dict[str, Any]:
    out = copy.deepcopy(row)
    objective = _objective_label(out)
    switch = policy_switches(policy, out.get("model_visible_input", {})) and objective in VALID_LABELS
    out["control_variant"] = "proposed_conservative_router"
    out["source_router_action"] = row.get("router_action")
    out["source_target_option_label"] = row.get("target_option_label")
    out["conservative_policy"] = policy
    out["router_action"] = "switch_to_objective" if switch else "abstain"
    out["target_option_label"] = objective if switch else "NONE"
    out["target_reason"] = (
        f"{policy}: objective switch allowed"
        if switch
        else f"{policy}: abstain by guard"
    )
    schema = out.setdefault("router_final_schema", {})
    schema["schema_version"] = "r238_conservative_router_v1"
    schema["label_policy"] = (
        "Labels are derived from label-free conservative abstention policy over model-visible "
        "baseline/objective support features; gold answers are not model-visible."
    )
    _set_promptedge_policy(
        out,
        True,
        "promptedge_meta.text",
        "Proposed conservative router keeps PromptEdge text enabled.",
    )
    return out


def _control_copy(row: Dict[str, Any], variant: str) -> Dict[str, Any]:
    out = copy.deepcopy(row)
    out["control_variant"] = variant
    out["source_router_action"] = row.get("router_action")
    out["source_target_option_label"] = row.get("target_option_label")
    return out


def build_control_records(proposed_rows: List[Dict[str, Any]], seed: int = 20260709) -> List[Dict[str, Any]]:
    controls: List[Dict[str, Any]] = []
    switch_count = sum(1 for row in proposed_rows if row.get("router_action") == "switch_to_objective")
    rng = random.Random(seed)
    random_switch_indices = set(rng.sample(range(len(proposed_rows)), switch_count)) if switch_count else set()

    for idx, row in enumerate(proposed_rows):
        abstain = _control_copy(row, "abstain_only_router")
        abstain["router_action"] = "abstain"
        abstain["target_option_label"] = "NONE"
        abstain["target_reason"] = "control: force abstain"
        controls.append(abstain)

        always = _control_copy(row, "always_switch_to_objective")
        objective = _objective_label(row)
        always["router_action"] = "switch_to_objective" if objective in VALID_LABELS else "abstain"
        always["target_option_label"] = objective if objective in VALID_LABELS else "NONE"
        always["target_reason"] = "control: always switch to objective prediction"
        controls.append(always)

        node_only = _control_copy(row, "node_only_no_promptedge_text")
        _set_promptedge_policy(
            node_only,
            False,
            "disabled_control",
            "Node-only control: PromptEdge text is disabled.",
        )
        node_only["target_reason"] = "control: conservative actions with PromptEdge text disabled"
        controls.append(node_only)

        random_row = _control_copy(row, "random_switch_labels_same_rate")
        if idx in random_switch_indices:
            random_row["router_action"] = "switch_to_objective"
            random_row["target_option_label"] = rng.choice(VALID_LABELS)
            random_row["target_reason"] = "control: random same-rate switch"
        else:
            random_row["router_action"] = "abstain"
            random_row["target_option_label"] = "NONE"
            random_row["target_reason"] = "control: random same-rate abstain"
        random_row["random_seed"] = seed
        controls.append(random_row)

    return controls


def summarize_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "records": len(records),
        "switches": sum(1 for row in records if row.get("router_action") == "switch_to_objective"),
        "variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in records).items())),
        "switch_counts_by_variant": dict(
            sorted(
                Counter(
                    str(row.get("control_variant"))
                    for row in records
                    if row.get("router_action") == "switch_to_objective"
                ).items()
            )
        ),
    }


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def export_conservative_manifests(
    input_jsonl: str,
    output_dir: str,
    summary_json: str,
    report_md: str,
    policy: str,
    seed: int,
) -> Dict[str, Any]:
    source_rows = load_jsonl(input_jsonl)
    proposed = [build_conservative_record(row, policy) for row in source_rows]
    controls = build_control_records(proposed, seed=seed)
    all_records = proposed + controls
    os.makedirs(output_dir, exist_ok=True)
    paths = {
        "proposed_conservative_router": os.path.join(output_dir, "mmlu_r238_proposed_conservative_router.jsonl"),
        "controls_all": os.path.join(output_dir, "mmlu_r238_conservative_controls_all.jsonl"),
    }
    write_jsonl(paths["proposed_conservative_router"], proposed)
    write_jsonl(paths["controls_all"], controls)
    for variant in sorted({row["control_variant"] for row in controls}):
        variant_path = os.path.join(output_dir, f"mmlu_r238_{variant}.jsonl")
        write_jsonl(variant_path, [row for row in controls if row["control_variant"] == variant])
        paths[variant] = variant_path

    summary = summarize_records(all_records)
    summary.update(
        {
            "run_id": "R238",
            "title": "Conservative router-final manifest export",
            "claim_boundary": "Manifest export only; no API, no accuracy claim, and no SCI-Q2 readiness claim.",
            "no_api": True,
            "policy": policy,
            "input_jsonl": input_jsonl,
            "output_dir": output_dir,
            "paths": paths,
            "seed": seed,
            "proposed_summary": summarize_records(proposed),
            "control_summary": summarize_records(controls),
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
    return "\n".join(
        [
            "# R238 Conservative Router-Final Manifest Export",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Policy: `{summary['policy']}`",
            f"- Records: `{summary['records']}`",
            f"- Proposed rows: `{summary['proposed_summary']['records']}`",
            f"- Proposed switches: `{summary['proposed_summary']['switches']}`",
            f"- Control rows: `{summary['control_summary']['records']}`",
            f"- Switch counts by variant: `{summary['switch_counts_by_variant']}`",
            f"- Output dir: `{summary['output_dir']}`",
            "",
            "## Boundary",
            "",
            "These manifests encode the conservative abstention policy and controls. They do not call a model or prove accuracy.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export conservative router-final manifests.")
    parser.add_argument("--input_jsonl", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    parser.add_argument("--policy", default="baseline_consensus_guard_top3")
    parser.add_argument("--seed", type=int, default=20260709)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = export_conservative_manifests(
        input_jsonl=args.input_jsonl,
        output_dir=args.output_dir,
        summary_json=args.summary_json,
        report_md=args.report_md,
        policy=args.policy,
        seed=args.seed,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
