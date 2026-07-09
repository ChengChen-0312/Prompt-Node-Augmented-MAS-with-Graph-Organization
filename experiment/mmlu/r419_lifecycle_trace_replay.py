from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SOURCE_JSONL = "experiment/mmlu/run_logs/mmlu_r413_definition_challenge_gate_api_results.jsonl"
DEFAULT_TRACE_JSONL = "experiment/mmlu/run_logs/mmlu_r419_lifecycle_trace_events.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r419_lifecycle_trace_replay_report.md"


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


def _event(
    row: Dict[str, Any],
    event_index: int,
    event_type: str,
    node_or_edge: str,
    action: str,
    evidence: Any,
    gate_effect: str = "",
    read_from: str = "",
    write_to: str = "graph_state",
    forward_to: str = "",
) -> Dict[str, Any]:
    return {
        "run_id": "R419",
        "source_run": "R413",
        "task_id": row.get("task_id"),
        "subject": row.get("subject"),
        "event_index": event_index,
        "event_type": event_type,
        "node_or_edge": node_or_edge,
        "action": action,
        "read_from": read_from,
        "write_to": write_to,
        "forward_to": forward_to,
        "evidence": evidence,
        "gate_effect": gate_effect,
    }


def _row_events(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    parsed = row.get("candidate_parsed_response") or {}
    outputs = parsed.get("promptnode_outputs") if isinstance(parsed.get("promptnode_outputs"), dict) else {}
    events = [
        _event(
            row,
            1,
            "PromptNodeWrite",
            "InstructionAmbiguityVerifierPN",
            "write",
            outputs.get("InstructionAmbiguityVerifierPN", "instruction extracted"),
            read_from="visible_item",
        ),
        _event(
            row,
            2,
            "PromptNodeUpdate",
            "ConceptDefinitionAnchorPN",
            "update",
            outputs.get("ConceptDefinitionAnchorPN", "definition anchor updated"),
            read_from="InstructionAmbiguityVerifierPN",
        ),
        _event(
            row,
            3,
            "PromptNodeCompress",
            "ConceptDefinitionAnchorPN",
            "compress",
            {
                "definition_anchor_confidence": parsed.get("definition_anchor_confidence"),
                "memory_bridge_write_confidence": parsed.get("memory_bridge_write_confidence"),
            },
            read_from="ConceptDefinitionAnchorPN",
            write_to="MemoryBridgePN",
        ),
        _event(
            row,
            4,
            "PromptNodeMerge",
            "ConsensusConflictResolverPN",
            "merge",
            {
                "node_agreement_count": parsed.get("node_agreement_count"),
                "node_disagreement_count": parsed.get("node_disagreement_count"),
                "contradiction_count": parsed.get("contradiction_count"),
            },
            read_from="OptionSemanticConsistencyVerifierPN+AdversarialVerifierPN+ContradictionDetectorPN",
        ),
    ]
    if row.get("gate_forward"):
        events.append(
            _event(
                row,
                5,
                "PromptEdgeForward",
                "OptionBindingPromptEdge",
                "forward",
                {
                    "candidate_label": row.get("candidate_label"),
                    "final_prediction": row.get("final_prediction"),
                    "nearest_distractor_margin": parsed.get("nearest_distractor_margin"),
                },
                gate_effect="forwarded",
                read_from="ConsensusConflictResolverPN",
                forward_to="final_aggregator",
            )
        )
    else:
        events.append(
            _event(
                row,
                5,
                "PromptNodePrune",
                "ConsensusConflictResolverPN",
                "prune",
                {"gate_block_reasons": row.get("gate_block_reasons"), "candidate_label": row.get("candidate_label")},
                gate_effect="candidate_pruned",
                read_from="ConsensusConflictResolverPN",
                write_to="final_aggregator",
            )
        )
    if row.get("fix"):
        events.append(
            _event(
                row,
                6,
                "PromptNodeUpgrade",
                "DefinitionChallengeGatePN",
                "upgrade",
                {"fix": True, "arg_prediction": row.get("arg_prediction"), "final_prediction": row.get("final_prediction")},
                gate_effect="repair_success",
                read_from="final_aggregator",
                write_to="case_study_bank",
            )
        )
    return events


def build_lifecycle_trace(source_jsonl: str = DEFAULT_SOURCE_JSONL) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = _load_jsonl(source_jsonl)
    events: List[Dict[str, Any]] = []
    for row in rows:
        events.extend(_row_events(row))
    event_counts = Counter(event["event_type"] for event in events)
    forward_ids = [row["task_id"] for row in rows if row.get("gate_forward")]
    prune_ids = [row["task_id"] for row in rows if not row.get("gate_forward")]
    upgrade_ids = [row["task_id"] for row in rows if row.get("fix")]
    return events, {
        "run_id": "R419",
        "title": "Lifecycle trace replay",
        "claim_boundary": (
            "R419 replays existing R413 outputs into lifecycle events. It supports case-study visualization, not new "
            "accuracy claims."
        ),
        "no_api": True,
        "broad_api": False,
        "source_jsonl": source_jsonl,
        "source_records": len(rows),
        "events": len(events),
        "event_counts": dict(sorted(event_counts.items())),
        "forwarded_tasks": len(forward_ids),
        "pruned_tasks": len(prune_ids),
        "upgrade_task_ids": upgrade_ids,
        "forward_task_ids": forward_ids,
        "prune_task_ids": prune_ids,
        "case_study_trace_available": bool(upgrade_ids and prune_ids),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R420_paper_asset_table_refresh",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R419 Lifecycle Trace Replay",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Source records: `{summary['source_records']}`",
            f"- Events: `{summary['events']}`",
            f"- Event counts: `{summary['event_counts']}`",
            f"- Forwarded/pruned tasks: `{summary['forwarded_tasks']}/{summary['pruned_tasks']}`",
            f"- Upgrade tasks: `{summary['upgrade_task_ids']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    source_jsonl: str = DEFAULT_SOURCE_JSONL,
    trace_jsonl: str = DEFAULT_TRACE_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    events, summary = build_lifecycle_trace(source_jsonl=source_jsonl)
    summary.update({"trace_jsonl": trace_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(trace_jsonl, events)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay R413 into lifecycle trace events.")
    parser.add_argument("--source_jsonl", default=DEFAULT_SOURCE_JSONL)
    parser.add_argument("--trace_jsonl", default=DEFAULT_TRACE_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
