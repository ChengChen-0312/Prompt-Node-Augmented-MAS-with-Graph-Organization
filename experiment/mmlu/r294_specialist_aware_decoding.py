from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Set

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r286_constrained_promptnode_decoding import candidate_score


DEFAULT_CANDIDATES = "experiment/mmlu/run_logs/mmlu_r287_constrained_promptnode_decoding_c64_candidates.jsonl"
DEFAULT_REFERENCE_SELECTED = "experiment/mmlu/run_logs/mmlu_r287_constrained_promptnode_decoding_c64_selected.jsonl"
DEFAULT_SELECTED = "experiment/mmlu/run_logs/mmlu_r294_specialist_aware_decoding_selected.jsonl"
DEFAULT_SUMMARY = "experiment/mmlu/res_logs/mmlu_r294_specialist_aware_decoding_summary.json"
DEFAULT_REPORT = "experiment/mmlu/run_logs/mmlu_r294_specialist_aware_decoding_report.md"

STEM_SPECIALISTS = {"Mathematician", "Programmer", "Knowlegable Expert"}
SCIENCE_SPECIALISTS = {"Mathematician", "Programmer", "Knowlegable Expert", "Doctor"}


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        f.write(text)


def specialist_roles_for_subject(subject: str) -> Set[str]:
    subject = str(subject or "").lower()
    if any(token in subject for token in ["math", "statistics", "algebra"]):
        return STEM_SPECIALISTS
    if any(token in subject for token in ["computer", "machine_learning", "physics", "engineering"]):
        return STEM_SPECIALISTS
    if "chemistry" in subject or "biology" in subject:
        return SCIENCE_SPECIALISTS
    return {"Knowlegable Expert", "Critic"}


def specialist_count(candidate: Dict[str, Any]) -> int:
    roles = candidate.get("roles", []) or []
    wanted = specialist_roles_for_subject(str(candidate.get("subject", "")))
    return sum(1 for role in roles if role in wanted)


def specialist_aware_score(candidate: Dict[str, Any]) -> float:
    pn_count = int(candidate.get("pn_role_count", 0) or 0)
    specialist_bonus = min(specialist_count(candidate), 3) * 25.0
    pn_crowding_penalty = max(0, pn_count - 3) * 4.0
    return candidate_score(candidate) + specialist_bonus - pn_crowding_penalty


def select_specialist_aware_candidate(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not candidates:
        raise ValueError("No candidates to select.")
    return max(
        candidates,
        key=lambda row: (
            specialist_aware_score(row),
            bool(row.get("promptedge_contract_ready")),
            specialist_count(row),
            -int(row.get("candidate_index", 0)),
        ),
    )


def count_changed_from_reference(
    selected_rows: List[Dict[str, Any]],
    reference_rows: List[Dict[str, Any]],
) -> int:
    reference_by_id = {str(row.get("task_id")): row for row in reference_rows}
    return sum(
        1
        for row in selected_rows
        if int(row.get("candidate_index", -1))
        != int(reference_by_id.get(str(row.get("task_id")), {}).get("candidate_index", -2))
    )


def summarize_selected(
    selected_rows: List[Dict[str, Any]],
    candidate_rows: List[Dict[str, Any]],
    reference_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    total = len(selected_rows)
    changed_from_r287 = count_changed_from_reference(selected_rows, reference_rows)
    return {
        "run_id": "R294",
        "title": "Specialist-aware constrained PromptNode decoding",
        "claim_boundary": (
            "No-API reselection over saved R287 candidates. It changes only selection objective; "
            "no new graph sampling, answer labels, or API calls are used."
        ),
        "no_api": True,
        "broad_api": False,
        "tasks": total,
        "candidate_graphs": len(candidate_rows),
        "selected_contract_ready": sum(1 for row in selected_rows if row.get("promptedge_contract_ready")),
        "selected_contract_ready_rate": (
            sum(1 for row in selected_rows if row.get("promptedge_contract_ready")) / total
            if total
            else 0.0
        ),
        "selected_with_specialist": sum(1 for row in selected_rows if specialist_count(row) > 0),
        "selected_mean_specialist_count": (
            sum(specialist_count(row) for row in selected_rows) / total if total else 0.0
        ),
        "changed_from_r287": changed_from_r287,
        "api_eval_allowed_next": total > 0
        and sum(1 for row in selected_rows if row.get("promptedge_contract_ready")) / total >= 0.5,
        "accuracy_claim_supported": False,
        "next_goal_audit_due": "R295",
    }


def run(
    candidates_jsonl: str = DEFAULT_CANDIDATES,
    reference_selected_jsonl: str = DEFAULT_REFERENCE_SELECTED,
    selected_jsonl: str = DEFAULT_SELECTED,
    summary_json: str = DEFAULT_SUMMARY,
    report_md: str = DEFAULT_REPORT,
) -> Dict[str, Any]:
    candidate_rows = _load_jsonl(candidates_jsonl)
    reference_rows = _load_jsonl(reference_selected_jsonl)
    reference_by_id = {str(row.get("task_id")): row for row in reference_rows}
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("task_id"))].append(row)

    selected = []
    for task_id, rows in grouped.items():
        best = dict(select_specialist_aware_candidate(rows))
        best["selected_by"] = "specialist_aware_contract_decoding"
        best["r287_selected_candidate_index"] = reference_by_id.get(task_id, {}).get("candidate_index")
        best["specialist_count"] = specialist_count(best)
        best["specialist_aware_score"] = specialist_aware_score(best)
        selected.append(best)
    selected.sort(key=lambda row: str(row.get("task_id")))

    summary = summarize_selected(selected, candidate_rows, reference_rows)
    summary.update(
        {
            "candidates_jsonl": candidates_jsonl,
            "reference_selected_jsonl": reference_selected_jsonl,
            "selected_jsonl": selected_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    _write_jsonl(selected_jsonl, selected)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R294 Specialist-Aware PromptNode Decoding",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- Candidate graphs: `{summary['candidate_graphs']}`",
            f"- Selected contract-ready: `{summary['selected_contract_ready']}`",
            f"- Selected contract-ready rate: `{summary['selected_contract_ready_rate']}`",
            f"- Selected with specialist: `{summary['selected_with_specialist']}`",
            f"- Mean specialist count: `{summary['selected_mean_specialist_count']}`",
            f"- Changed from R287: `{summary['changed_from_r287']}`",
            f"- API eval allowed next: `{summary['api_eval_allowed_next']}`",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run no-API specialist-aware reselection over R287 candidates.")
    parser.add_argument("--candidates_jsonl", default=DEFAULT_CANDIDATES)
    parser.add_argument("--reference_selected_jsonl", default=DEFAULT_REFERENCE_SELECTED)
    parser.add_argument("--selected_jsonl", default=DEFAULT_SELECTED)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY)
    parser.add_argument("--report_md", default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
