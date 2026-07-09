import argparse
import json
import os
import sys
from collections import Counter, defaultdict
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


def load_jsonl_rows(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _candidate_view(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "method": row.get("candidate_method"),
        "objective_score": row.get("objective_score"),
        "score_components": row.get("score_components", {}),
        "router_option": row.get("router_option"),
        "direct_majority": row.get("direct_majority"),
        "router_matches_direct_majority": row.get("router_matches_direct_majority"),
        "strong_router_contract_count": row.get("strong_router_contract_count", 0),
        "has_prompt_node_graph": bool(row.get("has_prompt_node_graph")),
        "predicted_answer": row.get("predicted_answer"),
        "training_target": row.get("training_target"),
    }


def _score(row: Dict[str, Any]) -> int:
    value = row.get("objective_score", 0)
    return int(value) if value is not None else 0


def build_pairwise_preferences(
    training_rows: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    by_task: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in training_rows:
        by_task[str(row.get("task_id"))].append(row)

    pairs: List[Dict[str, Any]] = []
    skipped_without_preferred = 0
    method_pair_counts: Counter[str] = Counter()

    for task_id, rows in sorted(by_task.items()):
        preferred_rows = [row for row in rows if row.get("training_target") == "preferred_graph"]
        if not preferred_rows:
            skipped_without_preferred += 1
            continue
        preferred = sorted(
            preferred_rows,
            key=lambda row: (-_score(row), str(row.get("candidate_method"))),
        )[0]
        negatives = [row for row in rows if row is not preferred]
        for negative in sorted(negatives, key=lambda row: (-_score(row), str(row.get("candidate_method")))):
            pair_key = f"{preferred.get('candidate_method')}>{negative.get('candidate_method')}"
            method_pair_counts[pair_key] += 1
            pairs.append(
                {
                    "task_id": task_id,
                    "slice_prefix": preferred.get("slice_prefix") or negative.get("slice_prefix"),
                    "positive_method": preferred.get("candidate_method"),
                    "negative_method": negative.get("candidate_method"),
                    "positive_score": _score(preferred),
                    "negative_score": _score(negative),
                    "score_delta": _score(preferred) - _score(negative),
                    "positive": _candidate_view(preferred),
                    "negative": _candidate_view(negative),
                    "preference_source": "label_free_contract_objective",
                    "claim_boundary": (
                        "Pairwise graph preference for graph-generator or candidate-selection training. "
                        "No gold answer, audit label, or correctness field is used."
                    ),
                }
            )

    outcome_field_violations = sum(
        1
        for pair in pairs
        if DISALLOWED_OUTCOME_FIELDS.intersection(pair)
        or DISALLOWED_OUTCOME_FIELDS.intersection(pair.get("positive", {}))
        or DISALLOWED_OUTCOME_FIELDS.intersection(pair.get("negative", {}))
    )
    summary = {
        "source_rows": len(training_rows),
        "total_tasks": len(by_task),
        "tasks_with_preferences": len(by_task) - skipped_without_preferred,
        "skipped_tasks_without_preferred": skipped_without_preferred,
        "pairwise_rows": len(pairs),
        "method_pair_counts": dict(sorted(method_pair_counts.items())),
        "outcome_field_violations": outcome_field_violations,
        "excluded_outcome_fields": sorted(DISALLOWED_OUTCOME_FIELDS),
        "claim_boundary": (
            "Label-free pairwise graph preferences only. These pairs are for training or selecting "
            "PromptNode graph organization before final aggregation and do not provide an accuracy claim."
        ),
    }
    return pairs, summary


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path: str, rows: Sequence[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def render_report(summary: Dict[str, Any], input_rows: str, output_pairs: str) -> str:
    method_pairs = ", ".join(
        f"{key}={value}" for key, value in summary.get("method_pair_counts", {}).items()
    )
    return "\n".join(
        [
            "# AQuA First200 Graph-Objective Pairwise Preferences",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Input graph-objective rows: `{input_rows}`",
            f"- Output pairwise preferences: `{output_pairs}`",
            f"- Source rows: `{summary['source_rows']}`",
            f"- Total tasks: `{summary['total_tasks']}`",
            f"- Tasks with preferences: `{summary['tasks_with_preferences']}`",
            f"- Skipped tasks without preferred graph: `{summary['skipped_tasks_without_preferred']}`",
            f"- Pairwise rows: `{summary['pairwise_rows']}`",
            f"- Outcome-field violations: `{summary['outcome_field_violations']}`",
            f"- Method-pair counts: `{method_pairs}`",
            "",
            "## How This Supports Training",
            "",
            "Each pair compares graph variants for the same task. The positive side is the unique margin-separated "
            "`preferred_graph` from the label-free contract objective; the negative side is another graph variant "
            "for that task. Tasks with only ties, low-margin tops, or non-positive tops are skipped instead of being "
            "forced into brittle supervision.",
            "",
            "These pairs can feed a pairwise ranking loss for a graph generator or a prospective graph selector. "
            "They are closer to the intended PromptNode-as-virtual-node design than answer-level fallback rules, "
            "because they supervise graph organization before final answer aggregation.",
            "",
        ]
    )


def write_artifacts(
    pairs: Sequence[Dict[str, Any]],
    summary: Dict[str, Any],
    input_rows: str,
    output_pairs: str,
    summary_json: str,
    report_md: str,
) -> None:
    write_jsonl(output_pairs, pairs)
    write_json(
        summary_json,
        {
            "input_rows": input_rows,
            "output_pairs": output_pairs,
            **summary,
        },
    )
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary, input_rows=input_rows, output_pairs=output_pairs))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export label-free pairwise preferences from PromptNode graph-objective rows."
    )
    parser.add_argument(
        "--input-jsonl",
        default="experiment/aqua/aqua_first200_graph_objective_training_rows.jsonl",
    )
    parser.add_argument(
        "--output-jsonl",
        default="experiment/aqua/aqua_first200_graph_objective_pairwise_preferences.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_first200_graph_objective_pairwise_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_graph_objective_pairwise_preferences.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_jsonl_rows(args.input_jsonl)
    pairs, summary = build_pairwise_preferences(rows)
    write_artifacts(
        pairs,
        summary,
        input_rows=args.input_jsonl,
        output_pairs=args.output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(
        f"Wrote {len(pairs)} graph-objective pairwise preferences "
        f"from {summary['tasks_with_preferences']} tasks to {args.output_jsonl}"
    )


if __name__ == "__main__":
    main()
