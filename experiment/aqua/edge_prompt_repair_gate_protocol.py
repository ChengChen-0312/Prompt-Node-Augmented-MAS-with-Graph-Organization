import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import mas_framework.agents  # noqa: F401,E402
from datasets.aqua_dataset import aqua_get_predict  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from mas_framework.agents.agent_registry import AgentRegistry  # noqa: E402
from mas_framework.agents.final_decision import (  # noqa: E402
    extract_edge_prompt_repair_candidates,
    select_edge_prompt_repair_answer,
)


RULE_NAME = "r134_edge_prompt_repair_gate_protocol"
CLAIM_BOUNDARY = (
    "implementation/offline repair gate only; no API, accuracy, cost, transfer, or robustness result"
)
DECISION_METHOD = "EdgePromptRepairContractFinalRefer"

DEFAULT_R132_SWITCH_RESULTS = "experiment/aqua/aqua_tail34_r132_deterministic_router_none_switch_results.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r134_edge_prompt_repair_gate_protocol_summary.json"
)
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r134_edge_prompt_repair_gate_protocol.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_jsonl(path: str) -> list[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _record_for_task(path: str, task_id: str) -> Dict[str, Any]:
    for row in _load_jsonl(path):
        if row.get("task_id") == task_id:
            return row
    raise ValueError(f"Missing {task_id} in {path}")


def _spatial_info_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
    spatial: Dict[str, Any] = {}
    for output in record.get("agent_outputs") or []:
        outputs = output.get("outputs") or []
        spatial[str(output.get("node"))] = {
            "role": output.get("role", ""),
            "output": str(outputs[-1]) if outputs else "",
        }
    return spatial


def _repair_spatial(
    confidence: str = "0.93",
    distance_ratio: str = "0.000046",
    include_repair: bool = True,
) -> Dict[str, Any]:
    repair_lines = ""
    if include_repair:
        repair_lines = (
            "REPAIR_OPTION: E\n"
            "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
            f"REPAIR_CONFIDENCE: {confidence}\n"
            f"REPAIR_DISTANCE_RATIO: {distance_ratio}\n"
        )
    return {
        "router": {
            "role": "PN_Router",
            "output": (
                "SUPPORTED_OPTION: NONE\n"
                "BINDING_STATUS: NO_EXACT_OPTION\n"
                f"{repair_lines}"
                "FINAL_EVIDENCE_SUMMARY: exact value is absent; repair edge decides whether to expose E.\n"
            ),
        }
    }


def _agent_response(spatial_info: Dict[str, Any]) -> str:
    agent = AgentRegistry.get(DECISION_METHOD, domain="aqua", llm_name="mock")
    return agent._execute({"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"}, spatial_info, {})


def build_edge_prompt_repair_gate_protocol(
    r132_switch_results: str = DEFAULT_R132_SWITCH_RESULTS,
) -> Dict[str, Any]:
    agent = AgentRegistry.get(DECISION_METHOD, domain="aqua", llm_name="mock")
    explicit_repair_spatial = _repair_spatial()
    missing_repair_spatial = _repair_spatial(include_repair=False)
    low_confidence_spatial = _repair_spatial(confidence="0.50")
    large_distance_spatial = _repair_spatial(distance_ratio="0.2")

    explicit_repair_prediction = _agent_response(explicit_repair_spatial)
    missing_repair_prediction = _agent_response(missing_repair_spatial)
    low_confidence_answer = select_edge_prompt_repair_answer(low_confidence_spatial)
    large_distance_answer = select_edge_prompt_repair_answer(large_distance_spatial)

    r132_task250 = _record_for_task(r132_switch_results, "task_250")
    r132_spatial = _spatial_info_from_record(r132_task250)
    r132_repair_candidates = extract_edge_prompt_repair_candidates(r132_spatial)
    r132_repair_prediction = _agent_response(r132_spatial)

    return {
        "rule": RULE_NAME,
        "implementation_only": True,
        "no_api_run": True,
        "decision_method": DECISION_METHOD,
        "decision_method_registered": agent.agent_name == DECISION_METHOD,
        "explicit_repair_candidate_count": len(
            extract_edge_prompt_repair_candidates(explicit_repair_spatial)
        ),
        "explicit_repair_prediction": explicit_repair_prediction,
        "explicit_repair_parser_prediction": aqua_get_predict(explicit_repair_prediction),
        "missing_repair_prediction": missing_repair_prediction,
        "missing_repair_parser_prediction": aqua_get_predict(missing_repair_prediction),
        "low_confidence_rejected": low_confidence_answer is None,
        "large_distance_rejected": large_distance_answer is None,
        "r132_task250_has_repair_fields": bool(r132_repair_candidates),
        "r132_task250_repair_gate_prediction": r132_repair_prediction,
        "r132_task250_repair_gate_parser_prediction": aqua_get_predict(r132_repair_prediction),
        "broad_api_allowed_next": False,
        "next_protocol": "edge_prompt_repair_field_prompting_presmoke",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R134 Edge-Prompt Repair Gate Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Implementation only: `{summary['implementation_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Decision method: `{summary['decision_method']}`",
            f"- Decision method registered: `{summary['decision_method_registered']}`",
            f"- Explicit repair candidate count: `{summary['explicit_repair_candidate_count']}`",
            f"- Explicit repair prediction: `{summary['explicit_repair_prediction']}`",
            f"- Explicit repair parser prediction: `{summary['explicit_repair_parser_prediction']}`",
            f"- Missing repair parser prediction: `{summary['missing_repair_parser_prediction']}`",
            f"- Low confidence rejected: `{summary['low_confidence_rejected']}`",
            f"- Large distance rejected: `{summary['large_distance_rejected']}`",
            f"- R132 task250 has repair fields: `{summary['r132_task250_has_repair_fields']}`",
            f"- R132 task250 repair-gate parser prediction: `{summary['r132_task250_repair_gate_parser_prediction']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Interpretation",
            "",
            "R134 implements the final-layer side of the edge-prompt repair path. A repair option can be "
            "exposed only when the router output contains explicit repair fields with sufficient confidence "
            "and bounded distance. The existing R132 task250 output has no repair fields, so it remains "
            "abstaining under the repair gate.",
            "",
            "This is not an accuracy result. The next step is to make PN_Verifier/PN_Router emit the repair "
            "fields through edge-prompt instructions, then run only the same four-task pre-smoke.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write R134 edge-prompt repair gate protocol.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_edge_prompt_repair_gate_protocol()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R134 edge-prompt repair gate protocol: "
        f"explicit={summary['explicit_repair_parser_prediction']} "
        f"r132_task250={summary['r132_task250_repair_gate_parser_prediction']} "
        f"broad_api={summary['broad_api_allowed_next']}"
    )


if __name__ == "__main__":
    main()
