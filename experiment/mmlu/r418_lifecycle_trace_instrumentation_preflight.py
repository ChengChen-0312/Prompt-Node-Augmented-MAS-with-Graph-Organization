from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SOURCE_JSONL = "experiment/mmlu/run_logs/mmlu_r413_definition_challenge_gate_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r418_lifecycle_trace_instrumentation_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r418_lifecycle_trace_instrumentation_preflight_report.md"


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


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_lifecycle_preflight(source_jsonl: str = DEFAULT_SOURCE_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(source_jsonl)
    lifecycle_actions = ["write", "update", "compress", "prune", "merge", "upgrade"]
    event_schema = {
        "required_fields": [
            "run_id",
            "task_id",
            "event_index",
            "event_type",
            "node_or_edge",
            "action",
            "read_from",
            "write_to",
            "forward_to",
            "evidence",
            "gate_effect",
        ],
        "event_types": [
            "PromptNodeWrite",
            "PromptNodeUpdate",
            "PromptNodeCompress",
            "PromptNodePrune",
            "PromptNodeMerge",
            "PromptNodeUpgrade",
            "PromptEdgeRead",
            "PromptEdgeWrite",
            "PromptEdgeForward",
            "GateDecision",
        ],
        "node_types": [
            "InstructionAmbiguityVerifierPN",
            "ConceptDefinitionAnchorPN",
            "OptionSemanticConsistencyVerifierPN",
            "AdversarialVerifierPN",
            "ContradictionDetectorPN",
            "ConsensusConflictResolverPN",
        ],
        "edge_types": [
            "DefinitionAnchorPromptEdge",
            "AdversarialChallengePromptEdge",
            "ConflictResolutionPromptEdge",
            "OptionBindingPromptEdge",
        ],
    }
    return {
        "run_id": "R418",
        "title": "Lifecycle trace instrumentation preflight",
        "claim_boundary": (
            "R418 defines the lifecycle event schema for replaying existing results. It does not execute API or create "
            "new accuracy evidence."
        ),
        "no_api": True,
        "broad_api": False,
        "source_jsonl": source_jsonl,
        "source_records": len(rows),
        "lifecycle_actions": lifecycle_actions,
        "event_schema": event_schema,
        "trace_replay_authorized_next": bool(rows),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R419_lifecycle_trace_replay",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R418 Lifecycle Trace Instrumentation Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Source records: `{summary['source_records']}`",
            f"- Lifecycle actions: `{summary['lifecycle_actions']}`",
            f"- Event types: `{summary['event_schema']['event_types']}`",
            f"- Trace replay authorized next: `{summary['trace_replay_authorized_next']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    source_jsonl: str = DEFAULT_SOURCE_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_lifecycle_preflight(source_jsonl=source_jsonl)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build lifecycle trace instrumentation preflight.")
    parser.add_argument("--source_jsonl", default=DEFAULT_SOURCE_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
