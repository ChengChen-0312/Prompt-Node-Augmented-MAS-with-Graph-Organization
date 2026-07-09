from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r335_prospective_selector_eval_api_smoke import _label
from experiment.mmlu.r373_retrain_after_r369_hard_negatives import DECISION_THRESHOLD, _clean_features
from experiment.mmlu.r375_history_guarded_fresh_eval_api_execution import (
    DEFAULT_TRAINING_MANIFEST_JSONL,
    _candidate_features,
    _confidence_value,
    _train_gate,
)


DEFAULT_R375_RESULTS = "experiment/mmlu/run_logs/mmlu_r375_history_guarded_fresh_eval_api_results.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r377_option_binding_promptedge_replay_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r377_option_binding_promptedge_replay_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r377_option_binding_promptedge_replay_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    p = _repo_path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _explicit_option_labels(rationale: str) -> List[str]:
    labels = []
    for match in re.finditer(r"\bOption\s+([A-E])\b", str(rationale or ""), flags=re.I):
        label = _label(match.group(1))
        if label:
            labels.append(label)
    return labels


def _bind_candidate(parsed: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    confidence = _confidence_value(parsed.get("confidence"))
    evidence_count = int(parsed.get("evidence_count") or 0)
    labels = _explicit_option_labels(str(parsed.get("rationale") or ""))
    unique = sorted(set(labels))
    if len(unique) != 1 or confidence < 0.85 or evidence_count < 1:
        return "", {}
    bound = dict(parsed)
    bound.update(
        {
            "candidate_label": unique[0],
            "promptnode_family": "history-passage-option-binding",
            "candidate_type": "option_binding_promptedge",
            "promptedge_contract_pass": True,
        }
    )
    return unique[0], bound


def build_option_binding_replay(
    r375_results: str = DEFAULT_R375_RESULTS,
    training_manifest_jsonl: str = DEFAULT_TRAINING_MANIFEST_JSONL,
) -> Dict[str, Any]:
    rows = _load_jsonl(r375_results)
    vectorizer, model = _train_gate(training_manifest_jsonl)
    replay_rows = []
    for row in rows:
        baseline = _label(row.get("arg_prediction")) or "A"
        true_answer = _label(row.get("true_answer"))
        parsed = row.get("candidate_parsed_response") or {}
        candidate, bound_parsed = _bind_candidate(parsed if isinstance(parsed, dict) else {})
        score = 0.0
        features: Dict[str, Any] = {}
        gate_forward = False
        if candidate:
            features = _candidate_features(row, bound_parsed)
            score = float(model.predict_proba(vectorizer.transform([_clean_features(features)]))[:, 1][0])
            gate_forward = score >= DECISION_THRESHOLD
        final = candidate if gate_forward else baseline
        replay_rows.append(
            {
                "run_id": "R377",
                "task_id": row.get("task_id"),
                "dataset_family": row.get("dataset_family"),
                "subject": row.get("subject"),
                "true_answer": true_answer,
                "arg_prediction": baseline,
                "r375_final_prediction": row.get("final_prediction"),
                "bound_candidate_label": candidate,
                "gate_forward_probability": round(score, 6),
                "gate_forward": gate_forward,
                "final_prediction": final,
                "arg_correct": baseline == true_answer,
                "r375_final_correct": bool(row.get("final_correct")),
                "final_correct": final == true_answer,
                "fix": baseline != true_answer and final == true_answer,
                "harm": baseline == true_answer and final != true_answer,
                "wrong_forward": gate_forward and final != true_answer,
                "blocked_original_r375_forward": bool(row.get("gate_forward")) and not gate_forward,
                "bound_candidate_features": features,
                "bound_candidate_parsed_response": bound_parsed,
            }
        )
    return _summarize(replay_rows)


def _summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    arg_correct = sum(1 for row in rows if row.get("arg_correct"))
    r375_correct = sum(1 for row in rows if row.get("r375_final_correct"))
    edge_correct = sum(1 for row in rows if row.get("final_correct"))
    return {
        "run_id": "R377",
        "title": "OptionBinding PromptEdge replay",
        "claim_boundary": (
            "R377 is a replay over R375 outputs. It tests whether a first-class PromptEdge can bind explicit "
            "Option X rationales into structured candidate labels before the learned safety gate. It is not a "
            "fresh API result."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "arg_correct": arg_correct,
        "r375_hybrid_correct": r375_correct,
        "edge_hybrid_correct": edge_correct,
        "delta_vs_arg": edge_correct - arg_correct,
        "delta_vs_r375": edge_correct - r375_correct,
        "arg_accuracy": round(arg_correct / len(rows), 6) if rows else 0.0,
        "edge_hybrid_accuracy": round(edge_correct / len(rows), 6) if rows else 0.0,
        "bound_candidate_count": sum(1 for row in rows if row.get("bound_candidate_label")),
        "gate_forward_count": sum(1 for row in rows if row.get("gate_forward")),
        "fixes": sum(1 for row in rows if row.get("fix")),
        "harms": sum(1 for row in rows if row.get("harm")),
        "wrong_forward_count": sum(1 for row in rows if row.get("wrong_forward")),
        "blocked_original_r375_forward_count": sum(1 for row in rows if row.get("blocked_original_r375_forward")),
        "fix_task_ids": [row.get("task_id") for row in rows if row.get("fix")],
        "harm_task_ids": [row.get("task_id") for row in rows if row.get("harm")],
        "wrong_forward_task_ids": [row.get("task_id") for row in rows if row.get("wrong_forward")],
        "claim_permissions": {
            "mechanism_replay_positive_delta_no_harm_allowed": edge_correct > arg_correct and not any(row.get("harm") for row in rows),
            "fresh_positive_delta_claim_allowed": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "replay_rows": rows,
        "next_required_run": "R378_goal_audit_after_option_binding_promptedge",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R377 OptionBinding PromptEdge Replay",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- ARG: `{summary['arg_correct']}/{summary['records']}`",
            f"- R375 hybrid: `{summary['r375_hybrid_correct']}/{summary['records']}`",
            f"- Edge hybrid: `{summary['edge_hybrid_correct']}/{summary['records']}`",
            f"- Delta vs ARG/R375: `{summary['delta_vs_arg']}/{summary['delta_vs_r375']}`",
            f"- Bound/forward/fix/harm/wrong-forward: `{summary['bound_candidate_count']}/{summary['gate_forward_count']}/{summary['fixes']}/{summary['harms']}/{summary['wrong_forward_count']}`",
            f"- Fix tasks: `{summary['fix_task_ids']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r375_results: str = DEFAULT_R375_RESULTS,
    training_manifest_jsonl: str = DEFAULT_TRAINING_MANIFEST_JSONL,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_option_binding_replay(r375_results=r375_results, training_manifest_jsonl=training_manifest_jsonl)
    replay_rows = summary.pop("replay_rows")
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(output_jsonl, replay_rows)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay R375 with an explicit OptionBinding PromptEdge.")
    parser.add_argument("--r375_results", default=DEFAULT_R375_RESULTS)
    parser.add_argument("--training_manifest_jsonl", default=DEFAULT_TRAINING_MANIFEST_JSONL)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
