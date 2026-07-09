from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r187_promptedge_generated_graph_audit import run_audit


DEFAULT_ARG_MODEL_DIR = "experiment/mmlu/output/mmlu_arg_retrain_r282_e5_observed"
DEFAULT_PROMPTNODE_MODEL_DIR = "experiment/mmlu/output/mmlu_promptnode_retrain_r283_e5_observed"
DEFAULT_ARG_TRAINING_JSON = "experiment/mmlu/res_logs/mmlu_r282_arg_retrain_e5_observed_summary.json"
DEFAULT_PROMPTNODE_TRAINING_JSON = "experiment/mmlu/res_logs/mmlu_r283_promptnode_retrain_e5_observed_summary.json"
DEFAULT_TRANSFER_JSONL = "experiment/mmlu/mmlu_stem_transfer100.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r284_retrained_graph_audit_compare_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r284_retrained_graph_audit_compare_report.md"
DEFAULT_ARG_AUDIT_SUMMARY = "experiment/mmlu/res_logs/mmlu_r284_arg_generated_graph_audit_summary.json"
DEFAULT_PROMPTNODE_AUDIT_SUMMARY = "experiment/mmlu/res_logs/mmlu_r284_promptnode_generated_graph_audit_summary.json"
DEFAULT_ARG_AUDIT_REPORT = "experiment/mmlu/run_logs/mmlu_r284_arg_generated_graph_audit_report.md"
DEFAULT_PROMPTNODE_AUDIT_REPORT = "experiment/mmlu/run_logs/mmlu_r284_promptnode_generated_graph_audit_report.md"
DEFAULT_ARG_DETAILS = "experiment/mmlu/run_logs/mmlu_r284_arg_generated_graph_audit_details.jsonl"
DEFAULT_PROMPTNODE_DETAILS = "experiment/mmlu/run_logs/mmlu_r284_promptnode_generated_graph_audit_details.jsonl"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        f.write(text)


def _rate(rows: List[Dict[str, Any]], key: str) -> float:
    return sum(1 for row in rows if row.get(key)) / len(rows) if rows else 0.0


def _mean(rows: List[Dict[str, Any]], key: str) -> float:
    return sum(float(row.get(key, 0.0)) for row in rows) / len(rows) if rows else 0.0


