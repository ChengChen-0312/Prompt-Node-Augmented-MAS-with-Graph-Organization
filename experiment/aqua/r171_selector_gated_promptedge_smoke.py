from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

import networkx as nx
import torch
from sentence_transformers import SentenceTransformer


os.environ["TOKENIZERS_PARALLELISM"] = "false"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AQUA_DIR = os.path.dirname(__file__)
for path in (REPO_ROOT, AQUA_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from datasets.aqua_dataset import aqua_get_predict  # noqa: E402
from experiment.aqua.aqua_prompt_set import ROLE_DESCRIPTION  # noqa: E402
from experiment.aqua.contract_ablation_analysis import load_audit_labels  # noqa: E402
from experiment.aqua.evaluate_aqua import (  # noqa: E402
    apply_prompt_node_policy_to_graph,
    assert_llm_environment_ready,
    assert_valid_evaluation_run,
    describe_agent_outputs,
    describe_candidate_graphs,
    describe_graph,
    resolve_decision_exposure_policy,
)
from experiment.aqua.evaluate_selective_promptnode import (  # noqa: E402
    load_aqua_tasks,
    load_model_with_workdir,
    run_graph_record,
)
from experiment.aqua.finetune_aqua import setup_environment  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402
from experiment.aqua.lightweight_calibrated_smoke_runner import (  # noqa: E402
    load_env_file,
    refresh_gpt_chat_env,
)
from experiment.aqua.offline_utility_selector import (  # noqa: E402
    extract_contract_consensus_features,
    normalize_option,
)
from experiment.aqua.prompt_node_graph import (  # noqa: E402
    attach_prompt_edge_metadata,
    is_prompt_node_role,
    select_prompt_node_candidate_graph,
)
from experiment.aqua.r168_promptedge_selector import (  # noqa: E402
    input_field_violations,
    predict_label,
    predict_score,
)
from experiment.aqua.selective_multiview_trigger import ratio_text, write_jsonl  # noqa: E402
from experiment.utils import convert_to_pyg_graph, generate_graph  # noqa: E402
from mas_framework.graph.graph import TestGraph  # noqa: E402
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens  # noqa: E402

import mas_framework.agents.final_decision  # noqa: E402,F401
import mas_framework.prompt.AQuA_prompt_set  # noqa: E402,F401


RULE_NAME = "r171_selector_gated_promptedge_smoke"
CLAIM_BOUNDARY = (
    "bounded four-task selector-gated PromptNode/PromptEdge smoke only; "
    "not broad held-out accuracy, transfer evidence, or SCI-Q2 readiness"
)

DEFAULT_ENV_FILE = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env"
DEFAULT_BASELINE_MODEL_PATH = "experiment/aqua/output/aqua_sync20_model_20260707-230509"
DEFAULT_PROMPTEDGE_MODEL_PATH = (
    "experiment/aqua/output/aqua_r166_expanded_selective_promptedge_r167_short"
)
DEFAULT_SELECTOR_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_first200_r168_promptedge_selector_summary.json"
)
DEFAULT_SELECTOR_TARGET_ROWS = (
    "experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_rows.jsonl"
)
DEFAULT_DATASET_PATH = "datasets/AQuA/AQuA.jsonl"
DEFAULT_TASK_SPLIT_PATH = "experiment/aqua/task_split_aqua_tail34.json"
DEFAULT_AUDIT_FILE = "experiment/aqua/aqua_tail34_option_binding_audit.jsonl"
DEFAULT_OUTPUT_JSONL = (
    "experiment/aqua/aqua_tail34_r171_selector_gated_promptedge_smoke_results.jsonl"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r171_selector_gated_promptedge_smoke_summary.json"
)
DEFAULT_SUMMARY_LOG_JSONL = (
    "experiment/aqua/res_logs/aqua_tail34_r171_selector_gated_promptedge_smoke_summary.jsonl"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r171_selector_gated_promptedge_smoke_report.md"
)
REGRESSION_TASK_IDS = ("task_8", "task_108", "task_188", "task_250")
MAX_R171_API_TASKS = 4


def _absolute(path: Optional[str]) -> Optional[str]:
    if path is None:
        return None
    return path if os.path.isabs(path) else os.path.abspath(os.path.join(REPO_ROOT, path))


