import argparse
import json
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from mas_framework.agents.final_decision import (  # type: ignore
        extract_router_contracts,
        summarize_pn_utility_features,
    )
except ModuleNotFoundError:
    def _extract_contract_field(text: str, field: str) -> str:
        match = re.search(rf"^{field}:\s*(.+)$", text or "", flags=re.I | re.M)
        return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""

    def _extract_final_option(text: str) -> Optional[str]:
        matches = re.findall(r"\bthe\s+answer\s+is\s+([A-E])\b", text or "", flags=re.I)
        if not matches:
            return None
        return matches[-1].upper()

    def extract_router_contracts(spatial_info: Dict[str, Any]) -> List[Dict[str, str]]:
        contracts = []
        for node_id, info in spatial_info.items():
            output = info.get("output", "")
            if info.get("role") != "PN_Router" and "SUPPORTED_OPTION:" not in output:
                continue
            supported_option = _extract_contract_field(output, "SUPPORTED_OPTION").upper()
            binding_status = _extract_contract_field(output, "BINDING_STATUS").upper()
            evidence_summary = _extract_contract_field(output, "FINAL_EVIDENCE_SUMMARY")
            if not any([supported_option, binding_status, evidence_summary]):
                continue
            contracts.append(
                {
                    "node_id": node_id,
                    "role": info.get("role", ""),
                    "supported_option": supported_option,
                    "binding_status": binding_status,
                    "final_evidence_summary": evidence_summary,
                    "raw_output": output,
                }
            )
        return contracts

    def _is_strong_router_contract(contract: Dict[str, str]) -> bool:
        return (
            contract.get("supported_option", "").upper() in {"A", "B", "C", "D", "E"}
            and contract.get("binding_status", "").upper()
            in {"EXACT_MATCH", "EQUIVALENT_FORM", "EQUIVALENT"}
        )

    def extract_direct_option_votes(spatial_info: Dict[str, Any]) -> List[str]:
        votes = []
        for info in spatial_info.values():
            if str(info.get("role", "")).startswith("PN_"):
                continue
            option = _extract_final_option(info.get("output", ""))
            if option:
                votes.append(option)
        return votes

    def summarize_pn_utility_features(spatial_info: Dict[str, Any]) -> Dict[str, Any]:
        direct_votes = extract_direct_option_votes(spatial_info)
        vote_counts = Counter(direct_votes)
        if vote_counts:
            direct_majority_option, direct_majority_count = vote_counts.most_common(1)[0]
        else:
            direct_majority_option, direct_majority_count = None, 0

        router_contracts = extract_router_contracts(spatial_info)
        strong_contracts = [
            contract for contract in router_contracts if _is_strong_router_contract(contract)
        ]
        strong_router_options = []
        for contract in strong_contracts:
            option = contract.get("supported_option", "").upper()
            if option not in strong_router_options:
                strong_router_options.append(option)

        return {
            "direct_votes": direct_votes,
            "direct_vote_counts": dict(vote_counts),
            "direct_valid_vote_count": len(direct_votes),
            "direct_majority_option": direct_majority_option,
            "direct_majority_count": direct_majority_count,
            "router_contract_count": len(router_contracts),
            "strong_router_options": strong_router_options,
            "all_router_contracts_weak": bool(router_contracts) and not strong_contracts,
            "strong_router_conflicts_with_direct_majority": (
                direct_majority_count >= 2
                and bool(strong_router_options)
                and direct_majority_option not in strong_router_options
            ),
        }


