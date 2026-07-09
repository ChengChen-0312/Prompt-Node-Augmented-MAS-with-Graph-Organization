import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import mas_framework.agents  # noqa: E402,F401
from datasets.aqua_dataset import aqua_get_predict  # noqa: E402
from mas_framework.agents.agent_registry import AgentRegistry  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r131_deterministic_router_none_guard_protocol"
CLAIM_BOUNDARY = "implementation and offline guard protocol only; no API, cost, or accuracy result"

DECISION_METHOD = "DeterministicRouterContractFinalRefer"
DEFAULT_R129_JSONL = "experiment/aqua/aqua_tail34_r129_task250_router_none_failure_diagnosis.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r131_deterministic_router_none_guard_protocol.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r131_deterministic_router_none_guard_protocol_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r131_deterministic_router_none_guard_protocol.md"
)


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _ratio(count: int, total: int) -> str:
    return f"{int(count)}/{int(total)}"


def _terminal_router_spatial_info(row: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    return {
        "router": {
            "role": "PN_Router",
            "output": row.get("router_text") or "",
        }
    }


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_deterministic_router_none_guard_protocol(
    r129_jsonl: str = DEFAULT_R129_JSONL,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    agent = AgentRegistry.get(DECISION_METHOD, domain="aqua", llm_name="mock")
    diagnosis_rows = _load_jsonl(r129_jsonl)
    rows: List[Dict[str, Any]] = []
    for row in diagnosis_rows:
        raw_response = agent._execute(
            {"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"},
            _terminal_router_spatial_info(row),
            {},
        )
        prediction = aqua_get_predict(raw_response)
        prevents_forced_option = (
            row.get("router_none_no_exact")
            and row.get("final_layer_selected_option_after_router_none")
            and prediction not in {"A", "B", "C", "D", "E"}
        )
        rows.append(
            {
                "run_name": row.get("run_name"),
                "task_id": row.get("task_id"),
                "source_prediction": row.get("predicted_answer"),
                "source_router_supported_option": row.get("router_supported_option"),
                "source_router_binding_status": row.get("router_binding_status"),
                "guard_raw_response": raw_response,
                "guard_prediction": prediction,
                "prevents_forced_option_after_router_none": bool(prevents_forced_option),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    total = len(rows)
    prevented = sum(1 for row in rows if row["prevents_forced_option_after_router_none"])
    abstained = sum(1 for row in rows if row["guard_prediction"] not in {"A", "B", "C", "D", "E"})
    registered = AgentRegistry.get(DECISION_METHOD, domain="aqua", llm_name="mock").agent_name == DECISION_METHOD
    summary = {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "implementation_only": True,
        "no_api_run": True,
        "decision_method": DECISION_METHOD,
        "decision_method_registered": registered,
        "router_none_terminal_guard_predictions": _ratio(abstained, total),
        "forced_option_after_router_none_prevented": _ratio(prevented, total),
        "parser_prediction_for_abstain": aqua_get_predict("no valid option is supported"),
        "r129_source": r129_jsonl,
        "broad_api_allowed_next": False,
        "same_four_task_smoke_allowed_next": True,
        "next_protocol": "same_four_task_deterministic_router_none_smoke",
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return rows, summary


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{run}` | `{src}` | `{guard}` | `{raw}` | `{prevented}` |".format(
            run=row["run_name"],
            src=row["source_prediction"],
            guard=row["guard_prediction"],
            raw=row["guard_raw_response"],
            prevented=row["prevents_forced_option_after_router_none"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R131 Deterministic Router-NONE Guard Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Decision method: `{summary['decision_method']}`",
            f"- Decision method registered: `{summary['decision_method_registered']}`",
            f"- Implementation only: `{summary['implementation_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Router-NONE terminal guard predictions: `{summary['router_none_terminal_guard_predictions']}`",
            f"- Forced option after router NONE prevented: `{summary['forced_option_after_router_none_prevented']}`",
            f"- Parser prediction for abstain: `{summary['parser_prediction_for_abstain']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Same-four-task smoke allowed next: `{summary['same_four_task_smoke_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "| Run | Source prediction | Guard prediction | Guard raw response | Prevented forced option |",
            "| --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R131 implements a deterministic final decision method for the R129 failure mode. When the "
            "terminal PN_Router contract abstains with `NONE/NO_EXACT_OPTION` and no direct majority is "
            "available, the final node returns a lower-case abstention string instead of any A-E label. "
            "This prevents the AQuA parser from extracting a false option from `NONE`. It is an offline "
            "implementation/protocol result; the next step is only the same four-task smoke, not broad "
            "tail34 or transfer.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write R131 deterministic router-NONE guard protocol.")
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows, summary = build_deterministic_router_none_guard_protocol()
    write_jsonl(args.output_jsonl, rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R131 deterministic router-NONE guard protocol: "
        f"prevented={summary['forced_option_after_router_none_prevented']} "
        f"smoke_next={summary['same_four_task_smoke_allowed_next']}"
    )


if __name__ == "__main__":
    main()