def parse_task_ids(raw: str) -> List[str]:
    task_ids = [item.strip() for item in str(raw or "").split(",") if item.strip()]
    return task_ids or list(REGRESSION_TASK_IDS)


def load_aqua_tasks_by_id(
    dataset_path: str,
    task_split_path: str,
    task_ids: Sequence[str],
) -> List[Dict[str, Any]]:
    tasks = load_aqua_tasks(dataset_path, task_split_path, limit=None)
    by_id = {task["task_id"]: task for task in tasks}
    missing = [task_id for task_id in task_ids if task_id not in by_id]
    if missing:
        raise ValueError(f"Requested task ids are not in the split: {missing}")
    return [by_id[task_id] for task_id in task_ids]


def _load_selector_model(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        summary = json.load(f)
    model = summary.get("model")
    if not isinstance(model, dict):
        raise ValueError(f"Selector summary does not contain a model: {path}")
    return model


def _graph_from_roles_edges(graph: Any) -> nx.DiGraph:
    if isinstance(graph, nx.Graph):
        return nx.DiGraph(graph)
    roles = list((graph or {}).get("roles") or [])
    edges = list((graph or {}).get("edges") or [])
    nx_graph = nx.DiGraph()
    for index, role in enumerate(roles):
        nx_graph.add_node(index, role=role)
    nx_graph.add_edges_from((int(source), int(target)) for source, target in edges)
    return nx_graph


def _graph_signature(nx_graph: nx.Graph) -> str:
    roles = sorted(str(data.get("role") or "") for _, data in nx_graph.nodes(data=True))
    edges = sorted(f"{int(source)}->{int(target)}" for source, target in nx_graph.edges())
    return f"{'|'.join(roles)}::{','.join(edges)}"


def promptedge_contract_evidence(graph: Any) -> Dict[str, Any]:
    nx_graph = attach_prompt_edge_metadata(_graph_from_roles_edges(graph))
    roles = [str(data.get("role") or "") for _, data in nx_graph.nodes(data=True)]
    role_counts = Counter(role for role in roles if is_prompt_node_role(role))
    prompt_edge_counts = nx_graph.graph.get("prompt_edge_type_counts") or {}
    is_dag = nx.is_directed_acyclic_graph(nx_graph)
    required_roles = {"PN_Memory", "PN_Verifier", "PN_Router"}
    has_required_prompt_roles = required_roles.issubset(set(roles))
    has_required_promptedge_path = all(
        int(prompt_edge_counts.get(edge_type, 0)) > 0
        for edge_type in ("write_memory", "verify_contract", "forward_verified")
    )
    return {
        "graph_signature": _graph_signature(nx_graph),
        "num_nodes": nx_graph.number_of_nodes(),
        "num_edges": nx_graph.number_of_edges(),
        "roles": roles,
        "prompt_node_role_counts": dict(sorted(role_counts.items())),
        "prompt_edge_type_counts": dict(sorted(prompt_edge_counts.items())),
        "is_dag": is_dag,
        "has_required_prompt_roles": has_required_prompt_roles,
        "has_required_promptedge_path": has_required_promptedge_path,
        "contract_passed": bool(
            is_dag and has_required_prompt_roles and has_required_promptedge_path
        ),
    }


def _edge_role_pairs(nx_graph: nx.Graph) -> List[str]:
    pairs = []
    for source, target in nx_graph.edges():
        source_role = nx_graph.nodes[source].get("role", "")
        target_role = nx_graph.nodes[target].get("role", "")
        if is_prompt_node_role(source_role) or is_prompt_node_role(target_role):
            pairs.append(f"{source_role}->{target_role}")
    return sorted(pairs)


def build_signature_priors(rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not row.get("positive_graph_target"):
            continue
        target = row.get("graph_policy_target") or {}
        signature = str(target.get("graph_signature") or "")
        if signature:
            grouped[signature].append(row)

    priors: Dict[str, Dict[str, Any]] = {}
    for signature, group in grouped.items():
        margins = [
            float((row.get("selector_policy_input") or {}).get("score_margin_to_next") or 0.0)
            for row in group
        ]
        top_scores = [
            float((row.get("selector_policy_input") or {}).get("objective_top_score") or 0.0)
            for row in group
        ]
        actions = Counter(str(row.get("selective_action") or "") for row in group)
        priors[signature] = {
            "positive_support": len(group),
            "score_margin_to_next": max(margins) if margins else 0.0,
            "objective_top_score": max(top_scores) if top_scores else 0.0,
            "dominant_selective_action": actions.most_common(1)[0][0] if actions else "",
        }
    return priors


def build_selector_policy_input(
    question: str,
    candidate_method: str,
    graph: Any,
    signature_priors: Optional[Dict[str, Dict[str, Any]]] = None,
    baseline_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    nx_graph = attach_prompt_edge_metadata(_graph_from_roles_edges(graph))
    evidence = promptedge_contract_evidence(nx_graph)
    signature_priors = signature_priors or {}
    prior = signature_priors.get(evidence["graph_signature"]) or {}
    prompt_node_edges = [
        edge
        for edge in nx_graph.edges()
        if is_prompt_node_role(nx_graph.nodes[edge[0]].get("role", ""))
        or is_prompt_node_role(nx_graph.nodes[edge[1]].get("role", ""))
    ]
    baseline_votes_split = False
    if baseline_record:
        features = extract_contract_consensus_features(baseline_record)
        valid_votes = int(features.get("direct_valid_vote_count") or 0)
        majority_votes = int(features.get("direct_majority_count") or 0)
        baseline_votes_split = valid_votes > majority_votes

    if prior:
        objective_bucket = "preferred_graph"
        score_margin = float(prior.get("score_margin_to_next") or 0.0)
        objective_top_score = float(prior.get("objective_top_score") or 0.0)
    else:
        objective_bucket = "low_margin_top" if evidence["contract_passed"] else "non_preferred_graph"
        score_margin = 0.0
        objective_top_score = 0.0

    return {
        "question": question,
        "candidate_method": candidate_method,
        "objective_bucket": objective_bucket,
        "score_margin_to_next": score_margin,
        "has_margin_at_least_3": score_margin >= 3.0,
        "objective_prediction_differs_from_baseline": False,
        "baseline_direct_votes_split": baseline_votes_split,
        "objective_top_score": objective_top_score,
        "candidate_graph_observation": {
            "num_prompt_nodes": sum(
                1
                for _, data in nx_graph.nodes(data=True)
                if is_prompt_node_role(data.get("role", ""))
            ),
            "num_prompt_node_edges": len(prompt_node_edges),
            "prompt_node_role_counts": evidence["prompt_node_role_counts"],
            "prompt_node_edge_role_pairs": _edge_role_pairs(nx_graph),
            "has_promptnode_specs": evidence["has_required_prompt_roles"],
            "has_promptnode_edge_permissions": evidence["has_required_promptedge_path"],
        },
        "selector_prior": {
            key: prior.get(key)
            for key in (
                "positive_support",
                "dominant_selective_action",
            )
            if key in prior
        },
    }


def build_selector_decision(
    model: Dict[str, Any],
    policy_input: Dict[str, Any],
) -> Dict[str, Any]:
    row = {"selector_policy_input": policy_input, "positive_graph_target": False}
    violations = input_field_violations([row])
    score = predict_score(model, row)
    threshold = float(model.get("threshold", 0.0))
    if violations:
        return {
            "selector_action": "fallback_to_arg",
            "selector_passed": False,
            "selector_score": score,
            "selector_threshold": threshold,
            "selector_input_field_violations": violations,
            "selector_block_reason": "forbidden_selector_input_fields",
        }
    passed = bool(predict_label(model, row))
    return {
        "selector_action": "run_promptedge" if passed else "fallback_to_arg",
        "selector_passed": passed,
        "selector_score": score,
        "selector_threshold": threshold,
        "selector_input_field_violations": 0,
        "selector_block_reason": "" if passed else "selector_negative",
    }


def build_selected_record(
    baseline_record: Dict[str, Any],
    promptedge_record: Optional[Dict[str, Any]],
    selector_decision: Dict[str, Any],
    contract_evidence: Dict[str, Any],
    policy_input: Dict[str, Any],
) -> Dict[str, Any]:
    true_answer = normalize_option(
        baseline_record.get("true_answer")
        or (promptedge_record or {}).get("true_answer")
    )
    baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
    promptedge_prediction = normalize_option(
        (promptedge_record or {}).get("predicted_answer")
    )
    promptedge_has_valid_option = promptedge_prediction in {"A", "B", "C", "D", "E"}
    selector_prior = (policy_input or {}).get("selector_prior") or {}
    selector_prior_action = str(selector_prior.get("dominant_selective_action") or "")
    switch_intent_allows_override = selector_prior_action == "switch_critical_insert"
    can_switch = bool(
        promptedge_record
        and selector_decision.get("selector_passed")
        and contract_evidence.get("contract_passed")
        and promptedge_has_valid_option
        and switch_intent_allows_override
    )
    selected = promptedge_record if can_switch else baseline_record
    selected_prediction = normalize_option(selected.get("predicted_answer"))
    runtime_fallback_reason = ""
    if not selector_decision.get("selector_passed"):
        runtime_fallback_reason = selector_decision.get("selector_block_reason") or "selector_negative"
    elif not contract_evidence.get("contract_passed"):
        runtime_fallback_reason = "promptedge_contract_failed"
    elif promptedge_record and not promptedge_has_valid_option:
        runtime_fallback_reason = "promptedge_abstained_or_invalid_option"
    elif not switch_intent_allows_override:
        runtime_fallback_reason = (
            "selector_prior_preserve_safe_not_switch_critical"
            if selector_prior_action == "preserve_safe_insert"
            else "selector_prior_missing_switch_critical_intent"
        )
    elif not promptedge_record:
        runtime_fallback_reason = "promptedge_not_run"
    baseline_is_solved = baseline_prediction == true_answer
    promptedge_is_solved = (
        promptedge_prediction == true_answer if promptedge_record else False
    )
    is_solved = selected_prediction == true_answer
    return {
        "task_id": baseline_record.get("task_id") or (promptedge_record or {}).get("task_id"),
        "question": baseline_record.get("question") or (promptedge_record or {}).get("question"),
        "true_answer": true_answer,
        "predicted_answer": selected_prediction,
        "raw_response": selected.get("raw_response"),
        "is_solved": is_solved,
        "selected_source": "selector_gated_promptedge" if can_switch else "baseline",
        "selection_rule": RULE_NAME,
        "baseline_prediction": baseline_prediction,
        "baseline_is_solved": baseline_is_solved,
        "promptedge_prediction": promptedge_prediction,
        "promptedge_is_solved": promptedge_is_solved,
        "promptedge_was_run": bool(promptedge_record),
        "selector_prior_action": selector_prior_action,
        "switch_intent_allows_override": switch_intent_allows_override,
        "runtime_fallback_reason": "" if can_switch else runtime_fallback_reason,
        "selector_decision": selector_decision,
        "promptedge_contract_evidence": contract_evidence,
        "selector_policy_input": policy_input,
        "baseline_record": baseline_record,
        "promptedge_record": promptedge_record,
        "fix": (not baseline_is_solved) and is_solved,
        "harm": baseline_is_solved and not is_solved,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def prepare_promptedge_candidate(
    task: Dict[str, Any],
    model,
    sentence_model: SentenceTransformer,
    role_constraints_dict: Dict[str, str],
    graph_index: int,
    prompt_node_topology_policy: str,
    num_candidate_graphs: int,
) -> Tuple[nx.DiGraph, List[nx.DiGraph], int, List[Dict[str, Any]], Dict[str, Any]]:
    task_embedding = torch.tensor(
        sentence_model.encode(task["task"]),
        device=model.args.device,
    ).float()
    generated_graphs = generate_graph(
        model,
        task_embedding,
        role_constraints_dict,
        graph_index,
        num_samples=max(num_candidate_graphs, 1),
        batch_size=1,
    )
    if not generated_graphs:
        raise RuntimeError("PromptEdge graph generation failed.")
    candidate_graphs = [
        attach_prompt_edge_metadata(
            apply_prompt_node_policy_to_graph(
                graph,
                prompt_node_policy="none",
                prompt_node_topology_policy=prompt_node_topology_policy,
            )
        )
        for graph in generated_graphs
    ]
    selected_graph, scored_candidates = select_prompt_node_candidate_graph(candidate_graphs)
    selected_candidate_index = next(
        item["candidate_index"]
        for item in scored_candidates
        if candidate_graphs[item["candidate_index"]] is selected_graph
    )
    contract_evidence = promptedge_contract_evidence(selected_graph)
    return (
        selected_graph,
        candidate_graphs,
        selected_candidate_index,
        scored_candidates,
        contract_evidence,
    )


async def run_prepared_graph_record(
    task: Dict[str, Any],
    generated_graph: nx.Graph,
    candidate_graphs: Sequence[nx.Graph],
    selected_candidate_index: int,
    scored_candidates: Sequence[Dict[str, Any]],
    llm_name: str,
    decision_method: str,
    prompt_node_topology_policy: str,
    decision_exposure_policy: str,
) -> Dict[str, Any]:
    task_text = task["task"]
    true_answer = task["answer"]
    task_id = task["task_id"]
    graph = attach_prompt_edge_metadata(generated_graph)
    pyg_data = convert_to_pyg_graph(graph, task_text)
    pyg_data.prompt_node_policy = "none"
    pyg_data.prompt_node_topology_policy = prompt_node_topology_policy
    pyg_data.decision_exposure_policy = resolve_decision_exposure_policy(
        graph,
        decision_exposure_policy,
    )
    test_graph = TestGraph(
        domain="aqua",
        llm_name=llm_name,
        decision_method=decision_method,
        pyg_data=pyg_data,
    )
    result = await test_graph.arun({"task": task_text}, num_rounds=1)
    raw_answer = result[0] if isinstance(result, list) and result else result
    predict_answer = aqua_get_predict(raw_answer)
    candidate_metadata = describe_candidate_graphs(
        list(candidate_graphs),
        selected_candidate_index,
        list(scored_candidates),
    )
    record = {
        "task_id": task_id,
        "question": task_text,
        "true_answer": true_answer,
        "predicted_answer": predict_answer,
        "raw_response": raw_answer,
        "is_solved": predict_answer == true_answer,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "generated_graph": describe_graph(graph),
        "selected_candidate_index": candidate_metadata["selected_candidate_index"],
        "candidate_graphs": candidate_metadata["candidate_graphs"],
        "agent_outputs": describe_agent_outputs(test_graph),
        "prompt_edge_type_counts": graph.graph.get("prompt_edge_type_counts") or {},
    }
    return record


async def run_task_selector_gated_promptedge_async(
    task: Dict[str, Any],
    graph_index: int,
    baseline_model,
    promptedge_model,
    selector_model: Dict[str, Any],
    signature_priors: Dict[str, Dict[str, Any]],
    sentence_model: SentenceTransformer,
    role_constraints_dict: Dict[str, str],
    args: argparse.Namespace,
) -> Dict[str, Any]:
    baseline_record = await run_graph_record(
        task,
        baseline_model,
        sentence_model,
        role_constraints_dict,
        graph_index,
        llm_name=args.llm_name,
        decision_method=args.baseline_decision_method,
        prompt_node_policy="none",
        prompt_node_topology_policy="none",
        decision_exposure_policy="all",
        num_candidate_graphs=args.baseline_num_candidate_graphs,
    )
    (
        promptedge_graph,
        candidate_graphs,
        selected_candidate_index,
        scored_candidates,
        contract_evidence,
    ) = prepare_promptedge_candidate(
        task,
        promptedge_model,
        sentence_model,
        role_constraints_dict,
        graph_index,
        prompt_node_topology_policy=args.prompt_node_topology_policy,
        num_candidate_graphs=args.num_candidate_graphs,
    )
    policy_input = build_selector_policy_input(
        question=task["task"],
        candidate_method="r167_promptedge_graph_generator",
        graph=promptedge_graph,
        signature_priors=signature_priors,
        baseline_record=baseline_record,
    )
    selector_decision = build_selector_decision(selector_model, policy_input)
    promptedge_record = None
    if selector_decision["selector_passed"] and contract_evidence["contract_passed"]:
        promptedge_record = await run_prepared_graph_record(
            task,
            promptedge_graph,
            candidate_graphs,
            selected_candidate_index,
            scored_candidates,
            llm_name=args.llm_name,
            decision_method=args.promptedge_decision_method,
            prompt_node_topology_policy=args.prompt_node_topology_policy,
            decision_exposure_policy=args.promptedge_decision_exposure_policy,
        )
    return build_selected_record(
        baseline_record,
        promptedge_record,
        selector_decision,
        contract_evidence,
        policy_input,
    )


def _audit_split_counts(
    rows: Sequence[Dict[str, Any]],
    audit_labels: Optional[Dict[str, str]],
) -> Dict[str, Any]:
    if not audit_labels:
        return {}
    clean_rows = [row for row in rows if audit_labels.get(row["task_id"]) == "clean"]
    noisy_rows = [row for row in rows if row not in clean_rows]
    return {
        "clean": ratio_text(sum(1 for row in clean_rows if row.get("is_solved")), len(clean_rows)),
        "clean_fix_harm": (
            f"{sum(1 for row in clean_rows if row.get('fix'))}/"
            f"{sum(1 for row in clean_rows if row.get('harm'))}"
        ),
        "noisy_or_ambiguous": ratio_text(
            sum(1 for row in noisy_rows if row.get("is_solved")),
            len(noisy_rows),
        ),
        "noisy_fix_harm": (
            f"{sum(1 for row in noisy_rows if row.get('fix'))}/"
            f"{sum(1 for row in noisy_rows if row.get('harm'))}"
        ),
        "clean_recovery_tasks": [row["task_id"] for row in clean_rows if row.get("fix")],
        "clean_harm_tasks": [row["task_id"] for row in clean_rows if row.get("harm")],
    }


def summarize_records(
    rows: Sequence[Dict[str, Any]],
    cost: float = 0.0,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    audit_labels: Optional[Dict[str, str]] = None,
    env_keys_loaded: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    total = len(rows)
    selected_solved = sum(1 for row in rows if row.get("is_solved"))
    baseline_solved = sum(1 for row in rows if row.get("baseline_is_solved"))
    promptedge_run_rows = [row for row in rows if row.get("promptedge_was_run")]
    promptedge_solved = sum(1 for row in promptedge_run_rows if row.get("promptedge_is_solved"))
    switches = [row for row in rows if row.get("selected_source") == "selector_gated_promptedge"]
    fixes = [row for row in rows if row.get("fix")]
    harms = [row for row in rows if row.get("harm")]
    selector_violations = sum(
        int((row.get("selector_decision") or {}).get("selector_input_field_violations") or 0)
        for row in rows
    )
    contract_passed = sum(
        1 for row in rows if (row.get("promptedge_contract_evidence") or {}).get("contract_passed")
    )
    summary = {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "claim_boundary": CLAIM_BOUNDARY,
        "total_tasks": total,
        "selected_solved_tasks": selected_solved,
        "baseline_solved_tasks": baseline_solved,
        "promptedge_solved_tasks_among_run": promptedge_solved,
        "selected_accuracy": ratio_text(selected_solved, total),
        "baseline_accuracy": ratio_text(baseline_solved, total),
        "promptedge_run_accuracy": ratio_text(promptedge_solved, len(promptedge_run_rows)),
        "delta_vs_baseline": selected_solved - baseline_solved,
        "promptedge_contract_passed": ratio_text(contract_passed, total),
        "promptedge_run_count": len(promptedge_run_rows),
        "switch_tasks": [row["task_id"] for row in switches],
        "fallback_tasks": [
            row["task_id"] for row in rows if row.get("selected_source") == "baseline"
        ],
        "fix_tasks": [row["task_id"] for row in fixes],
        "harm_tasks": [row["task_id"] for row in harms],
        "fix_harm": f"{len(fixes)}/{len(harms)}",
        "selector_input_field_violations": selector_violations,
        "cost": round(float(cost or 0.0), 6),
        "prompt_tokens": int(prompt_tokens or 0),
        "completion_tokens": int(completion_tokens or 0),
        "env_keys_loaded": sorted(set(env_keys_loaded or [])),
        "broad_api_allowed_next": False,
        "sci_q2_ready": False,
        "next_required_audit": "R175",
        "rows": list(rows),
    }
    summary.update(_audit_split_counts(rows, audit_labels))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{base}` | `{pn}` | `{action}` | `{selected}` | `{truth}` | `{score:.3f}` | `{contract}` | `{fix}` | `{harm}` |".format(
            task=row.get("task_id"),
            base=row.get("baseline_prediction"),
            pn=row.get("promptedge_prediction"),
            action=(row.get("selector_decision") or {}).get("selector_action"),
            selected=row.get("predicted_answer"),
            truth=row.get("true_answer"),
            score=float((row.get("selector_decision") or {}).get("selector_score") or 0.0),
            contract=(row.get("promptedge_contract_evidence") or {}).get("contract_passed"),
            fix=row.get("fix"),
            harm=row.get("harm"),
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R171 Selector-Gated PromptNode/PromptEdge Smoke",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['total_tasks']}`",
            f"- Selected accuracy: `{summary['selected_accuracy']}`",
            f"- Internal ARG baseline accuracy: `{summary['baseline_accuracy']}`",
            f"- PromptEdge run accuracy: `{summary['promptedge_run_accuracy']}`",
            f"- Delta vs ARG baseline: `{summary['delta_vs_baseline']:+d}`",
            f"- PromptEdge contract passed: `{summary['promptedge_contract_passed']}`",
            f"- PromptEdge run count: `{summary['promptedge_run_count']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Fix/Harm: `{summary['fix_harm']}`",
            f"- Selector input violations: `{summary['selector_input_field_violations']}`",
            f"- Cost: `${summary['cost']:.6f}`",
            f"- Prompt tokens: `{summary['prompt_tokens']}`",
            f"- Completion tokens: `{summary['completion_tokens']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next required audit: `{summary['next_required_audit']}`",
            "",
            "| Task | ARG | PromptEdge | Selector action | Selected | Truth | Selector score | Contract | Fix | Harm |",
            "| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R171 executes the R170-authorized bounded smoke. The selector can see only label-free "
            "graph-policy fields and live graph observations; task ids, gold answers, correctness flags, "
            "and clean/noisy labels are not selector inputs. A PromptNode/PromptEdge view is executed only "
            "when both the R168 selector and the PromptEdge graph contract pass. This is a regression smoke, "
            "not a paper-level result.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run R171 selector-gated PromptNode/PromptEdge bounded smoke."
    )
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--baseline-model-path", default=DEFAULT_BASELINE_MODEL_PATH)
    parser.add_argument("--promptedge-model-path", default=DEFAULT_PROMPTEDGE_MODEL_PATH)
    parser.add_argument("--selector-summary-json", default=DEFAULT_SELECTOR_SUMMARY_JSON)
    parser.add_argument("--selector-target-rows", default=DEFAULT_SELECTOR_TARGET_ROWS)
    parser.add_argument("--dataset-path", default=DEFAULT_DATASET_PATH)
    parser.add_argument("--task-split-path", default=DEFAULT_TASK_SPLIT_PATH)
    parser.add_argument("--task-ids", default=",".join(REGRESSION_TASK_IDS))
    parser.add_argument("--max-api-tasks", type=int, default=MAX_R171_API_TASKS)
    parser.add_argument("--llm-name", default="gpt-4o-2024-08-06")
    parser.add_argument("--baseline-decision-method", default="FinalRefer")
    parser.add_argument("--baseline-num-candidate-graphs", type=int, default=1)
    parser.add_argument(
        "--promptedge-decision-method",
        default="CalibratedEdgePromptRepairContractFinalRefer",
    )
    parser.add_argument("--prompt-node-topology-policy", default="canonicalize_generated")
    parser.add_argument("--promptedge-decision-exposure-policy", default="auto")
    parser.add_argument("--num-candidate-graphs", type=int, default=4)
    parser.add_argument("--audit-file", default=DEFAULT_AUDIT_FILE)
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--summary-log-jsonl", default=DEFAULT_SUMMARY_LOG_JSONL)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def absolutize_args(args: argparse.Namespace) -> argparse.Namespace:
    for attr in (
        "baseline_model_path",
        "promptedge_model_path",
        "selector_summary_json",
        "selector_target_rows",
        "dataset_path",
        "task_split_path",
        "audit_file",
        "output_jsonl",
        "summary_json",
        "summary_log_jsonl",
        "report_md",
    ):
        setattr(args, attr, _absolute(getattr(args, attr, None)))
    return args


async def main_async() -> None:
    args = absolutize_args(build_arg_parser().parse_args())
    task_ids = parse_task_ids(args.task_ids)
    if len(task_ids) > args.max_api_tasks or args.max_api_tasks > MAX_R171_API_TASKS:
        raise ValueError(
            f"R171 is bounded to at most {MAX_R171_API_TASKS} tasks; "
            f"requested task_ids={task_ids}, max_api_tasks={args.max_api_tasks}"
        )

    env_keys_loaded = load_env_file(args.env_file)
    refresh_gpt_chat_env()
    assert_llm_environment_ready(args.llm_name)
    setup_environment(42)
    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    selector_model = _load_selector_model(args.selector_summary_json)
    selector_rows = load_jsonl_rows(args.selector_target_rows)
    signature_priors = build_signature_priors(selector_rows)

    print(
        "Loaded R171 bounded smoke setup: "
        f"tasks={task_ids} selector_priors={len(signature_priors)} "
        f"env_keys={sorted(set(env_keys_loaded))}"
    )
    print("Loading ARG baseline and PromptEdge graph-generator models...")
    baseline_model = load_model_with_workdir(args.baseline_model_path, ef=True)
    promptedge_model = load_model_with_workdir(args.promptedge_model_path, ef=True)
    baseline_model.eval()
    promptedge_model.eval()
    sentence_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    tasks = load_aqua_tasks_by_id(args.dataset_path, args.task_split_path, task_ids)

    records: List[Dict[str, Any]] = []
    for graph_index, task in enumerate(tasks):
        try:
            record = await run_task_selector_gated_promptedge_async(
                task,
                graph_index,
                baseline_model,
                promptedge_model,
                selector_model,
                signature_priors,
                sentence_model,
                ROLE_DESCRIPTION,
                args,
            )
        except Exception as exc:
            print(f"Error executing R171 task {task.get('task_id')}: {exc}")
            record = {
                "task_id": task.get("task_id"),
                "question": task.get("task"),
                "true_answer": normalize_option(task.get("answer")),
                "predicted_answer": None,
                "raw_response": None,
                "is_solved": False,
                "selected_source": "error",
                "selection_rule": RULE_NAME,
                "baseline_prediction": None,
                "baseline_is_solved": False,
                "promptedge_prediction": None,
                "promptedge_is_solved": False,
                "promptedge_was_run": False,
                "selector_decision": {"selector_action": "error"},
                "promptedge_contract_evidence": {},
                "selector_policy_input": {},
                "fix": False,
                "harm": False,
                "error": str(exc),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        records.append(record)
        write_jsonl(args.output_jsonl, records)
        progress = summarize_records(records)
        print(
            "R171 progress: "
            f"selected={progress['selected_accuracy']} "
            f"baseline={progress['baseline_accuracy']} "
            f"switches={progress['switch_tasks']}"
        )

    prompt_tokens = int(PromptTokens.instance().value)
    completion_tokens = int(CompletionTokens.instance().value)
    assert_valid_evaluation_run(
        records,
        total_tasks=len(tasks),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    audit_labels = {}
    if args.audit_file and os.path.exists(args.audit_file):
        audit_labels = load_audit_labels([args.audit_file])
    summary = summarize_records(
        records,
        cost=Cost.instance().value,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        audit_labels=audit_labels,
        env_keys_loaded=env_keys_loaded,
    )
    summary.update(
        {
            "llm_name": args.llm_name,
            "baseline_model_path": args.baseline_model_path,
            "promptedge_model_path": args.promptedge_model_path,
            "selector_summary_json": args.selector_summary_json,
            "selector_target_rows": args.selector_target_rows,
            "task_ids_requested": task_ids,
            "output_jsonl": args.output_jsonl,
        }
    )
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(summary))
    if args.summary_log_jsonl:
        parent = os.path.dirname(args.summary_log_jsonl)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(args.summary_log_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