VALID_OPTIONS = {"A", "B", "C", "D", "E"}
STRONG_BINDING_STATUS = {"EXACT_MATCH", "EQUIVALENT_FORM", "EQUIVALENT"}
DEFAULT_METHOD_ORDER = [
    "baseline",
    "router",
    "candidate",
    "conservative",
    "calibrated",
]
DEFAULT_CONTRACT_METHOD_KEYS = ["router", "candidate", "conservative", "calibrated"]
PREFIX_FILES = {
    "baseline": "{prefix}_arg_baseline_results.jsonl",
    "router": "{prefix}_pn_router_contract_results.jsonl",
    "candidate": "{prefix}_pn_candidate_select_results.jsonl",
    "conservative": "{prefix}_pn_conservative_router_results.jsonl",
    "calibrated": "{prefix}_pn_calibrated_utility_results.jsonl",
    "ensemble": "{prefix}_pn_result_ensemble_results.jsonl",
}


def normalize_option(value: Any) -> Optional[str]:
    if isinstance(value, str):
        candidate = value.strip().upper()
        if candidate in VALID_OPTIONS:
            return candidate
    return None


def load_jsonl_by_task(path: str) -> Dict[str, Dict[str, Any]]:
    records: Dict[str, Dict[str, Any]] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            records[record["task_id"]] = record
    return records


def graph_has_prompt_node(graph: Any) -> bool:
    if not isinstance(graph, dict):
        return False
    roles = graph.get("roles") or []
    for role in roles:
        role_text = str(role).lower()
        if role_text.startswith("pn_") or "promptnode" in role_text or "prompt node" in role_text:
            return True
    return False


def candidate_graphs_have_prompt_node(record: Dict[str, Any]) -> bool:
    for graph in record.get("candidate_graphs") or []:
        if graph_has_prompt_node(graph):
            return True
    return False


def majority_prediction(predictions: Iterable[Optional[str]]) -> tuple[Optional[str], int]:
    votes = [prediction for prediction in predictions if prediction in VALID_OPTIONS]
    if not votes:
        return None, 0
    counts = Counter(votes)
    prediction, count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
    return prediction, count


def method_predictions_for_task(
    task_id: str,
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
    method_order: Optional[List[str]] = None,
) -> Dict[str, Optional[str]]:
    ensemble_record = result_sets.get("ensemble", {}).get(task_id, {})
    raw_predictions = ensemble_record.get("method_predictions")
    if isinstance(raw_predictions, dict):
        return {
            method: normalize_option(raw_predictions.get(method))
            for method in (method_order or list(raw_predictions.keys()))
        }

    order = method_order or DEFAULT_METHOD_ORDER
    return {
        method: normalize_option(result_sets.get(method, {}).get(task_id, {}).get("predicted_answer"))
        for method in order
    }


