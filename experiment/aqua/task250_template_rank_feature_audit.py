import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r101_task250_template_rank_feature_audit"
CLAIM_BOUNDARY = "task250 metadata feature audit; heuristic hypothesis only, not a general selector"
TASK_ID = "task_250"
DESIRED_PREDICTION = "E"

FORBIDDEN_HEURISTIC_INPUT_FIELDS = {
    "task_id",
    "true_answer",
    "predicted_answer",
    "desired_prediction",
    "is_solved",
    "matches_desired_prediction",
    "clean_label",
    "audit_label",
    "target_action",
}

DEFAULT_CANDIDATE_JSONL = "experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl"
DEFAULT_R092_FORCED_JSONL = "experiment/aqua/aqua_tail34_r092_forced_template_rank1_results.jsonl"
DEFAULT_R100_ROWS_JSONL = "experiment/aqua/aqua_tail34_r100_task250_template_rank_sweep_rows.jsonl"
DEFAULT_ROWS_JSONL = "experiment/aqua/aqua_tail34_r101_task250_template_rank_feature_rows.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r101_task250_template_rank_feature_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r101_task250_template_rank_feature_audit_report.md"


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _contains_forbidden_key(value: Any, forbidden: Iterable[str]) -> bool:
    forbidden_set = set(forbidden)
    if isinstance(value, dict):
        return any(key in forbidden_set or _contains_forbidden_key(child, forbidden_set) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(item, forbidden_set) for item in value)
    return False


def _task250_candidates() -> List[Dict[str, Any]]:
    for row in _load_jsonl(DEFAULT_CANDIDATE_JSONL):
        if row["task_id"] == TASK_ID:
            return row["candidates"]
    raise ValueError(f"{TASK_ID} not found in {DEFAULT_CANDIDATE_JSONL}")


def _rank_outcomes() -> Dict[int, Dict[str, Any]]:
    outcomes: Dict[int, Dict[str, Any]] = {}
    for row in _load_jsonl(DEFAULT_R092_FORCED_JSONL):
        if row["task_id"] == TASK_ID:
            outcomes[1] = {
                "predicted_answer": row["predicted_answer"],
                "is_solved": bool(row["is_solved"]),
                "true_answer": row["true_answer"],
            }
            break
    for row in _load_jsonl(DEFAULT_R100_ROWS_JSONL):
        outcomes[int(row["rank"])] = {
            "predicted_answer": row["predicted_answer"],
            "is_solved": bool(row["is_solved"]),
            "true_answer": row["true_answer"],
        }
    return outcomes


def _metadata_features(candidate: Dict[str, Any]) -> Dict[str, Any]:
    graph = candidate["graph"]
    upstream_roles = [role for role in graph["roles"] if not role.startswith("PN_")]
    role_counts = {role: upstream_roles.count(role) for role in sorted(set(upstream_roles))}
    support_slices = candidate.get("support_slice_counts", {})
    aqua_100 = int(support_slices.get("aqua_100", 0))
    aqua_next100 = int(support_slices.get("aqua_next100", 0))
    return {
        "rank": candidate["rank"],
        "support_count": candidate["support_count"],
        "support_aqua_100": aqua_100,
        "support_aqua_next100": aqua_next100,
        "support_aqua_100_ge_next100": aqua_100 >= aqua_next100,
        "upstream_agent_count": len(upstream_roles),
        "unique_upstream_role_count": len(set(upstream_roles)),
        "upstream_role_counts": role_counts,
        "has_math_solver": "Math Solver" in upstream_roles,
        "has_inspector": "Inspector" in upstream_roles,
        "has_programming_expert": "Programming Expert" in upstream_roles,
        "has_duplicate_upstream_role": any(count > 1 for count in role_counts.values()),
        "edge_count": len(graph.get("edges", [])),
        "pn_write_source_count": sum(
            1
            for permissions in graph.get("edge_permissions", {}).values()
            if "write" in permissions
        ),
        "prompt_node_roles": candidate.get("prompt_node_roles", []),
        "prompt_node_spec_count": len(candidate.get("prompt_node_specs", [])),
    }


