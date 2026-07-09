import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r161_bounded_mmlu_checkpoint_build_execution"
CLAIM_BOUNDARY = (
    "bounded MMLU checkpoint build execution only; this run creates compatible "
    "MMLU checkpoint artifacts and graph-training data but does not evaluate "
    "downstream MMLU transfer accuracy, AQuA accuracy, robustness, or SCI-Q2 readiness"
)

DEFAULT_LOG_PATH = "experiment/mmlu/run_logs/mmlu_r161_checkpoint_build.log"
DEFAULT_COLD_START_DIR = "experiment/ColdStartData_mmlu"
DEFAULT_FINETUNE_DATA_DIR = "experiment/FinetuneData_mmlu"
DEFAULT_MODEL_OUTPUT_DIR = "experiment/mmlu/output/mmlu_arg_base_model_r159"
DEFAULT_SUMMARY_JSON = (
    "experiment/mmlu/res_logs/mmlu_r161_bounded_checkpoint_build_execution_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/mmlu/run_logs/mmlu_r161_bounded_checkpoint_build_execution_report.md"
)

LLM_NAME = "gpt-4o-2024-08-06"
NUM_ITERATIONS = 10
BATCH_SIZE = 4


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _read_text(path: str) -> str:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return f.read()


def _count_pt_files(path: str) -> int:
    root = _repo_path(path)
    if not os.path.isdir(root):
        return 0
    return sum(1 for name in os.listdir(root) if name.endswith(".pt"))


def _count_matching_files(path: str, pattern: str) -> int:
    root = _repo_path(path)
    regex = re.compile(pattern)
    if not os.path.isdir(root):
        return 0
    return sum(1 for name in os.listdir(root) if regex.search(name))


def _parse_training_completed(text: str) -> List[Dict[str, Any]]:
    matches = re.findall(
        r"Training completed\. Best model at Epoch (\d+), Validation loss: ([0-9.]+)",
        text,
    )
    return [
        {"best_epoch": int(epoch), "best_validation_loss": float(loss)}
        for epoch, loss in matches
    ]


def _parse_stage2_counts(text: str) -> Tuple[int, int]:
    pruned = re.search(r"Stage 2a complete: (\d+) pruned graphs saved\.", text)
    replay = re.search(r"Copying replay data:.*?100%.*?\|\s*(\d+)/(\d+)", text)
    return int(pruned.group(1)) if pruned else 0, int(replay.group(1)) if replay else 0


def _parse_topology_results(text: str) -> List[Dict[str, Any]]:
    rows = []
    for match in re.finditer(
        r"Accuracy: ([0-9.]+)% \((\d+)/(\d+)\)\nFinished ([A-Za-z]+-\d+), accuracy: ([0-9.]+)%",
        text,
    ):
        rows.append(
            {
                "config": match.group(4),
                "accuracy_percent": float(match.group(1)),
                "correct": int(match.group(2)),
                "total": int(match.group(3)),
                "reported_ratio_percent_bug": float(match.group(5)),
            }
        )
    return rows


def _parse_stage3_metrics(text: str, completed: List[Dict[str, Any]]) -> Dict[str, Any]:
    train_rows = [
        (int(epoch), float(loss), float(acc))
        for epoch, loss, acc in re.findall(
            r"Epoch (\d+)/100, Average Training Loss: ([0-9.]+), Role Prediction Accuracy: ([0-9.]+)%",
            text,
        )
    ]
    val_rows = [
        (int(epoch), float(loss), float(acc))
        for epoch, loss, acc in re.findall(
            r"Epoch (\d+)/100, Validation Loss: ([0-9.]+), Validation Role Accuracy: ([0-9.]+)%",
            text,
        )
    ]
    final_train = max(train_rows, default=(0, 0.0, 0.0), key=lambda row: row[0])
    final_val = max(val_rows, default=(0, 0.0, 0.0), key=lambda row: row[0])
    best = completed[1] if len(completed) > 1 else {"best_epoch": 0, "best_validation_loss": 0.0}
    best_val_acc = next((acc for epoch, _, acc in val_rows if epoch == best["best_epoch"]), 0.0)
    return {
        "epochs": len(val_rows),
        "best_epoch": best["best_epoch"],
        "best_validation_loss": best["best_validation_loss"],
        "best_validation_role_accuracy": best_val_acc,
        "final_epoch": final_val[0],
        "final_training_loss": final_train[1],
        "final_training_role_accuracy": final_train[2],
        "final_validation_loss": final_val[1],
        "final_validation_role_accuracy": final_val[2],
    }