def agent_outputs_to_spatial_info(record: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    spatial_info = {}
    for output in record.get("agent_outputs") or []:
        node_id = str(output.get("node", len(spatial_info)))
        outputs = output.get("outputs") or []
        spatial_info[node_id] = {
            "role": output.get("role", ""),
            "output": "\n".join(str(item) for item in outputs),
        }
    return spatial_info


def extract_contract_consensus_features(record: Dict[str, Any]) -> Dict[str, Any]:
    spatial_info = agent_outputs_to_spatial_info(record)
    contracts = extract_router_contracts(spatial_info)
    strong_contracts = [
        contract
        for contract in contracts
        if contract.get("supported_option", "").upper() in VALID_OPTIONS
        and contract.get("binding_status", "").upper() in STRONG_BINDING_STATUS
    ]
    first_strong = strong_contracts[0] if strong_contracts else {}
    utility_features = summarize_pn_utility_features(spatial_info)
    router_option = normalize_option(first_strong.get("supported_option"))
    direct_majority = normalize_option(utility_features.get("direct_majority_option"))

    return {
        "router_option": router_option,
        "router_binding_status": first_strong.get("binding_status", "").upper(),
        "router_contract_count": len(contracts),
        "strong_router_contract_count": len(strong_contracts),
        "direct_majority": direct_majority,
        "direct_majority_count": utility_features.get("direct_majority_count", 0),
        "direct_valid_vote_count": utility_features.get("direct_valid_vote_count", 0),
        "router_matches_direct_majority": (
            router_option in VALID_OPTIONS
            and direct_majority in VALID_OPTIONS
            and router_option == direct_majority
        ),
        "router_conflicts_with_direct_majority": utility_features.get(
            "strong_router_conflicts_with_direct_majority", False
        ),
        "all_router_contracts_weak": utility_features.get("all_router_contracts_weak", False),
    }


def apply_contract_consensus_rule(
    baseline_prediction: Optional[str],
    ensemble_prediction: Optional[str],
    features: Dict[str, Any],
    min_direct_majority: int = 2,
    use_invalid_fallback: bool = True,
) -> tuple[Optional[str], str]:
    baseline_option = normalize_option(baseline_prediction)
    ensemble_option = normalize_option(ensemble_prediction)
    if use_invalid_fallback and baseline_option is None and ensemble_option in VALID_OPTIONS:
        return ensemble_option, "ensemble_invalid"

    router_option = normalize_option(features.get("router_option"))
    if (
        router_option in VALID_OPTIONS
        and baseline_option in VALID_OPTIONS
        and router_option != baseline_option
        and features.get("router_matches_direct_majority")
        and features.get("direct_majority_count", 0) >= min_direct_majority
    ):
        return router_option, "router_contract"
    return baseline_option, "baseline"


def extract_multi_contract_features(
    task_id: str,
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
    method_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    method_keys = method_keys or DEFAULT_CONTRACT_METHOD_KEYS
    method_features = {}
    strong_counts: Counter[str] = Counter()
    direct_consensus_counts: Counter[str] = Counter()

    for method_key in method_keys:
        record = result_sets.get(method_key, {}).get(task_id)
        if not record:
            continue
        features = extract_contract_consensus_features(record)
        method_features[method_key] = features
        router_option = normalize_option(features.get("router_option"))
        if router_option in VALID_OPTIONS:
            strong_counts[router_option] += 1
        if (
            router_option in VALID_OPTIONS
            and features.get("router_matches_direct_majority")
            and features.get("direct_majority_count", 0) >= 2
        ):
            direct_consensus_counts[router_option] += 1

    return {
        "method_features": method_features,
        "strong_option_counts": dict(strong_counts),
        "direct_consensus_counts": dict(direct_consensus_counts),
        "method_keys": method_keys,
    }


def _unique_top_option(counts: Dict[str, int], min_count: int) -> Optional[str]:
    filtered = {option: count for option, count in counts.items() if count >= min_count}
    if not filtered:
        return None
    ordered = sorted(filtered.items(), key=lambda item: (-item[1], item[0]))
    if len(ordered) > 1 and ordered[0][1] == ordered[1][1]:
        return None
    return ordered[0][0]


def apply_multi_contract_union_rule(
    baseline_prediction: Optional[str],
    ensemble_prediction: Optional[str],
    features: Dict[str, Any],
    min_direct_methods: int = 2,
    min_strong_methods: int = 3,
    use_invalid_fallback: bool = True,
) -> tuple[Optional[str], str]:
    baseline_option = normalize_option(baseline_prediction)
    ensemble_option = normalize_option(ensemble_prediction)
    if use_invalid_fallback and baseline_option is None and ensemble_option in VALID_OPTIONS:
        return ensemble_option, "ensemble_invalid"

    candidate_options = []
    direct_option = _unique_top_option(features.get("direct_consensus_counts", {}), min_direct_methods)
    strong_option = _unique_top_option(features.get("strong_option_counts", {}), min_strong_methods)
    if direct_option in VALID_OPTIONS:
        candidate_options.append(direct_option)
    if strong_option in VALID_OPTIONS:
        candidate_options.append(strong_option)

    selected = _unique_top_option(dict(Counter(candidate_options)), 1)
    if selected in VALID_OPTIONS and baseline_option in VALID_OPTIONS and selected != baseline_option:
        return selected, "multi_contract_union"
    return baseline_option, "baseline"


def extract_selector_features(
    task_id: str,
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
) -> Dict[str, Any]:
    baseline_record = result_sets.get("baseline", {}).get(task_id, {})
    ensemble_record = result_sets.get("ensemble", {}).get(task_id, {})
    method_order = ensemble_record.get("method_order") or DEFAULT_METHOD_ORDER
    method_predictions = method_predictions_for_task(task_id, result_sets, method_order)

    baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
    if baseline_prediction is None:
        baseline_prediction = method_predictions.get("baseline")
    ensemble_prediction = normalize_option(ensemble_record.get("predicted_answer"))
    if ensemble_prediction is None:
        ensemble_prediction, _ = majority_prediction(method_predictions.values())

    majority_choice, majority_count = majority_prediction(method_predictions.values())
    pn_methods = [method for method in method_order if method != "baseline"]
    pn_predictions = [method_predictions.get(method) for method in pn_methods]
    pn_majority_choice, pn_majority_count = majority_prediction(pn_predictions)
    pn_supports_ensemble_count = sum(
        1 for method in pn_methods if method_predictions.get(method) == ensemble_prediction
    )
    valid_vote_count = sum(1 for prediction in method_predictions.values() if prediction in VALID_OPTIONS)
    candidate_record = result_sets.get("candidate", {}).get(task_id, {})

    return {
        "baseline_prediction": baseline_prediction,
        "ensemble_prediction": ensemble_prediction,
        "baseline_valid": baseline_prediction in VALID_OPTIONS,
        "ensemble_valid": ensemble_prediction in VALID_OPTIONS,
        "baseline_disagrees_ensemble": (
            baseline_prediction in VALID_OPTIONS
            and ensemble_prediction in VALID_OPTIONS
            and baseline_prediction != ensemble_prediction
        ),
        "majority_prediction": majority_choice,
        "majority_count": majority_count,
        "valid_vote_count": valid_vote_count,
        "pn_majority_prediction": pn_majority_choice,
        "pn_majority_count": pn_majority_count,
        "pn_supports_ensemble_count": pn_supports_ensemble_count,
        "baseline_matches_majority": baseline_prediction == majority_choice,
        "baseline_matches_pn_majority": baseline_prediction == pn_majority_choice,
        "candidate_selected_prompt_node": graph_has_prompt_node(candidate_record.get("generated_graph")),
        "candidate_any_prompt_node": candidate_graphs_have_prompt_node(candidate_record),
        "any_selected_prompt_node": any(
            graph_has_prompt_node(result_sets.get(method, {}).get(task_id, {}).get("generated_graph"))
            for method in pn_methods
        ),
        "method_predictions": method_predictions,
    }


def candidate_rules() -> List[Dict[str, Any]]:
    return [
        {"name": "baseline"},
        {"name": "ensemble_if_baseline_invalid"},
        {"name": "pn_support_ge_4", "min_pn_support": 4},
        {"name": "pn_support_ge_3", "min_pn_support": 3},
        {"name": "majority_ge_4", "min_majority": 4},
        {"name": "majority_ge_3", "min_majority": 3},
        {
            "name": "candidate_pn_and_pn_support_ge_3",
            "min_pn_support": 3,
            "require_candidate_selected_prompt_node": True,
        },
        {
            "name": "candidate_any_pn_and_pn_support_ge_3",
            "min_pn_support": 3,
            "require_candidate_any_prompt_node": True,
        },
    ]


def apply_rule(rule: Dict[str, Any], features: Dict[str, Any]) -> bool:
    if not features.get("ensemble_valid"):
        return False
    if rule["name"] == "baseline":
        return False
    if rule["name"] == "ensemble_if_baseline_invalid":
        return not features.get("baseline_valid")
    if not features.get("baseline_disagrees_ensemble"):
        return False
    if rule.get("require_candidate_selected_prompt_node") and not features.get(
        "candidate_selected_prompt_node"
    ):
        return False
    if rule.get("require_candidate_any_prompt_node") and not features.get("candidate_any_prompt_node"):
        return False
    min_pn_support = rule.get("min_pn_support")
    if min_pn_support is not None:
        return features.get("pn_supports_ensemble_count", 0) >= min_pn_support
    min_majority = rule.get("min_majority")
    if min_majority is not None:
        return features.get("majority_count", 0) >= min_majority
    return False


def selected_prediction_for_record(record: Dict[str, Any], rule: Dict[str, Any]) -> tuple[Optional[str], str]:
    if apply_rule(rule, record["features"]):
        return record.get("ensemble_prediction"), "ensemble"
    return record.get("baseline_prediction"), "baseline"


def train_best_rule(training_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    best_rule: Optional[Dict[str, Any]] = None
    best_score: Optional[tuple[int, int, int]] = None
    for index, rule in enumerate(candidate_rules()):
        solved = 0
        switches = 0
        for record in training_records:
            prediction, source = selected_prediction_for_record(record, rule)
            solved += prediction == record.get("true_answer")
            switches += source == "ensemble"
        score = (solved, -switches, -index)
        if best_score is None or score > best_score:
            best_rule = dict(rule)
            best_score = score
    if best_rule is None:
        raise ValueError("No candidate rules available")
    best_rule["train_solved"] = best_score[0] if best_score else 0
    best_rule["train_total"] = len(training_records)
    return best_rule


def build_training_records(
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
    task_ids: Iterable[str],
) -> List[Dict[str, Any]]:
    records = []
    for task_id in task_ids:
        baseline_record = result_sets.get("baseline", {}).get(task_id, {})
        ensemble_record = result_sets.get("ensemble", {}).get(task_id, {})
        features = extract_selector_features(task_id, result_sets)
        records.append(
            {
                "task_id": task_id,
                "true_answer": baseline_record.get("true_answer") or ensemble_record.get("true_answer"),
                "baseline_prediction": features["baseline_prediction"],
                "ensemble_prediction": features["ensemble_prediction"],
                "features": features,
            }
        )
    return records


def public_selector_features(features: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in features.items() if key != "method_predictions"}


def build_selected_records(
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
    task_ids: Iterable[str],
    rule: Dict[str, Any],
) -> List[Dict[str, Any]]:
    records = []
    for task_id in task_ids:
        baseline_record = result_sets.get("baseline", {}).get(task_id, {})
        ensemble_record = result_sets.get("ensemble", {}).get(task_id, {})
        features = extract_selector_features(task_id, result_sets)
        selected_source = "ensemble" if apply_rule(rule, features) else "baseline"
        selected_prediction = (
            features["ensemble_prediction"]
            if selected_source == "ensemble"
            else features["baseline_prediction"]
        )
        true_answer = baseline_record.get("true_answer") or ensemble_record.get("true_answer")
        records.append(
            {
                "task_id": task_id,
                "question": baseline_record.get("question") or ensemble_record.get("question"),
                "true_answer": true_answer,
                "predicted_answer": selected_prediction,
                "is_solved": selected_prediction == true_answer,
                "selected_source": selected_source,
                "baseline_prediction": features["baseline_prediction"],
                "ensemble_prediction": features["ensemble_prediction"],
                "selector_rule": rule["name"],
                "selector_features": public_selector_features(features),
                "method_predictions": features["method_predictions"],
            }
        )
    return records


def build_contract_consensus_records(
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
    task_ids: Iterable[str],
    method_key: str = "router",
    min_direct_majority: int = 2,
    use_invalid_fallback: bool = True,
) -> List[Dict[str, Any]]:
    records = []
    for task_id in task_ids:
        baseline_record = result_sets.get("baseline", {}).get(task_id, {})
        ensemble_record = result_sets.get("ensemble", {}).get(task_id, {})
        method_record = result_sets.get(method_key, {}).get(task_id, {})
        baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
        ensemble_prediction = normalize_option(ensemble_record.get("predicted_answer"))
        features = extract_contract_consensus_features(method_record)
        selected_prediction, selected_source = apply_contract_consensus_rule(
            baseline_prediction,
            ensemble_prediction,
            features,
            min_direct_majority=min_direct_majority,
            use_invalid_fallback=use_invalid_fallback,
        )
        true_answer = baseline_record.get("true_answer") or ensemble_record.get("true_answer")
        records.append(
            {
                "task_id": task_id,
                "question": baseline_record.get("question") or ensemble_record.get("question"),
                "true_answer": true_answer,
                "predicted_answer": selected_prediction,
                "is_solved": selected_prediction == true_answer,
                "selected_source": selected_source,
                "baseline_prediction": baseline_prediction,
                "ensemble_prediction": ensemble_prediction,
                "selector_rule": "contract_consensus",
                "selector_method_key": method_key,
                "selector_features": features,
            }
        )
    return records


def build_multi_contract_union_records(
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
    task_ids: Iterable[str],
    method_keys: Optional[List[str]] = None,
    min_direct_methods: int = 2,
    min_strong_methods: int = 3,
    use_invalid_fallback: bool = True,
) -> List[Dict[str, Any]]:
    records = []
    for task_id in task_ids:
        baseline_record = result_sets.get("baseline", {}).get(task_id, {})
        ensemble_record = result_sets.get("ensemble", {}).get(task_id, {})
        baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
        ensemble_prediction = normalize_option(ensemble_record.get("predicted_answer"))
        features = extract_multi_contract_features(task_id, result_sets, method_keys)
        selected_prediction, selected_source = apply_multi_contract_union_rule(
            baseline_prediction,
            ensemble_prediction,
            features,
            min_direct_methods=min_direct_methods,
            min_strong_methods=min_strong_methods,
            use_invalid_fallback=use_invalid_fallback,
        )
        true_answer = baseline_record.get("true_answer") or ensemble_record.get("true_answer")
        records.append(
            {
                "task_id": task_id,
                "question": baseline_record.get("question") or ensemble_record.get("question"),
                "true_answer": true_answer,
                "predicted_answer": selected_prediction,
                "is_solved": selected_prediction == true_answer,
                "selected_source": selected_source,
                "baseline_prediction": baseline_prediction,
                "ensemble_prediction": ensemble_prediction,
                "selector_rule": "multi_contract_union",
                "selector_features": features,
            }
        )
    return records


def summarize_records(records: List[Dict[str, Any]], rule: Dict[str, Any]) -> Dict[str, Any]:
    total = len(records)
    solved = sum(1 for record in records if record["is_solved"])
    switches = sum(1 for record in records if record["selected_source"] == "ensemble")
    baseline_solved = sum(
        1 for record in records if record["baseline_prediction"] == record.get("true_answer")
    )
    ensemble_solved = sum(
        1 for record in records if record["ensemble_prediction"] == record.get("true_answer")
    )
    fixes = sum(
        1
        for record in records
        if record["baseline_prediction"] != record.get("true_answer") and record["is_solved"]
    )
    harms = sum(
        1
        for record in records
        if record["baseline_prediction"] == record.get("true_answer") and not record["is_solved"]
    )
    return {
        "total_tasks": total,
        "solved_tasks": solved,
        "pass_at_1": solved / total * 100 if total else 0.0,
        "baseline_solved_tasks": baseline_solved,
        "baseline_pass_at_1": baseline_solved / total * 100 if total else 0.0,
        "ensemble_solved_tasks": ensemble_solved,
        "ensemble_pass_at_1": ensemble_solved / total * 100 if total else 0.0,
        "delta_vs_baseline": solved - baseline_solved,
        "delta_vs_ensemble": solved - ensemble_solved,
        "fixes_vs_baseline": fixes,
        "harms_vs_baseline": harms,
        "ensemble_switches": switches,
        "non_baseline_switches": sum(
            1 for record in records if record.get("selected_source") != "baseline"
        ),
        "rule": rule,
    }


def load_prefix_result_sets(prefix: str, base_dir: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
    result_sets = {}
    for method, template in PREFIX_FILES.items():
        path = os.path.join(base_dir, template.format(prefix=prefix))
        if os.path.exists(path):
            result_sets[method] = load_jsonl_by_task(path)
    missing = [method for method in ("baseline", "ensemble") if method not in result_sets]
    if missing:
        raise FileNotFoundError(f"Missing required result files for {prefix}: {', '.join(missing)}")
    return result_sets


def common_task_ids(result_sets: Dict[str, Dict[str, Dict[str, Any]]]) -> List[str]:
    reference = result_sets["baseline"]
    return [task_id for task_id in reference if task_id in result_sets["ensemble"]]


def write_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and replay an offline AQuA PN utility selector.")
    parser.add_argument(
        "--selector",
        choices=["learned_rule", "contract_consensus", "multi_contract_union"],
        default="learned_rule",
    )
    parser.add_argument("--train-prefix")
    parser.add_argument("--test-prefix", required=True)
    parser.add_argument("--base-dir", default=os.path.dirname(__file__))
    parser.add_argument("--pn-method", choices=["router", "candidate", "conservative", "calibrated"], default="router")
    parser.add_argument("--min-direct-majority", type=int, default=2)
    parser.add_argument("--min-direct-methods", type=int, default=2)
    parser.add_argument("--min-strong-methods", type=int, default=3)
    parser.add_argument("--no-invalid-fallback", action="store_true")
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--summary-file", required=True)
    args = parser.parse_args()

    test_sets = load_prefix_result_sets(args.test_prefix, args.base_dir)
    if args.selector == "contract_consensus":
        rule = {
            "name": "contract_consensus",
            "method_key": args.pn_method,
            "min_direct_majority": args.min_direct_majority,
            "use_invalid_fallback": not args.no_invalid_fallback,
        }
        selected_records = build_contract_consensus_records(
            test_sets,
            common_task_ids(test_sets),
            method_key=args.pn_method,
            min_direct_majority=args.min_direct_majority,
            use_invalid_fallback=not args.no_invalid_fallback,
        )
    elif args.selector == "multi_contract_union":
        rule = {
            "name": "multi_contract_union",
            "method_keys": DEFAULT_CONTRACT_METHOD_KEYS,
            "min_direct_methods": args.min_direct_methods,
            "min_strong_methods": args.min_strong_methods,
            "use_invalid_fallback": not args.no_invalid_fallback,
        }
        selected_records = build_multi_contract_union_records(
            test_sets,
            common_task_ids(test_sets),
            method_keys=DEFAULT_CONTRACT_METHOD_KEYS,
            min_direct_methods=args.min_direct_methods,
            min_strong_methods=args.min_strong_methods,
            use_invalid_fallback=not args.no_invalid_fallback,
        )
    else:
        if not args.train_prefix:
            raise ValueError("--train-prefix is required for --selector learned_rule")
        train_sets = load_prefix_result_sets(args.train_prefix, args.base_dir)
        train_records = build_training_records(train_sets, common_task_ids(train_sets))
        rule = train_best_rule(train_records)
        selected_records = build_selected_records(test_sets, common_task_ids(test_sets), rule)
    summary = summarize_records(selected_records, rule)
    summary["selector"] = args.selector
    summary["train_prefix"] = args.train_prefix
    summary["test_prefix"] = args.test_prefix
    summary["output_file"] = args.output_file

    write_jsonl(args.output_file, selected_records)
    write_json(args.summary_file, summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