def metadata_heuristic_selects(features: Dict[str, Any]) -> bool:
    return (
        features["support_count"] <= 5
        and features["has_math_solver"]
        and (features["has_inspector"] or features["upstream_agent_count"] >= 3)
    )


def build_feature_rows() -> List[Dict[str, Any]]:
    outcomes = _rank_outcomes()
    rows = []
    for candidate in _task250_candidates():
        rank = int(candidate["rank"])
        features = _metadata_features(candidate)
        outcome = outcomes[rank]
        rows.append(
            {
                "task_id": TASK_ID,
                "rank": rank,
                "heuristic_input": features,
                "heuristic_selected": metadata_heuristic_selects(features),
                "predicted_answer": outcome["predicted_answer"],
                "desired_prediction": DESIRED_PREDICTION,
                "matches_desired_prediction": outcome["predicted_answer"] == DESIRED_PREDICTION,
                "is_solved": outcome["is_solved"],
                "true_answer": outcome["true_answer"],
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def _fraction(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}"


def build_feature_audit_summary() -> Dict[str, Any]:
    rows = build_feature_rows()
    matching = [row["rank"] for row in rows if row["matches_desired_prediction"]]
    nonmatching = [row["rank"] for row in rows if not row["matches_desired_prediction"]]
    selected = [row["rank"] for row in rows if row["heuristic_selected"]]
    selected_matching = [
        row for row in rows if row["heuristic_selected"] and row["matches_desired_prediction"]
    ]
    return {
        "rule": RULE_NAME,
        "task_id": TASK_ID,
        "matching_ranks": matching,
        "nonmatching_ranks": nonmatching,
        "heuristic": "support_count<=5 AND has_math_solver AND (has_inspector OR upstream_agent_count>=3)",
        "heuristic_selected_ranks": selected,
        "heuristic_precision": _fraction(len(selected_matching), len(selected)),
        "heuristic_recall": _fraction(len(selected_matching), len(matching)),
        "heuristic_input_field_violations": sum(
            1
            for row in rows
            if _contains_forbidden_key(row["heuristic_input"], FORBIDDEN_HEURISTIC_INPUT_FIELDS)
        ),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = []
    for row in summary["rows"]:
        features = row["heuristic_input"]
        table_rows.append(
            "| `{rank}` | `{pred}` | `{match}` | `{support}` | `{roles}` | `{upstream}` | `{selected}` |".format(
                rank=row["rank"],
                pred=row["predicted_answer"],
                match=row["matches_desired_prediction"],
                support=features["support_count"],
                roles=features["upstream_role_counts"],
                upstream=features["upstream_agent_count"],
                selected=row["heuristic_selected"],
            )
        )
    return "\n".join(
        [
            "# R101 Task250 Template Rank Feature Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Matching ranks: `{summary['matching_ranks']}`",
            f"- Nonmatching ranks: `{summary['nonmatching_ranks']}`",
            f"- Heuristic: `{summary['heuristic']}`",
            f"- Heuristic selected ranks: `{summary['heuristic_selected_ranks']}`",
            f"- Heuristic precision: `{summary['heuristic_precision']}`",
            f"- Heuristic recall: `{summary['heuristic_recall']}`",
            f"- Heuristic input field violations: `{summary['heuristic_input_field_violations']}`",
            "",
            "| Rank | Prediction | Matches E | Support | Upstream role counts | Upstream count | Heuristic selected |",
            "| ---: | --- | --- | ---: | --- | ---: | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "This audit gives a label-free metadata hypothesis for why ranks 2 and 5 worked on "
            "`task_250`: low support templates that keep Math Solver and either Inspector oversight "
            "or a wider upstream-agent fan-in. This is not a general selector until it is tested on "
            "clean-safe regression tasks.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit task250 template-rank metadata features.")
    parser.add_argument("--rows-jsonl", default=DEFAULT_ROWS_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = build_feature_rows()
    _write_jsonl(args.rows_jsonl, rows)
    summary = build_feature_audit_summary()
    summary["rows_jsonl"] = args.rows_jsonl
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R101 task250 feature audit: "
        f"selected={summary['heuristic_selected_ranks']} precision={summary['heuristic_precision']}"
    )


if __name__ == "__main__":
    main()