def _detect_errors(text: str) -> List[str]:
    error_patterns = {
        "Traceback": r"\bTraceback\b",
        "RuntimeError": r"\bRuntimeError\b",
        "APIError": r"\bAPIError\b",
        "AuthenticationError": r"\bAuthenticationError\b",
        "HTTP 401": r"\b(?:HTTP\s*)?401\b.*(?:Unauthorized|Authentication|auth)",
        "HTTP 429": r"\b(?:HTTP\s*)?429\b.*(?:quota|rate|limit|insufficient)",
        "insufficient_quota": r"\binsufficient_quota\b",
        "Killed": r"\bKilled\b",
        "NaN": r"\bNaN\b|\bnan\b",
    }
    return [
        name
        for name, pattern in error_patterns.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]


def build_execution_summary(
    log_path: str = DEFAULT_LOG_PATH,
    cold_start_dir: str = DEFAULT_COLD_START_DIR,
    finetune_data_dir: str = DEFAULT_FINETUNE_DATA_DIR,
    model_output_dir: str = DEFAULT_MODEL_OUTPUT_DIR,
) -> Dict[str, Any]:
    text = _read_text(log_path)
    completed = _parse_training_completed(text)
    stage2a_pruned, stage2c_replay = _parse_stage2_counts(text)
    topology_results = _parse_topology_results(text)
    best_topology = max(
        topology_results,
        default={"config": "", "correct": 0, "total": 0, "accuracy_percent": 0.0},
        key=lambda row: (row["correct"], row["accuracy_percent"], row["config"]),
    )
    cold_start_graph_count = _count_pt_files(cold_start_dir)
    finetune_graph_count = _count_pt_files(finetune_data_dir)
    model_dir_abs = _repo_path(model_output_dir)
    artifacts = {
        "configuration_txt": os.path.join(model_dir_abs, "configuration.txt"),
        "best_model_pth": os.path.join(model_dir_abs, "best_model.pth"),
        "ef_best_model_pth": os.path.join(model_dir_abs, "ef_best_model.pth"),
    }
    artifact_exists = {key: os.path.exists(path) for key, path in artifacts.items()}
    pipeline_complete = "Pipeline complete. Final model at:" in text
    errors_detected = _detect_errors(text)
    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "log_path": _repo_path(log_path),
        "bounded_build_run": True,
        "api_backed_graph_generation": True,
        "pipeline_complete": pipeline_complete,
        "llm_name": LLM_NAME,
        "num_iterations": NUM_ITERATIONS,
        "batch_size": BATCH_SIZE,
        "model_output_dir": model_dir_abs,
        "cold_start_dir": _repo_path(cold_start_dir),
        "finetune_data_dir": _repo_path(finetune_data_dir),
        "cold_start_graph_count": cold_start_graph_count,
        "finetune_graph_count": finetune_graph_count,
        "efficient_pruned_file_count": _count_matching_files(finetune_data_dir, r"^eff_q\d+_g\d+\.pt$"),
        "simple_topology_file_count": _count_matching_files(finetune_data_dir, r"^mmlu_\d+_[A-Za-z]+_\d+_True\.pt$"),
        "replay_file_count": _count_matching_files(finetune_data_dir, r"^mmlu_task_\d+_[A-Za-z]+_\d+_True\.pt$"),
        "stage2a_pruned_graphs_saved": stage2a_pruned,
        "stage2c_replay_graphs_copied": stage2c_replay,
        "simple_topology_results": topology_results,
        "best_simple_topology": best_topology,
        "mean_simple_topology_accuracy_percent": (
            sum(row["accuracy_percent"] for row in topology_results) / len(topology_results)
            if topology_results
            else 0.0
        ),
        "stage1": completed[0] if completed else {"best_epoch": 0, "best_validation_loss": 0.0},
        "stage3": _parse_stage3_metrics(text, completed),
        "artifacts": artifacts,
        "artifact_exists": artifact_exists,
        "compatible_checkpoint_exists": all(artifact_exists.values()),
        "errors_detected": errors_detected,
        "checkpoint_training_run": True,
        "transfer_result": False,
        "downstream_accuracy_claim_supported": False,
        "aqua_accuracy_claim_supported": False,
        "mmlu_transfer_accuracy_claim_supported": False,
        "sci_q2_ready": False,
        "transfer_eval_allowed_next": pipeline_complete and all(artifact_exists.values()),
        "broad_api_allowed_next": False,
        "next_protocol": "r162_mmlu_transfer_eval_preflight_or_bounded_eval",
        "next_goal_audit_due": "R165",
    }


