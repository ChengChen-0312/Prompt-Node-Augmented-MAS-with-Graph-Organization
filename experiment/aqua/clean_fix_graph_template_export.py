import argparse
import datetime
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402


RULE_NAME = "r082_clean_fix_graph_template_export"

FORBIDDEN_TEMPLATE_FIELDS = {
    "true_answer",
    "predicted_answer",
    "router_option",
    "direct_majority",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
    "task_id",
    "source_task_id",
}


def _field_violates(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_TEMPLATE_FIELDS:
                return True
            if _field_violates(child):
                return True
    elif isinstance(value, list):
        return any(_field_violates(child) for child in value)
    return False


def _is_positive(row: Dict[str, Any]) -> bool:
    target = row.get("clean_fix_distillation_target") or {}
    return target.get("target_class") == "clean_fix_preserve_graph"


def _graph_target(row: Dict[str, Any]) -> Dict[str, Any]:
    return (row.get("clean_fix_distillation_target") or {}).get("graph_policy_target") or {}


def build_graph_templates(rows: Sequence[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    slice_counts: Dict[str, Counter[str]] = defaultdict(Counter)
    method_counts: Dict[str, Counter[str]] = defaultdict(Counter)
    positive_rows = 0
    for row in rows:
        if not _is_positive(row):
            continue
        target = _graph_target(row)
        signature = str(target.get("graph_signature") or "")
        if not signature:
            continue
        positive_rows += 1
        if signature not in grouped:
            grouped[signature] = {
                "graph_signature": signature,
                "support_count": 0,
                "roles": list(target.get("roles") or []),
                "edges": list(target.get("edges") or []),
                "prompt_node_roles": list(target.get("prompt_node_roles") or []),
                "prompt_node_specs": list(target.get("prompt_node_specs") or []),
                "prompt_node_edge_permissions": dict(target.get("prompt_node_edge_permissions") or {}),
            }
        grouped[signature]["support_count"] += 1
        slice_counts[signature][str(row.get("source_slice_prefix"))] += 1
        method_counts[signature][str(row.get("source_candidate_method"))] += 1

    templates = []
    for signature, template in grouped.items():
        completed = {
            **template,
            "support_slice_counts": dict(sorted(slice_counts[signature].items())),
            "support_candidate_method_counts": dict(sorted(method_counts[signature].items())),
            "prompt_node_spec_count": len(template.get("prompt_node_specs") or []),
            "prompt_node_edge_permission_count": len(template.get("prompt_node_edge_permissions") or {}),
            "claim_boundary": (
                "Template-level PromptNode graph candidate derived from R077 clean-fix-preserve targets. "
                "It contains roles, edges, identity/permission/lifecycle metadata, and support counts, but no task ids, "
                "answers, predictions, audit labels, or correctness fields."
            ),
        }
        templates.append(completed)

    templates.sort(key=lambda item: (-int(item["support_count"]), str(item["graph_signature"])))
    summary = {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "source_rows": len(rows),
        "positive_rows": positive_rows,
        "unique_templates": len(templates),
        "templates_with_promptnode_specs": sum(1 for item in templates if item["prompt_node_spec_count"] > 0),
        "templates_with_edge_permissions": sum(
            1 for item in templates if item["prompt_node_edge_permission_count"] > 0
        ),
        "top_support_count": templates[0]["support_count"] if templates else 0,
        "forbidden_field_violations": sum(1 for item in templates if _field_violates(item)),
        "excluded_template_fields": sorted(FORBIDDEN_TEMPLATE_FIELDS),
        "claim_boundary": (
            "R082 exports a clean-fix PromptNode graph template library for future candidate generation. "
            "It is not an answer-accuracy result."
        ),
    }
    return templates, summary


def build_first200_templates(
    input_jsonl: str = "experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = load_jsonl_rows(input_jsonl)
    templates, summary = build_graph_templates(rows)
    summary["input_jsonl"] = input_jsonl
    return templates, summary


def write_json(path: str, payload: Dict[str, Any]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_text(path: str, text: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def render_report(templates: Sequence[Dict[str, Any]], summary: Dict[str, Any], output_jsonl: str) -> str:
    table_rows = [
        "| `{idx}` | `{support}` | `{nodes}` | `{edges}` | `{specs}` | `{methods}` |".format(
            idx=index + 1,
            support=template["support_count"],
            nodes=len(template.get("roles") or []),
            edges=len(template.get("edges") or []),
            specs=template["prompt_node_spec_count"],
            methods=", ".join(
                f"{key}={value}" for key, value in template.get("support_candidate_method_counts", {}).items()
            ),
        )
        for index, template in enumerate(templates[:10])
    ]
    return "\n".join(
        [
            "# R082 Clean-Fix PromptNode Graph Template Export",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Input rows: `{summary.get('input_jsonl')}`",
            f"- Output templates: `{output_jsonl}`",
            f"- Source rows: `{summary['source_rows']}`",
            f"- Positive rows: `{summary['positive_rows']}`",
            f"- Unique templates: `{summary['unique_templates']}`",
            f"- Templates with PromptNode specs: `{summary['templates_with_promptnode_specs']}`",
            f"- Templates with edge permissions: `{summary['templates_with_edge_permissions']}`",
            f"- Forbidden-field violations: `{summary['forbidden_field_violations']}`",
            "",
            "| Rank | Support | Nodes | Edges | PromptNode specs | Candidate-method support |",
            "| ---: | ---: | ---: | ---: | ---: | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R082 turns the R077 clean-fix-preserve graph targets into a template library that can seed the next candidate "
            "generation experiment. This closes the bookkeeping gap exposed by R081: future tail34 candidates must carry "
            "explicit PromptNode roles/specs like R058, but they should use graph patterns distilled from clean-fix targets "
            "rather than dense R058 generation.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export clean-fix PromptNode graph templates from R077 rows.")
    parser.add_argument(
        "--input-jsonl",
        default="experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl",
    )
    parser.add_argument(
        "--output-jsonl",
        default="experiment/aqua/aqua_first200_r082_clean_fix_graph_templates.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_first200_r082_clean_fix_graph_templates_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_r082_clean_fix_graph_templates_report.md",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    templates, summary = build_first200_templates(args.input_jsonl)
    write_jsonl(args.output_jsonl, templates)
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(templates, summary, args.output_jsonl))
    print(
        "Exported clean-fix graph templates: "
        f"positive_rows={summary['positive_rows']} unique_templates={summary['unique_templates']} "
        f"violations={summary['forbidden_field_violations']}"
    )


if __name__ == "__main__":
    main()
