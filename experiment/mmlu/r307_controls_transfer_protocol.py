from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R306_SUMMARY = "experiment/mmlu/res_logs/mmlu_r306_nonmath_stack_eval_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r307_controls_transfer_protocol_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r307_controls_transfer_protocol_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_protocol_summary(r306_summary_json: str = DEFAULT_R306_SUMMARY) -> Dict[str, Any]:
    r306 = _load_json(r306_summary_json)
    main_correct = int(r306.get("main_correct", 0))
    main_records = int(r306.get("main_records", 97))
    return {
        "run_id": "R307",
        "title": "Controls and transfer protocol before training",
        "claim_boundary": "Protocol freeze only. It blocks training until negative controls, ablations, and at least two transfer settings are evaluated.",
        "no_api": True,
        "broad_api": False,
        "source_summary": r306_summary_json,
        "current_best_run": "R306",
        "current_best_main97": f"{main_correct}/{main_records}",
        "current_best_fix_harm": r306.get("main_fix_harm"),
        "current_best_switches": r306.get("switched_task_ids", []),
        "negative_controls": {
            "no_nonmath_promptnodes": "R304 baseline stack without R305/R306 non-math nodes.",
            "random_forward": "Randomly forward the same number of candidate nodes as R306; must not match R306 gain.",
            "always_forward": "Forward every non-empty candidate; expected to expose harm if SafetyGate is removed.",
            "no_safety_gate": "Verifier candidates bypass PN_SafetyGate and go straight to router.",
            "random_promptnode_type": "Replace each candidate type with a random type while keeping candidate label hidden from gate.",
            "no_lifecycle": "Disable compress/prune/upgrade annotations and test whether graph policy degrades.",
        },
        "required_ablations": {
            "remove_instruction_ambiguity_verifier": "Measure whether ambiguity flags prevent unsafe forwarding.",
            "remove_option_semantic_consistency": "Expected to lose MMLU-machine_learning_test-81 repair.",
            "remove_contradiction_detector": "Expected to lose conceptual all-of-these repair.",
            "remove_memory_bridge": "Expected to leave truncation cases unresolved and document data-path limitation.",
            "remove_symbolic_verifier_family": "Separate non-math contribution from R304 symbolic contribution.",
            "remove_safety_gate": "Must be worse or higher harm than gated variant.",
        },
        "required_transfer_splits": {
            "AQuA_tail34_audit_clean": "Run the same node catalog on AQuA tail34 audit-clean with task_59/task_139/task_228 excluded or appendix-only.",
            "MMLU_non_STEM_multiple_choice": "Create a non-STEM multiple-choice split to test instruction/semantic nodes outside formula-heavy STEM.",
            "MMLU_STEM_main97": "Retain current main97 as development/diagnostic split, not the only evidence.",
        },
        "training_entry_criteria": {
            "main97_no_harm": "R306 or later keeps main official and audit-clean harm at 0.",
            "controls_pass": "No negative control beats the gated method at equal switch budget.",
            "transfer_not_negative": "At least one non-AQuA transfer split has positive gain or statistically non-negative delta.",
            "type_coverage": "At least four PromptNode families contribute candidates, with at least two non-symbolic families.",
            "leakage_pass": "Training inputs exclude task_id, true_answer, correctness, and audit labels.",
        },
        "training_authorized_next": False,
        "next_runs": [
            "R308 random/always-forward negative controls",
            "R309 per-node ablation table",
            "R310 AQuA transfer stack replay",
            "R311 MMLU non-STEM transfer split preflight",
        ],
        "sci_q2_ready": False,
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R307 Controls And Transfer Protocol",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Current best: `{summary['current_best_run']}` main97 `{summary['current_best_main97']}` with fix/harm `{summary['current_best_fix_harm']}`",
        f"- Training authorized next: `{summary['training_authorized_next']}`",
        "",
        "## Negative Controls",
        "",
    ]
    rows.extend(f"- `{name}`: {desc}" for name, desc in summary["negative_controls"].items())
    rows.extend(["", "## Required Transfer Splits", ""])
    rows.extend(f"- `{name}`: {desc}" for name, desc in summary["required_transfer_splits"].items())
    rows.extend(["", "## Training Entry Criteria", ""])
    rows.extend(f"- `{name}`: {desc}" for name, desc in summary["training_entry_criteria"].items())
    rows.extend(["", "## Next Runs", ""])
    rows.extend(f"- {item}" for item in summary["next_runs"])
    rows.append("")
    return "\n".join(rows)


def run(
    r306_summary_json: str = DEFAULT_R306_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_protocol_summary(r306_summary_json)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze R307 controls and transfer protocol.")
    parser.add_argument("--r306_summary_json", default=DEFAULT_R306_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
