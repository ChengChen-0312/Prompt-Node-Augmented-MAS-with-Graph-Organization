from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from collections import Counter
from copy import deepcopy
from typing import Any, Dict, List, Sequence


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402
from experiment.aqua.r168_promptedge_selector import (  # noqa: E402
    build_selector_summary,
    split_rows_by_slice,
)


RULE_NAME = "r174_two_head_promptedge_policy_audit"
DEFAULT_INPUT_ROWS = (
    "experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_rows.jsonl"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_first200_r174_two_head_promptedge_policy_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_first200_r174_two_head_promptedge_policy_report.md"
)

INSERT_ACTIONS = {"preserve_safe_insert", "switch_critical_insert"}
SWITCH_ACTIONS = {"switch_critical_insert"}


def add_two_head_targets(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for row in rows:
        item = deepcopy(row)
        action = str(item.get("selective_action") or "")
        item["insertion_target"] = 1 if action in INSERT_ACTIONS else 0
        item["override_target"] = 1 if action in SWITCH_ACTIONS else 0
        if item["override_target"]:
            deployment_action = "insert_switch_allowed"
        elif item["insertion_target"]:
            deployment_action = "insert_observe_only"
        else:
            deployment_action = "fallback_to_arg"
        item["deployment_action"] = deployment_action
        enriched.append(item)
    return enriched


def _rows_for_head(rows: Sequence[Dict[str, Any]], target_field: str) -> List[Dict[str, Any]]:
    head_rows = []
    for row in rows:
        item = deepcopy(row)
        item["positive_graph_target"] = bool(item.get(target_field))
        head_rows.append(item)
    return head_rows


def _binary_metrics(golds: Sequence[int], preds: Sequence[int]) -> Dict[str, Any]:
    tp = fp = tn = fn = 0
    for gold, pred in zip(golds, preds):
        if gold and pred:
            tp += 1
        elif not gold and pred:
            fp += 1
        elif not gold and not pred:
            tn += 1
        else:
            fn += 1
    total = len(golds)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "total": total,
        "correct": tp + tn,
        "accuracy": (tp + tn) / total if total else 0.0,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "positive_total": tp + fn,
        "predicted_positive": tp + fp,
        "positive_precision": precision,
        "positive_recall": recall,
        "positive_f1": f1,
    }


def rule_override_prediction(row: Dict[str, Any]) -> int:
    policy_input = row.get("selector_policy_input") or {}
    graph = policy_input.get("candidate_graph_observation") or {}
    role_counts = graph.get("prompt_node_role_counts") or {}
    has_required_roles = all(
        int(role_counts.get(role) or 0) > 0
        for role in ("PN_Memory", "PN_Verifier", "PN_Router")
    )
    return int(
        policy_input.get("objective_bucket") == "preferred_graph"
        and bool(policy_input.get("objective_prediction_differs_from_baseline"))
        and float(policy_input.get("score_margin_to_next") or 0.0) >= 3.0
        and has_required_roles
        and bool(graph.get("has_promptnode_edge_permissions"))
    )


