import argparse
import asyncio
import datetime
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

from sentence_transformers import SentenceTransformer


os.environ["TOKENIZERS_PARALLELISM"] = "false"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AQUA_DIR = os.path.dirname(__file__)
for path in (REPO_ROOT, AQUA_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from experiment.aqua.aqua_prompt_set import ROLE_DESCRIPTION  # noqa: E402
from experiment.aqua.contract_ablation_analysis import load_audit_labels  # noqa: E402
from experiment.aqua.contract_graph_objective import (  # noqa: E402
    score_contract_features,
    select_objective_guided_prediction,
)
from experiment.aqua.evaluate_aqua import (  # noqa: E402
    assert_llm_environment_ready,
    assert_valid_evaluation_run,
)
from experiment.aqua.evaluate_selective_promptnode import (  # noqa: E402
    load_aqua_tasks,
    load_model_with_workdir,
    run_graph_record,
)
from experiment.aqua.finetune_aqua import setup_environment  # noqa: E402
from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.objective_safety_proxy_rule_learner import (  # noqa: E402
    FORBIDDEN_PROXY_INPUT_FIELDS,
    candidate_rules,
)
from experiment.aqua.offline_utility_selector import (  # noqa: E402
    extract_contract_consensus_features,
    graph_has_prompt_node,
    normalize_option,
)
from experiment.aqua.selective_multiview_trigger import ratio_text, write_jsonl  # noqa: E402
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens  # noqa: E402

import mas_framework.agents.final_decision  # noqa: E402,F401
import mas_framework.prompt.AQuA_prompt_set  # noqa: E402,F401


RULE_NAME = "r119_lightweight_calibrated_smoke_runner"
PROBE_PROTOCOL = "calibrated_single_view_probe"
CLAIM_BOUNDARY = (
    "four-task prospective calibrated-probe smoke only; "
    "not broad held-out accuracy or SCI-ready claim"
)

DEFAULT_ENV_FILE = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env"
DEFAULT_DATASET_PATH = "datasets/AQuA/AQuA.jsonl"
DEFAULT_TASK_SPLIT_PATH = "experiment/aqua/task_split_aqua_tail34.json"
DEFAULT_AUDIT_FILE = "experiment/aqua/aqua_tail34_option_binding_audit.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r119_lightweight_calibrated_smoke_results.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r119_lightweight_calibrated_smoke_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r119_lightweight_calibrated_smoke_report.md"
)
DEFAULT_SUMMARY_LOG_JSONL = (
    "experiment/aqua/res_logs/aqua_tail34_r119_lightweight_calibrated_smoke_summary.jsonl"
)

CALIBRATED_DECISION_METHOD = "CalibratedPNUtilityFinalRefer"
REGRESSION_TASK_IDS = ["task_8", "task_108", "task_188", "task_250"]
LEARNED_RULE_NAME = "diff_and_top_score_ge_3_or_split"
FORBIDDEN_POLICY_INPUT_FIELDS = FORBIDDEN_PROXY_INPUT_FIELDS


def _round_cost(value: float) -> float:
    return round(float(value or 0.0), 6)


