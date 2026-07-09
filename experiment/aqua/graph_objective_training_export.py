import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DISALLOWED_OUTCOME_FIELDS = {
    "true_answer",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
    "r035_selected_prediction",
    "r035_selected_source",
}


def load_json(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_objective_records(path: str) -> List[Dict[str, Any]]:
    payload = load_json(path)
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError(f"No records list found in {path}")
    return records


def _top_score_info(ranked_variants: Sequence[Dict[str, Any]]) -> Tuple[Any, int, bool, int]:
    if not ranked_variants:
        return None, 0, False, 0
    top_score = ranked_variants[0].get("score")
    tied_top_count = sum(1 for variant in ranked_variants if variant.get("score") == top_score)
    lower_scores = [
        int(variant.get("score", 0))
        for variant in ranked_variants
        if variant.get("score") != top_score
    ]
    margin = int(top_score) - max(lower_scores) if lower_scores and top_score is not None else 0
    return top_score, tied_top_count, tied_top_count > 1, margin


def _training_target(
    variant: Dict[str, Any],
    top_score: Any,
    has_top_tie: bool,
    score_margin: int,
    min_score_margin: int,
) -> str:
    if variant.get("score") != top_score:
        return "non_preferred_graph"
    if has_top_tie:
        return "multi_view_tie"
    if top_score is None or int(top_score) <= 0:
        return "non_positive_top"
    if score_margin < min_score_margin:
        return "low_margin_top"
    return "preferred_graph"


def build_training_rows(
    objective_records: Sequence[Dict[str, Any]],
    min_score_margin: int = 3,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    task_count = 0
    positive_top_tasks = 0
    top_score_ties = 0
    margin_top_tasks = 0
    target_counts: Counter[str] = Counter()
    method_counts: Counter[str] = Counter()

    for record in objective_records:
        ranked = list(record.get("ranked_variants") or [])
        if not ranked:
            continue
        task_count += 1
        top_score, tied_top_count, has_top_tie, score_margin = _top_score_info(ranked)
        if top_score is not None and int(top_score) > 0:
            positive_top_tasks += 1
        if has_top_tie:
            top_score_ties += 1
        if not has_top_tie and top_score is not None and int(top_score) > 0 and score_margin >= min_score_margin:
            margin_top_tasks += 1

        for rank_index, variant in enumerate(ranked):
            target = _training_target(
                variant,
                top_score=top_score,
                has_top_tie=has_top_tie,
                score_margin=score_margin,
                min_score_margin=min_score_margin,
            )
            target_counts[target] += 1
            method_counts[str(variant.get("method_key"))] += 1
            rows.append(
                {
                    "task_id": record.get("task_id"),
                    "slice_prefix": record.get("slice_prefix"),
                    "candidate_method": variant.get("method_key"),
                    "rank_index": rank_index,
                    "objective_score": variant.get("score"),
                    "score_components": variant.get("score_components", {}),
                    "top_score": top_score,
                    "top_tie_count": tied_top_count,
                    "score_margin_to_next": score_margin if variant.get("score") == top_score else None,
                    "is_top_candidate": variant.get("score") == top_score,
                    "is_margin_top": target == "preferred_graph",
                    "training_target": target,
                    "router_option": variant.get("router_option"),
                    "direct_majority": variant.get("direct_majority"),
                    "router_matches_direct_majority": variant.get("router_matches_direct_majority"),
                    "strong_router_contract_count": variant.get("strong_router_contract_count", 0),
                    "has_prompt_node_graph": bool(variant.get("has_prompt_node_graph")),
                    "predicted_answer": variant.get("predicted_answer"),
                }
            )

    summary = {
        "total_tasks": task_count,
        "variant_rows": len(rows),
        "min_score_margin": min_score_margin,
        "positive_top_tasks": positive_top_tasks,
        "top_score_ties": top_score_ties,
        "margin_top_tasks": margin_top_tasks,
        "outcome_field_violations": sum(
            1 for row in rows if DISALLOWED_OUTCOME_FIELDS.intersection(row)
        ),
        "training_target_counts": dict(sorted(target_counts.items())),
        "candidate_method_counts": dict(sorted(method_counts.items())),
        "excluded_outcome_fields": sorted(DISALLOWED_OUTCOME_FIELDS),
        "claim_boundary": (
            "Label-free graph-objective export only. Rows are targets for graph candidate selection "
            "or graph-generator training and contain no gold answer, audit label, or correctness field."
        ),
    }
    return rows, summary


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_jsonl(path: str, rows: Sequence[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def render_report(summary: Dict[str, Any], rows_path: str, source_path: str) -> str:
    target_counts = ", ".join(
        f"{key}={value}" for key, value in summary.get("training_target_counts", {}).items()
    )
    method_counts = ", ".join(
        f"{key}={value}" for key, value in summary.get("candidate_method_counts", {}).items()
    )
    return "\n".join(
        [
            "# AQuA First200 Graph-Objective Training Export",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Source objective summary: `{source_path}`",
            f"- Training rows: `{rows_path}`",
            f"- Total tasks: `{summary['total_tasks']}`",
            f"- Variant rows: `{summary['variant_rows']}`",
            f"- Positive top-score tasks: `{summary['positive_top_tasks']}`",
            f"- Top-score ties: `{summary['top_score_ties']}`",
            f"- Margin-top tasks: `{summary['margin_top_tasks']}` with margin >= `{summary['min_score_margin']}`",
            f"- Outcome-field violations: `{summary['outcome_field_violations']}`",
            f"- Training target counts: `{target_counts}`",
            f"- Candidate method counts: `{method_counts}`",
            "",
            "## How This Supports The Method",
            "",
            "This export turns PromptNode contract evidence into a graph-organization target. "
            "Each row corresponds to one PromptNode graph variant for one task. The preferred target is assigned "
            "only when the label-free contract objective has a unique positive top score separated by the configured margin. "
            "Tied top variants remain multi-view targets rather than forced single-graph labels.",
            "",
            "The rows intentionally exclude gold answers, clean/noisy audit labels, and correctness fields. "
            "They can be used to train or select graph structures before final answer aggregation, which is closer to "
            "the PromptNode-as-virtual-node design than post-hoc answer patching.",
            "",
        ]
    )


def write_artifacts(
    rows: Sequence[Dict[str, Any]],
    summary: Dict[str, Any],
    source_path: str,
    rows_path: str,
    summary_path: str,
    report_path: str,
) -> None:
    write_jsonl(rows_path, rows)
    write_json(
        summary_path,
        {
            "source_objective_summary": source_path,
            "rows_path": rows_path,
            **summary,
        },
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(render_report(summary, rows_path=rows_path, source_path=source_path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export label-free PromptNode graph-objective rows for candidate selection/training."
    )
    parser.add_argument(
        "--objective-summary-json",
        default="experiment/aqua/res_logs/aqua_first200_contract_graph_objective_summary.json",
    )
    parser.add_argument(
        "--output-jsonl",
        default="experiment/aqua/aqua_first200_graph_objective_training_rows.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_first200_graph_objective_training_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_graph_objective_training_export.md",
    )
    parser.add_argument("--min-score-margin", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_objective_records(args.objective_summary_json)
    rows, summary = build_training_rows(records, min_score_margin=args.min_score_margin)
    write_artifacts(
        rows,
        summary,
        source_path=args.objective_summary_json,
        rows_path=args.output_jsonl,
        summary_path=args.summary_json,
        report_path=args.report_md,
    )
    print(
        f"Wrote {len(rows)} graph-objective training rows from "
        f"{summary['total_tasks']} tasks to {args.output_jsonl}"
    )


if __name__ == "__main__":
    main()
