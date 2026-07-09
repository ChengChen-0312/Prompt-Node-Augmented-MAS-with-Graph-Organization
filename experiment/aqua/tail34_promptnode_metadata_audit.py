import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


RULE_NAME = "r081_tail34_promptnode_metadata_audit"

SOURCES = [
    {
        "run_id": "R058_dense_generated_pn",
        "path": "experiment/aqua/aqua_tail34_r058_router_contract_terminal_results.jsonl",
        "mode": "direct",
        "positive_accuracy_source": False,
    },
    {
        "run_id": "R064_router_view",
        "path": "experiment/aqua/aqua_tail34_pn_router_contract_results.jsonl",
        "mode": "direct",
        "positive_accuracy_source": True,
    },
    {
        "run_id": "R064_candidate_view",
        "path": "experiment/aqua/aqua_tail34_pn_candidate_select_results.jsonl",
        "mode": "direct",
        "positive_accuracy_source": False,
    },
    {
        "run_id": "R064_conservative_view",
        "path": "experiment/aqua/aqua_tail34_pn_conservative_router_results.jsonl",
        "mode": "direct",
        "positive_accuracy_source": False,
    },
    {
        "run_id": "R064_calibrated_view",
        "path": "experiment/aqua/aqua_tail34_pn_calibrated_utility_results.jsonl",
        "mode": "direct",
        "positive_accuracy_source": True,
    },
    {
        "run_id": "R069_fresh_integrated_multiview",
        "path": "experiment/aqua/aqua_tail34_r069_integrated_selective_multiview_results.jsonl",
        "mode": "nested_views",
        "positive_accuracy_source": True,
    },
    {
        "run_id": "R072_fresh_cascade",
        "path": "experiment/aqua/aqua_tail34_r072_integrated_cascade_results.jsonl",
        "mode": "nested_views",
        "positive_accuracy_source": True,
    },
    {
        "run_id": "R074_fresh_surgical_cascade",
        "path": "experiment/aqua/aqua_tail34_r074_surgical_cascade_results.jsonl",
        "mode": "nested_views",
        "positive_accuracy_source": True,
    },
]


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _roles_have_promptnode(graph: Any) -> bool:
    if not isinstance(graph, dict):
        return False
    roles = graph.get("roles") or []
    return any(str(role).startswith("PN_") for role in roles)


def _graphs_for_record(record: Dict[str, Any], mode: str) -> List[Any]:
    if mode == "direct":
        return [record.get("generated_graph")]
    if mode == "nested_views":
        return [
            view.get("generated_graph")
            for view in (record.get("view_records") or {}).values()
            if isinstance(view, dict)
        ]
    raise ValueError(f"Unknown metadata-audit mode: {mode}")


def audit_source(source: Dict[str, Any]) -> Dict[str, Any]:
    rows = load_jsonl(source["path"])
    graph_records = 0
    graph_records_with_promptnode_roles = 0
    variant_graphs = 0
    variant_graphs_with_promptnode_roles = 0
    for record in rows:
        graphs = [graph for graph in _graphs_for_record(record, source["mode"]) if isinstance(graph, dict)]
        if graphs:
            graph_records += 1
        if any(_roles_have_promptnode(graph) for graph in graphs):
            graph_records_with_promptnode_roles += 1
        variant_graphs += len(graphs)
        variant_graphs_with_promptnode_roles += sum(1 for graph in graphs if _roles_have_promptnode(graph))

    return {
        "run_id": source["run_id"],
        "path": source["path"],
        "mode": source["mode"],
        "positive_accuracy_source": bool(source["positive_accuracy_source"]),
        "records": len(rows),
        "records_with_generated_graph": graph_records,
        "records_with_promptnode_roles": graph_records_with_promptnode_roles,
        "variant_graphs": variant_graphs,
        "variant_graphs_with_promptnode_roles": variant_graphs_with_promptnode_roles,
        "promptnode_record_rate": graph_records_with_promptnode_roles / len(rows) if rows else 0.0,
    }


def build_metadata_audit(sources: Sequence[Dict[str, Any]] = SOURCES) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = [audit_source(source) for source in sources]
    positive_sources = [row for row in rows if row["positive_accuracy_source"]]
    positive_with_promptnode = [
        row for row in positive_sources if row["records_with_promptnode_roles"] > 0
    ]
    dense_metadata_negative = [
        row
        for row in rows
        if row["run_id"] == "R058_dense_generated_pn" and row["records_with_promptnode_roles"] > 0
    ]
    summary = {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "sources": len(rows),
        "positive_accuracy_sources": len(positive_sources),
        "positive_accuracy_sources_with_promptnode_roles": len(positive_with_promptnode),
        "dense_metadata_negative_sources": len(dense_metadata_negative),
        "claim_boundary": (
            "positive tail34 sources lack explicit PromptNode graph metadata, while the dense metadata-compatible "
            "R058 source is negative. This audit shows the next candidate pool must combine positive clean-fix behavior "
            "with first-class PromptNode graph metadata."
        ),
    }
    return rows, summary


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


def render_report(rows: Sequence[Dict[str, Any]], summary: Dict[str, Any], output_jsonl: str) -> str:
    table_rows = [
        "| `{run_id}` | `{records}` | `{records_with_generated_graph}` | `{records_with_promptnode_roles}` | `{variant_graphs_with_promptnode_roles}/{variant_graphs}` | `{positive}` |".format(
            run_id=row["run_id"],
            records=row["records"],
            records_with_generated_graph=row["records_with_generated_graph"],
            records_with_promptnode_roles=row["records_with_promptnode_roles"],
            variant_graphs_with_promptnode_roles=row["variant_graphs_with_promptnode_roles"],
            variant_graphs=row["variant_graphs"],
            positive=row["positive_accuracy_source"],
        )
        for row in rows
    ]
    return "\n".join(
        [
            "# R081 Tail34 PromptNode Metadata Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Output rows: `{output_jsonl}`",
            f"- Sources audited: `{summary['sources']}`",
            f"- Positive accuracy sources: `{summary['positive_accuracy_sources']}`",
            f"- Positive sources with PromptNode roles: `{summary['positive_accuracy_sources_with_promptnode_roles']}`",
            f"- Dense metadata negative sources: `{summary['dense_metadata_negative_sources']}`",
            "",
            "| Source | Records | Records with graph | Records with PN roles | PN variant graphs | Positive accuracy source |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R081 explains why R078 cannot yet become the main SCI method. The tail34 sources with positive accuracy signal "
            "(R064/R069/R072/R074) do not expose explicit PromptNode roles in their generated graphs. The only audited "
            "tail34 source with PromptNode roles on every record is R058, and R080 shows that source harms accuracy. "
            "The next experiment must generate clean-fix-aligned PromptNode graph candidates, not simply rescore the "
            "existing positive traces or reuse dense R058 candidates.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit PromptNode graph metadata coverage across tail34 sources.")
    parser.add_argument(
        "--output-jsonl",
        default="experiment/aqua/aqua_tail34_r081_promptnode_metadata_audit_rows.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_tail34_r081_promptnode_metadata_audit_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_tail34_r081_promptnode_metadata_audit_report.md",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows, summary = build_metadata_audit()
    write_jsonl(args.output_jsonl, rows)
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(rows, summary, args.output_jsonl))
    print(
        "Audited tail34 PromptNode metadata: "
        f"sources={summary['sources']} "
        f"positive_with_pn={summary['positive_accuracy_sources_with_promptnode_roles']}"
    )


if __name__ == "__main__":
    main()
