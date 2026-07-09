from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R369_RESULTS = "experiment/mmlu/run_logs/mmlu_r369_adversarial_verifier_api_probe_results.jsonl"
DEFAULT_R369_SUMMARY = "experiment/mmlu/res_logs/mmlu_r369_adversarial_verifier_api_probe_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r370_adversarial_verifier_probe_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r370_adversarial_verifier_probe_analysis_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    p = _repo_path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_probe_analysis(
    r369_results: str = DEFAULT_R369_RESULTS,
    r369_summary: str = DEFAULT_R369_SUMMARY,
) -> Dict[str, Any]:
    rows = _load_jsonl(r369_results)
    r369 = _load_json(r369_summary)
    domain = [row for row in rows if row.get("control_variant") == "domain_specialized_candidate_api"]
    domain_candidates = [row for row in domain if row.get("candidate_label")]
    domain_correct = [row for row in domain_candidates if row.get("candidate_is_correct")]
    history_correct = [row for row in domain_correct if row.get("subject") == "high_school_us_history"]
    wrong_domain = [row for row in domain_candidates if not row.get("candidate_is_correct")]
    subject_counts = Counter(row.get("subject") for row in wrong_domain)
    root_causes = []
    if r369.get("adversarial_block_count", 0) == 0:
        root_causes.append("adversarial_prompt_repeated_prior_candidate")
    if domain_candidates and len(domain_correct) / len(domain_candidates) < 0.5:
        root_causes.append("unconstrained_domain_verifier_is_unsafe")
        root_causes.append("needs_evidence_type_specific_gate_features")
    if history_correct:
        root_causes.append("passage_history_entailment_is_promising_but_needs_fresh_validation")
    precision = round(len(domain_correct) / len(domain_candidates), 6) if domain_candidates else 0.0
    return {
        "run_id": "R370",
        "title": "Adversarial verifier probe analysis",
        "claim_boundary": (
            "R370 analyzes the targeted R369 probe. It rejects unconstrained domain verifiers as unsafe and keeps "
            "only the history-passage signal as a future preflight candidate."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "adversarial_block_count": int(r369.get("adversarial_block_count", 0)),
        "adversarial_correct_candidate_count": int(r369.get("adversarial_correct_candidate_count", 0)),
        "domain_candidate_count": len(domain_candidates),
        "domain_correct_candidate_count": len(domain_correct),
        "domain_candidate_precision": precision,
        "history_domain_correct_count": len(history_correct),
        "wrong_domain_subject_counts": dict(sorted(subject_counts.items())),
        "root_causes": root_causes,
        "claim_permissions": {
            "integrate_unconstrained_domain_verifier": False,
            "history_passage_signal_allowed_for_future_preflight": bool(history_correct),
            "hard_negative_update_allowed": bool(wrong_domain),
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R371_adversarial_probe_hard_negative_update",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R370 Adversarial Verifier Probe Analysis",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Domain candidates/correct/precision: `{summary['domain_candidate_count']}/{summary['domain_correct_candidate_count']}/{summary['domain_candidate_precision']}`",
        f"- Adversarial block count: `{summary['adversarial_block_count']}`",
        f"- History correct: `{summary['history_domain_correct_count']}`",
        f"- Wrong-domain subjects: `{summary['wrong_domain_subject_counts']}`",
        f"- Root causes: `{summary['root_causes']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run(
    r369_results: str = DEFAULT_R369_RESULTS,
    r369_summary: str = DEFAULT_R369_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_probe_analysis(r369_results=r369_results, r369_summary=r369_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R369 adversarial verifier probe.")
    parser.add_argument("--r369_results", default=DEFAULT_R369_RESULTS)
    parser.add_argument("--r369_summary", default=DEFAULT_R369_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
