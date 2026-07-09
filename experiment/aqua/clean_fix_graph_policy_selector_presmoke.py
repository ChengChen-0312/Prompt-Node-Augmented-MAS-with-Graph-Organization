import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r127_clean_fix_graph_policy_selector_presmoke"
CLAIM_BOUNDARY = "pre-smoke selector plan only; no API, accuracy, cost, or prospective result"

DEFAULT_R126_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r126_clean_fix_graph_policy_selector_protocol_summary.json"
)
DEFAULT_R113_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r113_objective_safety_proxy_rule_summary.json"
)
DEFAULT_CANDIDATE_JSONL = "experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r127_clean_fix_graph_policy_selector_presmoke.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r127_clean_fix_graph_policy_selector_presmoke_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r127_clean_fix_graph_policy_selector_presmoke_report.md"
)

REQUESTED_TASKS = ["task_8", "task_108", "task_188", "task_250"]
FORBIDDEN_SELECTOR_INPUT_FIELDS = {
    "task_id",
    "true_answer",
    "answer",
    "answers",
    "predicted_answer",
    "raw_response",
    "question",
    "task_text",
    "is_solved",
    "baseline_is_solved",
    "audit_label",
    "clean_label",
    "target_action",
    "target_reason",
}


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_SELECTOR_INPUT_FIELDS or _contains_forbidden_key(child):
                return True
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _candidate_index(candidate_jsonl: str) -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in _load_jsonl(candidate_jsonl)}


def _eval_prediction_index(r113_summary: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in r113_summary.get("eval_predictions", [])}


def _memory_write_count(candidate: Dict[str, Any]) -> int:
    graph = candidate.get("graph") or {}
    count = 0
    for edge in graph.get("edge_records", []):
        if edge.get("target_role") == "PN_Memory" and "write" in (edge.get("permissions") or []):
            count += 1
    return count


def _edge_permission_count(candidate: Dict[str, Any]) -> int:
    graph = candidate.get("graph") or {}
    return len(graph.get("edge_permissions") or {})


def _lifecycle_action_count(candidate: Dict[str, Any]) -> int:
    return sum(len(spec.get("lifecycle_actions") or []) for spec in candidate.get("prompt_node_specs") or [])


def _has_update2_metadata(candidate: Dict[str, Any] | None) -> bool:
    if not candidate:
        return False
    required_roles = {"PN_Memory", "PN_Verifier", "PN_Router"}
    if not required_roles.issubset(set(candidate.get("prompt_node_roles") or [])):
        return False
    specs = candidate.get("prompt_node_specs") or []
    if len(specs) < 3:
        return False
    for spec in specs:
        if not spec.get("identity_type"):
            return False
        if not spec.get("insertion_pattern"):
            return False
        if not spec.get("permissions"):
            return False
        if not spec.get("budget"):
            return False
        if not spec.get("lifecycle_actions"):
            return False
        if not spec.get("content_schema"):
            return False
    return _edge_permission_count(candidate) > 0


def _candidate_features(candidate: Dict[str, Any]) -> Dict[str, Any]:
    graph = candidate.get("graph") or {}
    return {
        "rank": candidate.get("rank"),
        "support_count": candidate.get("support_count"),
        "edge_count": len(graph.get("edges") or []),
        "memory_write_edges": _memory_write_count(candidate),
        "prompt_node_roles": list(candidate.get("prompt_node_roles") or []),
        "prompt_node_spec_count": len(candidate.get("prompt_node_specs") or []),
        "edge_permission_count": _edge_permission_count(candidate),
        "lifecycle_action_count": _lifecycle_action_count(candidate),
        "decision_exposure_policy": candidate.get("decision_exposure_policy"),
        "has_update2_metadata": _has_update2_metadata(candidate),
    }


def _select_high_fanin_template(candidates: Sequence[Dict[str, Any]]) -> Dict[str, Any] | None:
    eligible = [candidate for candidate in candidates if _has_update2_metadata(candidate)]
    if not eligible:
        return None
    return max(
        eligible,
        key=lambda candidate: (
            _memory_write_count(candidate),
            len((candidate.get("graph") or {}).get("edges") or []),
            _edge_permission_count(candidate),
            int(candidate.get("support_count") or 0),
            -int(candidate.get("rank") or 999),
        ),
    )


def _selector_input(candidate_row: Dict[str, Any] | None) -> Dict[str, Any]:
    candidates = list((candidate_row or {}).get("candidates") or [])
    return {
        "candidate_count": len(candidates),
        "rank_policy": "max_memory_write_fanin_then_edge_count",
        "candidate_features": [_candidate_features(candidate) for candidate in candidates],
    }