def _role_counts(rows: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        for role in row.get("roles", []) or []:
            counter[str(role)] += 1
    return dict(sorted(counter.items()))


def summarize_checkpoint(training: Dict[str, Any], details: List[Dict[str, Any]]) -> Dict[str, Any]:
    pn_roles_present = list(training.get("pn_roles_present") or [])
    return {
        "training_run_id": training.get("run_id"),
        "training_role_mapping_size": int(training.get("role_mapping_size", 0)),
        "pn_roles_present": pn_roles_present,
        "tasks_audited": len(details),
        "dag_rate": _rate(details, "is_dag"),
        "any_pn_rate": _rate(details, "has_any_pn"),
        "all_pn_roles_rate": _rate(details, "has_all_pn_roles"),
        "contract_ready_rate": _rate(details, "promptedge_contract_ready"),
        "mean_nodes": _mean(details, "num_nodes"),
        "mean_edges": _mean(details, "num_edges"),
        "role_counts": _role_counts(details),
    }


def summarize_audit_comparison(
    arg_training: Dict[str, Any],
    promptnode_training: Dict[str, Any],
    arg_details: List[Dict[str, Any]],
    promptnode_details: List[Dict[str, Any]],
    run_id: str = "R284",
) -> Dict[str, Any]:
    arg = summarize_checkpoint(arg_training, arg_details)
    promptnode = summarize_checkpoint(promptnode_training, promptnode_details)
    structural_claim_supported = (
        arg["training_role_mapping_size"] == 6
        and not arg["pn_roles_present"]
        and arg["any_pn_rate"] == 0.0
        and arg["dag_rate"] == 1.0
        and promptnode["training_role_mapping_size"] >= 9
        and {"PN_Memory", "PN_Verifier", "PN_Router"}.issubset(
            set(promptnode["pn_roles_present"])
        )
        and promptnode["dag_rate"] == 1.0
        and promptnode["any_pn_rate"] > 0.0
        and promptnode["contract_ready_rate"] >= 0.5
    )
    return {
        "run_id": run_id,
        "title": "MMLU retrained ARG vs PromptNode generated-graph audit",
        "claim_boundary": (
            "No-API generated-graph audit only. This supports structural integration "
            "checks for retrained checkpoints, not answer accuracy or transfer superiority."
        ),
        "no_api": True,
        "broad_api": False,
        "arg": arg,
        "promptnode": promptnode,
        "structural_claim_supported": bool(structural_claim_supported),
        "accuracy_claim_supported": False,
        "transfer_superiority_claim_supported": False,
        "api_evaluation_authorized_next": bool(structural_claim_supported),
        "next_action": (
            "Run matched checkpoint-level MMLU API evaluation on the same transfer split "
            "if structural_claim_supported is true; otherwise continue graph-policy training."
        ),
        "next_goal_audit_due": "R285",
    }


def render_report(summary: Dict[str, Any]) -> str:
    arg = summary["arg"]
    promptnode = summary["promptnode"]
    return "\n".join(
        [
            "# R284 Retrained MMLU Graph Audit Compare",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "| Checkpoint | Train roles | PN roles in train | Tasks | Any PN | Contract ready | Mean nodes | Mean edges |",
            "|---|---:|---|---:|---:|---:|---:|---:|",
            (
                f"| ARG R282 | `{arg['training_role_mapping_size']}` | "
                f"`{arg['pn_roles_present']}` | `{arg['tasks_audited']}` | "
                f"`{arg['any_pn_rate']:.2f}` | `{arg['contract_ready_rate']:.2f}` | "
                f"`{arg['mean_nodes']:.2f}` | `{arg['mean_edges']:.2f}` |"
            ),
            (
                f"| PromptNode R283 | `{promptnode['training_role_mapping_size']}` | "
                f"`{promptnode['pn_roles_present']}` | `{promptnode['tasks_audited']}` | "
                f"`{promptnode['any_pn_rate']:.2f}` | `{promptnode['contract_ready_rate']:.2f}` | "
                f"`{promptnode['mean_nodes']:.2f}` | `{promptnode['mean_edges']:.2f}` |"
            ),
            "",
            "## Claim Gate",
            "",
            f"- Structural claim supported: `{summary['structural_claim_supported']}`",
            f"- Accuracy claim supported: `{summary['accuracy_claim_supported']}`",
            f"- Transfer superiority claim supported: `{summary['transfer_superiority_claim_supported']}`",
            f"- API evaluation authorized next: `{summary['api_evaluation_authorized_next']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
            "## Interpretation",
            "",
            "R284 only verifies whether retrained checkpoints produce the intended graph families. "
            "It deliberately does not use answer labels or API calls.",
            "",
        ]
    )


def run(
    arg_model_dir: str = DEFAULT_ARG_MODEL_DIR,
    promptnode_model_dir: str = DEFAULT_PROMPTNODE_MODEL_DIR,
    arg_training_json: str = DEFAULT_ARG_TRAINING_JSON,
    promptnode_training_json: str = DEFAULT_PROMPTNODE_TRAINING_JSON,
    transfer_jsonl: str = DEFAULT_TRANSFER_JSONL,
    num_tasks: int = 24,
    seed: int = 42,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    arg_audit_summary: str = DEFAULT_ARG_AUDIT_SUMMARY,
    promptnode_audit_summary: str = DEFAULT_PROMPTNODE_AUDIT_SUMMARY,
    arg_audit_report: str = DEFAULT_ARG_AUDIT_REPORT,
    promptnode_audit_report: str = DEFAULT_PROMPTNODE_AUDIT_REPORT,
    arg_details_jsonl: str = DEFAULT_ARG_DETAILS,
    promptnode_details_jsonl: str = DEFAULT_PROMPTNODE_DETAILS,
) -> Dict[str, Any]:
    run_audit(
        model_dir=arg_model_dir,
        transfer_jsonl=transfer_jsonl,
        summary_json=arg_audit_summary,
        report_md=arg_audit_report,
        details_jsonl=arg_details_jsonl,
        num_tasks=num_tasks,
        seed=seed,
        run_id="R284_ARG",
    )
    run_audit(
        model_dir=promptnode_model_dir,
        transfer_jsonl=transfer_jsonl,
        summary_json=promptnode_audit_summary,
        report_md=promptnode_audit_report,
        details_jsonl=promptnode_details_jsonl,
        num_tasks=num_tasks,
        seed=seed,
        run_id="R284_PROMPTNODE",
    )
    summary = summarize_audit_comparison(
        arg_training=_load_json(arg_training_json),
        promptnode_training=_load_json(promptnode_training_json),
        arg_details=_load_jsonl(arg_details_jsonl),
        promptnode_details=_load_jsonl(promptnode_details_jsonl),
        run_id="R284",
    )
    summary.update(
        {
            "arg_model_dir": arg_model_dir,
            "promptnode_model_dir": promptnode_model_dir,
            "transfer_jsonl": transfer_jsonl,
            "num_tasks": num_tasks,
            "seed": seed,
            "arg_details_jsonl": arg_details_jsonl,
            "promptnode_details_jsonl": promptnode_details_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare generated graph structure from retrained MMLU ARG and PromptNode checkpoints."
    )
    parser.add_argument("--arg_model_dir", default=DEFAULT_ARG_MODEL_DIR)
    parser.add_argument("--promptnode_model_dir", default=DEFAULT_PROMPTNODE_MODEL_DIR)
    parser.add_argument("--arg_training_json", default=DEFAULT_ARG_TRAINING_JSON)
    parser.add_argument("--promptnode_training_json", default=DEFAULT_PROMPTNODE_TRAINING_JSON)
    parser.add_argument("--transfer_jsonl", default=DEFAULT_TRANSFER_JSONL)
    parser.add_argument("--num_tasks", type=int, default=24)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--arg_audit_summary", default=DEFAULT_ARG_AUDIT_SUMMARY)
    parser.add_argument("--promptnode_audit_summary", default=DEFAULT_PROMPTNODE_AUDIT_SUMMARY)
    parser.add_argument("--arg_audit_report", default=DEFAULT_ARG_AUDIT_REPORT)
    parser.add_argument("--promptnode_audit_report", default=DEFAULT_PROMPTNODE_AUDIT_REPORT)
    parser.add_argument("--arg_details_jsonl", default=DEFAULT_ARG_DETAILS)
    parser.add_argument("--promptnode_details_jsonl", default=DEFAULT_PROMPTNODE_DETAILS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
