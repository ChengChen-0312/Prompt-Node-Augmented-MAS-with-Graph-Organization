from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r373_retrain_after_r369_hard_negatives import DECISION_THRESHOLD, _clean_features
from experiment.mmlu.r392_retrain_after_mixed_nonmath_hard_negatives import (
    DEFAULT_MANIFEST_JSONL as DEFAULT_TRAINING_MANIFEST_JSONL,
    _sample_weights,
)


DEFAULT_R389_RESULTS = "experiment/mmlu/run_logs/mmlu_r389_mixed_nonmath_option_binding_api_results.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r393_replay_mixed_nonmath_with_retrained_gate_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r393_replay_mixed_nonmath_with_retrained_gate_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r393_replay_mixed_nonmath_with_retrained_gate_report.md"


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


def _train_gate(training_manifest_jsonl: str = DEFAULT_TRAINING_MANIFEST_JSONL) -> Tuple[DictVectorizer, LogisticRegression]:
    train_rows = [row for row in _load_jsonl(training_manifest_jsonl) if row.get("split") == "train"]
    vectorizer = DictVectorizer(sparse=True)
    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=0, solver="liblinear")
    x = vectorizer.fit_transform([_clean_features(row["features"]) for row in train_rows])
    y = [int(bool(row.get("target_forward"))) for row in train_rows]
    model.fit(x, y, sample_weight=_sample_weights(train_rows))
    return vectorizer, model


def replay_rows(
    r389_results: str = DEFAULT_R389_RESULTS,
    training_manifest_jsonl: str = DEFAULT_TRAINING_MANIFEST_JSONL,
) -> List[Dict[str, Any]]:
    rows = _load_jsonl(r389_results)
    vectorizer, model = _train_gate(training_manifest_jsonl)
    replayed = []
    for row in rows:
        candidate = str(row.get("candidate_label") or "").strip().upper()[:1]
        score = 0.0
        if candidate:
            score = float(model.predict_proba(vectorizer.transform([_clean_features(row.get("candidate_features") or {})]))[:, 1][0])
        gate_forward = bool(candidate and score >= DECISION_THRESHOLD)
        final = candidate if gate_forward else row.get("arg_prediction")
        out = dict(row)
        out.update(
            {
                "run_id": "R393",
                "original_gate_forward": bool(row.get("gate_forward")),
                "original_final_prediction": row.get("final_prediction"),
                "retrained_gate_forward_probability": round(score, 6),
                "retrained_gate_forward": gate_forward,
                "retrained_final_prediction": final,
                "retrained_final_correct": final == row.get("true_answer"),
                "retrained_fix": (not row.get("arg_correct")) and final == row.get("true_answer"),
                "retrained_harm": row.get("arg_correct") and final != row.get("true_answer"),
                "retrained_wrong_forward": gate_forward and final != row.get("true_answer"),
                "blocked_original_wrong_forward": bool(row.get("wrong_forward")) and not gate_forward,
            }
        )
        replayed.append(out)
    return replayed


def build_replay_summary(
    r389_results: str = DEFAULT_R389_RESULTS,
    training_manifest_jsonl: str = DEFAULT_TRAINING_MANIFEST_JSONL,
) -> Dict[str, Any]:
    rows = replay_rows(r389_results=r389_results, training_manifest_jsonl=training_manifest_jsonl)
    return {
        "run_id": "R393",
        "title": "Replay mixed nonmath with retrained gate",
        "claim_boundary": (
            "R393 replays R389 outputs with the R392 weighted gate. It is not a fresh API result, but verifies "
            "that the updated gate removes known wrong-forwards without losing the positive delta."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "arg_correct": sum(1 for row in rows if row.get("arg_correct")),
        "original_hybrid_correct": sum(1 for row in rows if row.get("final_correct")),
        "retrained_hybrid_correct": sum(1 for row in rows if row.get("retrained_final_correct")),
        "retrained_delta_correct": sum(1 for row in rows if row.get("retrained_final_correct")) - sum(1 for row in rows if row.get("arg_correct")),
        "original_gate_forward_count": sum(1 for row in rows if row.get("original_gate_forward")),
        "retrained_gate_forward_count": sum(1 for row in rows if row.get("retrained_gate_forward")),
        "retrained_fixes": sum(1 for row in rows if row.get("retrained_fix")),
        "retrained_harms": sum(1 for row in rows if row.get("retrained_harm")),
        "retrained_wrong_forward_count": sum(1 for row in rows if row.get("retrained_wrong_forward")),
        "blocked_original_wrong_forward_count": sum(1 for row in rows if row.get("blocked_original_wrong_forward")),
        "retrained_fix_task_ids": [row.get("task_id") for row in rows if row.get("retrained_fix")],
        "blocked_original_wrong_forward_task_ids": [row.get("task_id") for row in rows if row.get("blocked_original_wrong_forward")],
        "claim_permissions": {
            "replay_positive_no_harm_allowed": sum(1 for row in rows if row.get("retrained_final_correct")) > sum(1 for row in rows if row.get("arg_correct"))
            and not any(row.get("retrained_harm") for row in rows),
            "larger_fresh_preflight_allowed_next": True,
            "api_execution_allowed_now": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "replay_rows": rows,
        "next_required_run": "R394_larger_mixed_nonmath_fresh_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R393 Replay Mixed Nonmath With Retrained Gate",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- ARG/original/retrained: `{summary['arg_correct']}/{summary['original_hybrid_correct']}/{summary['retrained_hybrid_correct']}`",
            f"- Retrained forward/fix/harm/wrong-forward: `{summary['retrained_gate_forward_count']}/{summary['retrained_fixes']}/{summary['retrained_harms']}/{summary['retrained_wrong_forward_count']}`",
            f"- Blocked original wrong-forwards: `{summary['blocked_original_wrong_forward_task_ids']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r389_results: str = DEFAULT_R389_RESULTS,
    training_manifest_jsonl: str = DEFAULT_TRAINING_MANIFEST_JSONL,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_replay_summary(r389_results=r389_results, training_manifest_jsonl=training_manifest_jsonl)
    rows = summary.pop("replay_rows")
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(output_jsonl, rows)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay R389 mixed nonmath outputs with the R392 retrained gate.")
    parser.add_argument("--r389_results", default=DEFAULT_R389_RESULTS)
    parser.add_argument("--training_manifest_jsonl", default=DEFAULT_TRAINING_MANIFEST_JSONL)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