def build_clean_fix_graph_policy_selector_presmoke(
    r126_summary: str = DEFAULT_R126_SUMMARY,
    r113_summary: str = DEFAULT_R113_SUMMARY,
    candidate_jsonl: str = DEFAULT_CANDIDATE_JSONL,
    requested_tasks: Sequence[str] = REQUESTED_TASKS,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    protocol = _load_json(r126_summary)
    proxy = _load_json(r113_summary)
    candidates = _candidate_index(candidate_jsonl)
    eval_predictions = _eval_prediction_index(proxy)

    rows: List[Dict[str, Any]] = []
    for task_id in requested_tasks:
        candidate_row = candidates.get(task_id)
        proxy_row = eval_predictions.get(task_id)
        if candidate_row is None:
            raise ValueError(f"Missing candidate row for {task_id}")
        if proxy_row is None:
            raise ValueError(f"Missing R113 proxy eval prediction for {task_id}")
        selector_input = _selector_input(candidate_row)
        proxy_action = proxy_row.get("proxy_action")
        selected_template = (
            _select_high_fanin_template(candidate_row.get("candidates") or [])
            if proxy_action == "switch_to_objective"
            else None
        )
        planned_action = (
            "switch_to_promptnode_template" if selected_template else "fallback_to_arg"
        )
        rows.append(
            {
                "task_id": task_id,
                "dataset_index": candidate_row.get("dataset_index"),
                "learned_action_rule": proxy.get("learned_rule"),
                "action_source": "R113_proxy_rule_trained_on_R112_first200",
                "proxy_action": proxy_action,
                "planned_action": planned_action,
                "selected_template_rank": selected_template.get("rank") if selected_template else None,
                "selected_template": selected_template,
                "selector_input": selector_input,
                "rank_selection_reason": (
                    "max_memory_write_fanin_then_edge_count"
                    if selected_template
                    else "proxy_rule_fallback"
                ),
                "has_update2_metadata": _has_update2_metadata(selected_template),
                "has_high_fanin_memory_bridge": (
                    _memory_write_count(selected_template) >= 3 if selected_template else False
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    switch_rows = [row for row in rows if row["planned_action"] == "switch_to_promptnode_template"]
    fallback_rows = [row for row in rows if row["planned_action"] == "fallback_to_arg"]
    summary = {
        "rule": RULE_NAME,
        "presmoke_only": True,
        "no_api_run": True,
        "requested_tasks": list(requested_tasks),
        "allowed_training_sources": protocol.get("allowed_training_sources"),
        "forbidden_training_sources": protocol.get("forbidden_training_sources"),
        "uses_tail34_training_source": bool(proxy.get("uses_tail34_training_source")),
        "uses_tail34_outputs_for_rank_selection": False,
        "action_rule_train_source": proxy.get("train_source"),
        "action_rule_eval_source": proxy.get("frozen_eval_source"),
        "learned_action_rule": proxy.get("learned_rule"),
        "candidate_source": candidate_jsonl,
        "switch_tasks": [row["task_id"] for row in switch_rows],
        "fallback_tasks": [row["task_id"] for row in fallback_rows],
        "selected_template_ranks": {
            row["task_id"]: row["selected_template_rank"] for row in switch_rows
        },
        "switches_with_update2_metadata": sum(1 for row in switch_rows if row["has_update2_metadata"]),
        "switches_with_high_fanin_memory_bridge": sum(
            1 for row in switch_rows if row["has_high_fanin_memory_bridge"]
        ),
        "selector_input_field_violations": sum(
            1 for row in rows if _contains_forbidden_key(row["selector_input"])
        ),
        "broad_api_allowed_before_smoke": False,
        "same_four_task_smoke_allowed_next": True,
        "output_jsonl": DEFAULT_OUTPUT_JSONL,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return rows, summary


def render_report(rows: Sequence[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    table_rows = []
    for row in rows:
        selected = row.get("selected_template") or {}
        table_rows.append(
            "| `{task}` | `{action}` | `{proxy}` | `{rank}` | `{memory}` | `{metadata}` | `{reason}` |".format(
                task=row["task_id"],
                action=row["planned_action"],
                proxy=row["proxy_action"],
                rank=row.get("selected_template_rank"),
                memory=_memory_write_count(selected) if selected else 0,
                metadata=row["has_update2_metadata"],
                reason=row["rank_selection_reason"],
            )
        )
    return "\n".join(
        [
            "# R127 Clean-Fix Graph-Policy Selector Pre-Smoke",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Pre-smoke only: `{summary['presmoke_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Learned action rule: `{summary['learned_action_rule']}`",
            f"- Action rule train source: `{summary['action_rule_train_source']}`",
            f"- Uses tail34 training source: `{summary['uses_tail34_training_source']}`",
            f"- Uses tail34 outputs for rank selection: `{summary['uses_tail34_outputs_for_rank_selection']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Fallback tasks: `{summary['fallback_tasks']}`",
            f"- Selected template ranks: `{summary['selected_template_ranks']}`",
            f"- Switches with update2 metadata: `{summary['switches_with_update2_metadata']}`",
            f"- Switches with high-fanin Memory bridge: `{summary['switches_with_high_fanin_memory_bridge']}`",
            f"- Selector input field violations: `{summary['selector_input_field_violations']}`",
            f"- Broad API before smoke: `{summary['broad_api_allowed_before_smoke']}`",
            f"- Same-four-task smoke allowed next: `{summary['same_four_task_smoke_allowed_next']}`",
            "",
            "| Task | Planned action | Proxy action | Template rank | Memory writes | Update2 metadata | Rank reason |",
            "| --- | --- | --- | ---: | ---: | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R127 joins the R113 first200-trained action rule with R083 explicit PromptNode template candidates. "
            "When the action rule switches, the rank policy selects the template with the largest write fan-in "
            "into PN_Memory, then the largest graph edge count. This is a structural PromptNode graph-policy "
            "choice, not a tail34 answer-output lookup.",
            "",
            "The artifact is still pre-smoke only. It permits the same four-task API smoke, but not broad tail34 "
            "or transfer evaluation.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the R127 clean-fix selector pre-smoke plan.")
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows, summary = build_clean_fix_graph_policy_selector_presmoke()
    summary["output_jsonl"] = args.output_jsonl
    _write_jsonl(args.output_jsonl, rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(rows, summary))
    print(
        "Built R127 clean-fix selector pre-smoke: "
        f"switches={summary['switch_tasks']} ranks={summary['selected_template_ranks']}"
    )


if __name__ == "__main__":
    main()