def evaluate_rule_override(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    enriched = add_two_head_targets(rows)
    return _binary_metrics(
        [int(row["override_target"]) for row in enriched],
        [rule_override_prediction(row) for row in enriched],
    )


def _head_summary(
    rows: Sequence[Dict[str, Any]],
    target_field: str,
    min_positive_for_claim: int,
) -> Dict[str, Any]:
    head_rows = _rows_for_head(rows, target_field)
    selector_summary = build_selector_summary(head_rows)
    train_rows, eval_rows = split_rows_by_slice(head_rows)
    positive_rows = sum(1 for row in head_rows if row.get("positive_graph_target"))
    train_positive = sum(1 for row in train_rows if row.get("positive_graph_target"))
    eval_positive = sum(1 for row in eval_rows if row.get("positive_graph_target"))
    eval_metrics = selector_summary["eval_metrics"]
    data_insufficient = positive_rows < min_positive_for_claim or eval_positive < 5
    learned_head_claim_supported = bool(
        not data_insufficient
        and eval_metrics["positive_precision"] >= 0.8
        and eval_metrics["positive_recall"] >= 0.8
    )
    return {
        "target_field": target_field,
        "positive_rows": positive_rows,
        "train_positive_rows": train_positive,
        "eval_positive_rows": eval_positive,
        "data_insufficient": data_insufficient,
        "learned_head_claim_supported": learned_head_claim_supported,
        "train_metrics": selector_summary["train_metrics"],
        "eval_metrics": eval_metrics,
        "model": selector_summary["model"],
    }


def build_two_head_summary(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    enriched = add_two_head_targets(rows)
    action_counts = Counter(str(row.get("selective_action") or "") for row in enriched)
    target_counts = {
        "insertion_positive": sum(row["insertion_target"] for row in enriched),
        "override_positive": sum(row["override_target"] for row in enriched),
        "fallback": sum(1 for row in enriched if row["deployment_action"] == "fallback_to_arg"),
        "insert_observe_only": sum(
            1 for row in enriched if row["deployment_action"] == "insert_observe_only"
        ),
        "insert_switch_allowed": sum(
            1 for row in enriched if row["deployment_action"] == "insert_switch_allowed"
        ),
    }
    train_rows, eval_rows = split_rows_by_slice(enriched)
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "source_rows": len(enriched),
        "source_action_counts": dict(sorted(action_counts.items())),
        "target_counts": target_counts,
        "train_rows": len(train_rows),
        "eval_rows": len(eval_rows),
        "insertion_head": _head_summary(
            enriched,
            target_field="insertion_target",
            min_positive_for_claim=20,
        ),
        "override_head": _head_summary(
            enriched,
            target_field="override_target",
            min_positive_for_claim=20,
        ),
        "rule_override_metrics": evaluate_rule_override(enriched),
        "claim_boundary": (
            "R174 is a no-API target audit. It separates PromptNode/PromptEdge insertion "
            "from answer override. Insertion-head target agreement is not answer accuracy; "
            "override-head claims are blocked when switch-critical positives are too sparse."
        ),
    }


def render_report(summary: Dict[str, Any]) -> str:
    insertion = summary["insertion_head"]
    override = summary["override_head"]
    rule = summary["rule_override_metrics"]
    return "\n".join(
        [
            "# R174 Two-Head PromptNode/PromptEdge Policy Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Source rows: `{summary['source_rows']}`",
            f"- Action counts: `{summary['source_action_counts']}`",
            f"- Insertion positives: `{summary['target_counts']['insertion_positive']}`",
            f"- Override positives: `{summary['target_counts']['override_positive']}`",
            f"- Insert observe-only: `{summary['target_counts']['insert_observe_only']}`",
            f"- Insert switch-allowed: `{summary['target_counts']['insert_switch_allowed']}`",
            "",
            "## Head Metrics",
            "",
            "| Head | Positives | Eval positives | Eval precision | Eval recall | Eval F1 | Data insufficient | Claim supported |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
            "| Insertion | `{pos}` | `{eval_pos}` | `{prec:.3f}` | `{rec:.3f}` | `{f1:.3f}` | `{insuff}` | `{claim}` |".format(
                pos=insertion["positive_rows"],
                eval_pos=insertion["eval_positive_rows"],
                prec=insertion["eval_metrics"]["positive_precision"],
                rec=insertion["eval_metrics"]["positive_recall"],
                f1=insertion["eval_metrics"]["positive_f1"],
                insuff=insertion["data_insufficient"],
                claim=insertion["learned_head_claim_supported"],
            ),
            "| Override learned | `{pos}` | `{eval_pos}` | `{prec:.3f}` | `{rec:.3f}` | `{f1:.3f}` | `{insuff}` | `{claim}` |".format(
                pos=override["positive_rows"],
                eval_pos=override["eval_positive_rows"],
                prec=override["eval_metrics"]["positive_precision"],
                rec=override["eval_metrics"]["positive_recall"],
                f1=override["eval_metrics"]["positive_f1"],
                insuff=override["data_insufficient"],
                claim=override["learned_head_claim_supported"],
            ),
            "| Override rule | `{pos}` | `all` | `{prec:.3f}` | `{rec:.3f}` | `{f1:.3f}` | `diagnostic` | `False` |".format(
                pos=rule["positive_total"],
                prec=rule["positive_precision"],
                rec=rule["positive_recall"],
                f1=rule["positive_f1"],
            ),
            "",
            "## Interpretation",
            "",
            "The insertion head has enough positive rows to learn when first-class PromptNodes and "
            "PromptEdges should be generated. The override head does not: only four switch-critical "
            "rows exist in R166, split two/two across train/eval, and the learned head has no "
            "claimable positive recall. This explains why R171/R172 could make the graph path run "
            "but could not robustly beat ARG. The next data iteration must create more non-leaky "
            "switch-critical targets before any broad API evaluation.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit two-head PromptEdge policy targets.")
    parser.add_argument("--input-rows", default=DEFAULT_INPUT_ROWS)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = load_jsonl_rows(_repo_path(args.input_rows))
    summary = build_two_head_summary(rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R174 two-head policy audit: "
        f"insertion={summary['target_counts']['insertion_positive']} "
        f"override={summary['target_counts']['override_positive']} "
        f"override_claim={summary['override_head']['learned_head_claim_supported']}"
    )


if __name__ == "__main__":
    main()