def render_report(summary: Dict[str, Any]) -> str:
    topology_rows = [
        f"| `{row['config']}` | `{row['correct']}/{row['total']}` | `{row['accuracy_percent']:.1f}%` |"
        for row in summary["simple_topology_results"]
    ]
    return "\n".join(
        [
            "# R161 Bounded MMLU Checkpoint Build Execution",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Execution Verdict",
            "",
            f"- Pipeline complete: `{summary['pipeline_complete']}`",
            f"- Compatible checkpoint exists: `{summary['compatible_checkpoint_exists']}`",
            f"- Checkpoint training run: `{summary['checkpoint_training_run']}`",
            f"- Transfer result: `{summary['transfer_result']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Errors detected: `{summary['errors_detected']}`",
            "",
            "## Settings",
            "",
            f"- LLM: `{summary['llm_name']}`",
            f"- Iterations: `{summary['num_iterations']}`",
            f"- Batch size: `{summary['batch_size']}`",
            f"- Model output: `{summary['model_output_dir']}`",
            "",
            "## Artifacts",
            "",
            f"- Cold-start graphs: `{summary['cold_start_graph_count']}`",
            f"- Finetune graphs: `{summary['finetune_graph_count']}`",
            f"- Efficient pruned files: `{summary['efficient_pruned_file_count']}`",
            f"- Simple topology files: `{summary['simple_topology_file_count']}`",
            f"- Replay files: `{summary['replay_file_count']}`",
            *[f"- `{name}`: `{exists}`" for name, exists in summary["artifact_exists"].items()],
            "",
            "## Stage Metrics",
            "",
            f"- Stage 1 best: epoch `{summary['stage1']['best_epoch']}`, validation loss `{summary['stage1']['best_validation_loss']:.4f}`",
            f"- Stage 2a pruned graphs saved: `{summary['stage2a_pruned_graphs_saved']}`",
            f"- Stage 2c replay graphs copied: `{summary['stage2c_replay_graphs_copied']}`",
            f"- Stage 3 best: epoch `{summary['stage3']['best_epoch']}`, validation loss `{summary['stage3']['best_validation_loss']:.4f}`, validation role accuracy `{summary['stage3']['best_validation_role_accuracy']:.2f}%`",
            f"- Stage 3 final: epoch `{summary['stage3']['final_epoch']}`, validation loss `{summary['stage3']['final_validation_loss']:.4f}`, validation role accuracy `{summary['stage3']['final_validation_role_accuracy']:.2f}%`",
            "",
            "## Simple Topology Screening",
            "",
            "| Config | Raw accuracy | Percent |",
            "| --- | ---: | ---: |",
            *topology_rows,
            "",
            "## Claim Gate",
            "",
            f"- Downstream accuracy claim supported: `{summary['downstream_accuracy_claim_supported']}`",
            f"- MMLU transfer accuracy claim supported: `{summary['mmlu_transfer_accuracy_claim_supported']}`",
            f"- AQuA accuracy claim supported: `{summary['aqua_accuracy_claim_supported']}`",
            f"- Transfer eval allowed next: `{summary['transfer_eval_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
            "## Interpretation",
            "",
            "R161 closes the compatible MMLU checkpoint blocker. It does not close the transfer-evidence "
            "or SCI-Q2 evidence gaps. R162 should only run a bounded transfer preflight/evaluation "
            "against this checkpoint, preserving the same-model and claim-boundary constraints.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R161 bounded checkpoint execution report.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_execution_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R161 bounded checkpoint execution report: "
        f"pipeline={summary['pipeline_complete']} "
        f"stage3_best_epoch={summary['stage3']['best_epoch']} "
        f"stage3_best_val_loss={summary['stage3']['best_validation_loss']:.4f} "
        f"transfer_next={summary['transfer_eval_allowed_next']}"
    )


if __name__ == "__main__":
    main()