def load_env_file(path: Optional[str]) -> List[str]:
    if not path:
        return []
    abs_path = _repo_path(path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Env file not found: {abs_path}")
    loaded_keys: List[str] = []
    with open(abs_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if not key:
                continue
            os.environ[key] = value
            loaded_keys.append(key)
    return loaded_keys


def refresh_gpt_chat_env() -> None:
    import mas_framework.llm.gpt_chat as gpt_chat

    gpt_chat.MINE_BASE_URL = os.getenv("BASE_URL", "").strip() or None
    gpt_chat.MINE_API_KEY = (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()


def _proxy_rule_fn(rule_name: str = LEARNED_RULE_NAME):
    for name, fn, _complexity in candidate_rules():
        if name == rule_name:
            return fn
    raise ValueError(f"Unknown proxy rule: {rule_name}")


def proxy_action_for_policy_input(
    policy_input: Dict[str, Any],
    learned_rule: str = LEARNED_RULE_NAME,
) -> str:
    return "switch_to_objective" if _proxy_rule_fn(learned_rule)(policy_input) else "fallback_to_arg"


def ranked_calibrated_variant(calibrated_record: Dict[str, Any]) -> Dict[str, Any]:
    features = extract_contract_consensus_features(calibrated_record)
    has_prompt_node_graph = graph_has_prompt_node(calibrated_record.get("generated_graph"))
    score = score_contract_features(features, has_prompt_node_graph=has_prompt_node_graph)
    return {
        "method_key": "calibrated",
        "method_index": 0,
        "score": score["score"],
        "score_components": score["components"],
        "router_option": features.get("router_option"),
        "direct_majority": features.get("direct_majority"),
        "router_matches_direct_majority": features.get("router_matches_direct_majority"),
        "strong_router_contract_count": features.get("strong_router_contract_count", 0),
        "has_prompt_node_graph": has_prompt_node_graph,
        "predicted_answer": normalize_option(calibrated_record.get("predicted_answer")),
    }


def policy_input_from_live_records(
    baseline_record: Dict[str, Any],
    calibrated_record: Dict[str, Any],
    ranked_variant: Dict[str, Any],
) -> Dict[str, Any]:
    baseline_features = extract_contract_consensus_features(baseline_record)
    baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
    selected_prediction, selected_source = select_objective_guided_prediction(
        baseline_prediction,
        [ranked_variant],
        min_top_score=1,
        min_score_margin=0,
    )
    direct_valid = int(baseline_features.get("direct_valid_vote_count") or 0)
    direct_majority = int(baseline_features.get("direct_majority_count") or 0)
    return {
        "baseline_prediction": baseline_prediction,
        "objective_prediction": selected_prediction,
        "objective_prediction_differs_from_baseline": selected_prediction != baseline_prediction,
        "objective_selected_source": selected_source,
        "objective_top_score": int(ranked_variant.get("score") or 0),
        "baseline_direct_majority": baseline_features.get("direct_majority"),
        "baseline_direct_majority_count": direct_majority,
        "baseline_direct_valid_vote_count": direct_valid,
        "baseline_direct_votes_split": direct_valid > direct_majority,
        "calibrated_prediction": normalize_option(calibrated_record.get("predicted_answer")),
    }


def build_calibrated_probe_record(
    baseline_record: Dict[str, Any],
    calibrated_record: Dict[str, Any],
    learned_rule: str = LEARNED_RULE_NAME,
) -> Dict[str, Any]:
    ranked_variant = ranked_calibrated_variant(calibrated_record)
    policy_input = policy_input_from_live_records(
        baseline_record,
        calibrated_record,
        ranked_variant,
    )
    proxy_action = proxy_action_for_policy_input(policy_input, learned_rule=learned_rule)
    baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
    calibrated_prediction = normalize_option(calibrated_record.get("predicted_answer"))
    true_answer = normalize_option(
        baseline_record.get("true_answer") or calibrated_record.get("true_answer")
    )
    if proxy_action == "switch_to_objective":
        selected_prediction = policy_input["objective_prediction"]
        selected_source = "calibrated_probe"
        selected_method = "calibrated"
    else:
        selected_prediction = baseline_prediction
        selected_source = "baseline"
        selected_method = None
    baseline_is_solved = baseline_prediction == true_answer
    calibrated_is_solved = calibrated_prediction == true_answer
    is_solved = selected_prediction == true_answer
    return {
        "task_id": baseline_record.get("task_id") or calibrated_record.get("task_id"),
        "question": baseline_record.get("question") or calibrated_record.get("question"),
        "true_answer": true_answer,
        "predicted_answer": selected_prediction,
        "raw_response": (
            calibrated_record.get("raw_response")
            if selected_source == "calibrated_probe"
            else baseline_record.get("raw_response")
        ),
        "is_solved": is_solved,
        "baseline_prediction": baseline_prediction,
        "calibrated_prediction": calibrated_prediction,
        "baseline_is_solved": baseline_is_solved,
        "calibrated_is_solved": calibrated_is_solved,
        "selected_source": selected_source,
        "selected_method": selected_method,
        "proxy_action": proxy_action,
        "learned_rule": learned_rule,
        "probe_protocol": PROBE_PROTOCOL,
        "promptnode_view_count": 1,
        "view_predictions": {"calibrated": calibrated_prediction},
        "ranked_variants": [ranked_variant],
        "top_score": int(ranked_variant.get("score") or 0),
        "policy_input": policy_input,
        "policy_input_field_violations": len(FORBIDDEN_PROXY_INPUT_FIELDS.intersection(policy_input)),
        "baseline_record": baseline_record,
        "calibrated_record": calibrated_record,
        "fix": (not baseline_is_solved) and is_solved,
        "harm": baseline_is_solved and not is_solved,
        "calibrated_harm": baseline_is_solved and not calibrated_is_solved,
    }


async def run_task_calibrated_probe_async(
    task: Dict[str, Any],
    baseline_model,
    promptnode_model,
    sentence_model: SentenceTransformer,
    role_constraints_dict: Dict[str, str],
    args: argparse.Namespace,
) -> Dict[str, Any]:
    graph_index = int(task.get("graph_index", 0))
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
    calibrated_record = await run_graph_record(
        task,
        promptnode_model,
        sentence_model,
        role_constraints_dict,
        graph_index,
        llm_name=args.llm_name,
        decision_method=CALIBRATED_DECISION_METHOD,
        prompt_node_policy="none",
        prompt_node_topology_policy=args.prompt_node_topology_policy,
        decision_exposure_policy="auto",
        num_candidate_graphs=1,
    )
    return build_calibrated_probe_record(
        baseline_record,
        calibrated_record,
        learned_rule=args.learned_rule,
    )


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


def _audit_split_counts(rows: Sequence[Dict[str, Any]], audit_labels: Dict[str, str]) -> Dict[str, Any]:
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
        "clean_recovery_tasks": [
            row["task_id"] for row in clean_rows if row.get("fix")
        ],
        "clean_harm_tasks": [
            row["task_id"] for row in clean_rows if row.get("harm")
        ],
    }


def build_calibrated_smoke_summary(
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
    calibrated_solved = sum(1 for row in rows if row.get("calibrated_is_solved"))
    fixes = [row for row in rows if row.get("fix")]
    harms = [row for row in rows if row.get("harm")]
    summary = {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "probe_protocol": PROBE_PROTOCOL,
        "learned_rule": LEARNED_RULE_NAME,
        "regression_tasks": list(REGRESSION_TASK_IDS),
        "total_tasks": total,
        "selected_solved_tasks": selected_solved,
        "baseline_solved_tasks": baseline_solved,
        "calibrated_solved_tasks": calibrated_solved,
        "selected_accuracy": ratio_text(selected_solved, total),
        "baseline_accuracy": ratio_text(baseline_solved, total),
        "calibrated_accuracy": ratio_text(calibrated_solved, total),
        "delta_vs_baseline": selected_solved - baseline_solved,
        "switch_tasks": [
            row["task_id"] for row in rows if row.get("selected_source") == "calibrated_probe"
        ],
        "fallback_tasks": [
            row["task_id"] for row in rows if row.get("selected_source") == "baseline"
        ],
        "fix_tasks": [row["task_id"] for row in fixes],
        "harm_tasks": [row["task_id"] for row in harms],
        "fix_harm": f"{len(fixes)}/{len(harms)}",
        "suppressed_calibrated_harm_tasks": [
            row["task_id"]
            for row in rows
            if row.get("calibrated_harm") and row.get("selected_source") == "baseline"
        ],
        "policy_input_field_violations": sum(
            int(row.get("policy_input_field_violations") or 0) for row in rows
        ),
        "max_promptnode_views_per_task": max(
            [int(row.get("promptnode_view_count") or 0) for row in rows] or [0]
        ),
        "cost": _round_cost(cost),
        "prompt_tokens": int(prompt_tokens or 0),
        "completion_tokens": int(completion_tokens or 0),
        "env_keys_loaded": sorted(set(env_keys_loaded or [])),
        "broad_heldout_claim_ready": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "rows": list(rows),
    }
    if audit_labels:
        summary.update(_audit_split_counts(rows, audit_labels))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{base}` | `{cal}` | `{action}` | `{selected}` | `{truth}` | `{score}` | `{fix}` | `{harm}` |".format(
            task=row.get("task_id"),
            base=row.get("baseline_prediction"),
            cal=row.get("calibrated_prediction"),
            action=row.get("proxy_action"),
            selected=row.get("predicted_answer"),
            truth=row.get("true_answer"),
            score=row.get("top_score"),
            fix=row.get("fix"),
            harm=row.get("harm"),
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R119 Lightweight Calibrated Probe Smoke",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Probe protocol: `{summary['probe_protocol']}`",
            f"- Learned rule: `{summary['learned_rule']}`",
            f"- Tasks: `{summary['total_tasks']}`",
            f"- Selected accuracy: `{summary['selected_accuracy']}`",
            f"- ARG baseline accuracy: `{summary['baseline_accuracy']}`",
            f"- Calibrated-only accuracy: `{summary['calibrated_accuracy']}`",
            f"- Delta vs ARG baseline: `{summary['delta_vs_baseline']:+d}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Suppressed calibrated harms: `{summary['suppressed_calibrated_harm_tasks']}`",
            f"- Fix/Harm: `{summary['fix_harm']}`",
            f"- Max PromptNode views per task: `{summary['max_promptnode_views_per_task']}`",
            f"- Policy-input violations: `{summary['policy_input_field_violations']}`",
            f"- Cost: `${summary['cost']:.6f}`",
            f"- Prompt tokens: `{summary['prompt_tokens']}`",
            f"- Completion tokens: `{summary['completion_tokens']}`",
            "",
            "| Task | ARG | Calibrated | Proxy action | Selected | Truth | Top score | Fix | Harm |",
            "| --- | --- | --- | --- | --- | --- | ---: | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R119 is the prospective smoke counterpart to R118. It runs one calibrated PromptNode view "
            "per regression task and applies the R113 non-leaky proxy rule. Passing this smoke can justify "
            "a larger measured run; it cannot by itself support a broad held-out or SCI-ready accuracy claim.",
            "",
        ]
    )


def _absolute(path: Optional[str]) -> Optional[str]:
    if path is None:
        return None
    return path if os.path.isabs(path) else os.path.abspath(os.path.join(REPO_ROOT, path))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run R119 calibrated single-view PromptNode smoke.")
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--baseline-model-path", required=True)
    parser.add_argument("--promptnode-model-path", required=True)
    parser.add_argument("--dataset-path", default=DEFAULT_DATASET_PATH)
    parser.add_argument("--task-split-path", default=DEFAULT_TASK_SPLIT_PATH)
    parser.add_argument("--task-ids", default=",".join(REGRESSION_TASK_IDS))
    parser.add_argument("--llm-name", default="gpt-4o-2024-08-06")
    parser.add_argument("--baseline-decision-method", default="FinalRefer")
    parser.add_argument("--baseline-num-candidate-graphs", type=int, default=1)
    parser.add_argument("--prompt-node-topology-policy", default="canonicalize_generated")
    parser.add_argument("--learned-rule", default=LEARNED_RULE_NAME)
    parser.add_argument("--audit-file", default=DEFAULT_AUDIT_FILE)
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--summary-log-jsonl", default=DEFAULT_SUMMARY_LOG_JSONL)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def absolutize_args(args: argparse.Namespace) -> argparse.Namespace:
    for attr in (
        "baseline_model_path",
        "promptnode_model_path",
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
    env_keys_loaded = load_env_file(args.env_file)
    refresh_gpt_chat_env()
    assert_llm_environment_ready(args.llm_name)
    setup_environment(42)
    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    task_ids = parse_task_ids(args.task_ids)
    tasks = load_aqua_tasks_by_id(args.dataset_path, args.task_split_path, task_ids)
    print(
        "Loaded R119 calibrated smoke tasks: "
        f"{[task['task_id'] for task in tasks]} with env keys {sorted(set(env_keys_loaded))}"
    )
    print("Loading baseline and PromptNode models...")
    baseline_model = load_model_with_workdir(args.baseline_model_path, ef=True)
    promptnode_model = load_model_with_workdir(args.promptnode_model_path, ef=True)
    baseline_model.eval()
    promptnode_model.eval()
    sentence_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    records: List[Dict[str, Any]] = []
    for task in tasks:
        try:
            record = await run_task_calibrated_probe_async(
                task,
                baseline_model,
                promptnode_model,
                sentence_model,
                ROLE_DESCRIPTION,
                args,
            )
        except Exception as exc:
            print(f"Error executing R119 task {task.get('task_id')}: {exc}")
            record = {
                "task_id": task.get("task_id"),
                "question": task.get("task"),
                "true_answer": normalize_option(task.get("answer")),
                "predicted_answer": None,
                "raw_response": None,
                "is_solved": False,
                "baseline_prediction": None,
                "calibrated_prediction": None,
                "baseline_is_solved": False,
                "calibrated_is_solved": False,
                "selected_source": "error",
                "selected_method": None,
                "proxy_action": "error",
                "learned_rule": args.learned_rule,
                "probe_protocol": PROBE_PROTOCOL,
                "promptnode_view_count": 0,
                "view_predictions": {"calibrated": None},
                "ranked_variants": [],
                "top_score": None,
                "policy_input": {},
                "policy_input_field_violations": 0,
                "fix": False,
                "harm": False,
                "calibrated_harm": False,
                "error": str(exc),
            }
        records.append(record)
        write_jsonl(args.output_jsonl, records)
        current = build_calibrated_smoke_summary(records)
        print(
            "R119 progress: "
            f"{current['selected_accuracy']} baseline={current['baseline_accuracy']} "
            f"switches={current['switch_tasks']}"
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
    summary = build_calibrated_smoke_summary(
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
            "promptnode_model_path": args.promptnode_model_path,
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
