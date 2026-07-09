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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r430_draft_method_results_sections_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r430_draft_method_results_sections_report.md"
DEFAULT_OUTPUT_DIR = "paper/sections"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _sections() -> Dict[str, str]:
    method = r"""\section{PromptNode-Augmented Multi-Agent Graphs}
\label{sec:method}

We model a multi-agent reasoning workflow as a directed communication graph whose nodes may be ordinary agents, tools, memory stores, verifiers, or typed virtual PromptNodes. A PromptNode is not a post-hoc answer patch. It is a first-class graph element with an identity, read/write permissions, a forwarding contract, and lifecycle actions. In our implementation, PromptNode identities include Memory, Instruction-Verifier, Tool-Resource, Verifier, and Agent-like roles. PromptEdges carry explicit read, write, and forward constraints: they determine what evidence a downstream node may consume, what state may be written, and whether an answer label may be forwarded to the final aggregator.

The graph policy follows a two-stage organization. First, diagnostic PromptNodes write structured evidence such as the operative instruction, option binding, definition anchors, adversarial checks, contradictions, confidence, and local memory summaries. Second, a conservative gate decides whether the candidate answer should be forwarded or pruned. The gate is trained or fixed only over graph-visible features, never over hidden labels, task identifiers, or post-hoc correctness. Lifecycle events are recorded as update, compress, prune, merge, and upgrade actions; R419 replays 121 lifecycle events from the fresh R413 DefinitionChallenge run.

For STEM tasks, PromptNodes instantiate InstructionVerifierPN, ToolResourcePN, OptionVerifierPN, and SafetyGatePN. For non-mathematical concept-definition tasks, the DefinitionChallenge path uses InstructionAmbiguityVerifierPN, ConceptDefinitionAnchorPN, OptionSemanticConsistencyVerifierPN, AdversarialVerifierPN, ContradictionDetectorPN, and ConsensusConflictResolverPN. This separation is deliberate: the method is graph organization, while the node library is task-family specific.
"""

    experiments = r"""\section{Experimental Setup}
\label{sec:setup}

We use ARG-Designer as the main baseline and preserve its model setting as closely as possible. All API-based fresh runs in the current evidence set use \texttt{gpt-4o-2024-08-06}. The main evaluated slices are: audited AQuA tail34, MMLU STEM transfer, mixed MMLU non-STEM transfer, and a fresh DefinitionChallenge subset over logical fallacies, moral disputes, and philosophy. For AQuA, known noisy items are reported through official and audit-clean columns rather than silently rewritten. For MMLU, audited label issues are excluded or reported in appendix-style sensitivity analyses.

Metrics are accuracy, fix/harm, wrong-forward count, and cost. Cost rows are sourced from direct API summaries when available. The MMLU STEM cost in the current draft is a probe-estimated cost from R424/R425, not exact original R306 accounting. All paper-facing claims remain provisional because the external integrity audit is pending.
"""

    results = r"""\section{Results}
\label{sec:results}

\paragraph{AQuA audited tail.}
On the audit-clean AQuA tail31 slice, ARG obtains 28/31 while the PromptNode graph policy obtains 31/31. Under the conservative boundary that also removes task 114, ARG obtains 28/30 and the PromptNode variant obtains 30/30. These results support a scoped AQuA improvement claim, not a claim about all AQuA variants or noisy labels.

\paragraph{MMLU STEM transfer.}
On the MMLU STEM main97 slice, the PromptNode stack obtains 95/97 compared with 88/97 for ARG, with fix/harm 7/0 in the evidence table. The draft cost row is based on a 12-task cost probe: R425 estimates a combined main97 cost of 0.676454 for ARG direct plus PromptNode-stack style calls. This cost is marked as a probe estimate and must not be described as exact R306 accounting.

\paragraph{Non-STEM transfer.}
The broader mixed non-STEM result supports only a no-harm boundary: R396 reports ARG 41/48 and the retrained hybrid 41/48, with no harms but no positive delta. A targeted fresh DefinitionChallenge run gives a narrower positive result: R413/R414 reports ARG 21/24 versus DefinitionChallenge 22/24, with fix/harm/wrong-forward 1/0/0. The raw candidate pool alone is 21/24, so the improvement comes from graph selection rather than from a stronger plain requery candidate pool.

\paragraph{Controls and limitations of evidence.}
Plain requery is not enough to explain the positive targeted result: R316 plain requery on non-STEM40 has the same 37/40 accuracy as ARG and fix/harm 1/1. However, this does not yet establish broad transfer. The DefinitionChallenge result is a targeted nonmath result, the lifecycle trace is replayed from R413 outputs, and the external integrity audit is pending.
"""

    cases = r"""\section{Mechanism Case Studies}
\label{sec:cases}

R417 extracts three reproducible mechanism cases. In \texttt{MMLU-nonstem-moral\_disputes\_test-14}, ARG predicts A, while the DefinitionChallenge graph forwards C and matches the dataset label; this is the single fresh fix in R413. The active elements are ConceptDefinitionAnchorPN, AdversarialVerifierPN, OptionBindingPromptEdge, and ConsensusConflictResolverPN.

In \texttt{MMLU-nonstem-logical\_fallacies\_test-12}, the candidate would have changed an already correct ARG answer. The gate prunes the candidate, preserving the final answer. This case should be described carefully: the row also exposes parser and contract fragility, so it is a safety-prune case rather than a pure semantic-verifier proof.

At the aggregate level, R413 shows that graph selection matters: ARG is 21/24, the candidate pool is also 21/24, and the gated graph is 22/24. The trace replay in R419 records 121 lifecycle events, including 11 forward decisions, 13 prune events, and one upgrade event for the repair case.
"""

    limitations = r"""\section{Limitations}
\label{sec:limitations}

The current evidence supports a narrowed paper, not a fully submission-ready claim. First, the broad mixed non-STEM setting remains no-harm rather than positive. Second, the MMLU STEM cost is probe-estimated, not exact original R306 accounting. Third, R419 lifecycle traces are replay artifacts from R413 outputs, not independently instrumented runtime logs. Fourth, the external integrity audit is pending, so all draft claims must remain provisional.

These limitations shape the paper framing. The supported core is that typed PromptNodes and PromptEdges improve audited AQuA and MMLU STEM under ARG-Designer-matched settings, while targeted DefinitionChallenge graph selection provides a fresh nonmath positive result. We do not generalize the targeted nonmath result to all non-STEM multiple-choice tasks.
"""
    return {
        "method": method,
        "experimental_setup": experiments,
        "results": results,
        "case_studies": cases,
        "limitations": limitations,
    }


def build_draft_sections() -> Dict[str, Any]:
    section_text = _sections()
    return {
        "run_id": "R430",
        "title": "Draft bounded method/results sections",
        "claim_boundary": (
            "R430 drafts bounded LaTeX sections from verified assets. It does not authorize final paper claims."
        ),
        "no_api": True,
        "broad_api": False,
        "section_text": section_text,
        "section_files": {
            "method": "paper/sections/3_method.tex",
            "experimental_setup": "paper/sections/4_experimental_setup.tex",
            "results": "paper/sections/5_results.tex",
            "case_studies": "paper/sections/6_case_studies.tex",
            "limitations": "paper/sections/7_limitations.tex",
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R431_draft_claim_sanity_check",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R430 Draft Method/Results Sections",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Files",
        "",
    ]
    rows.extend(f"- `{key}`: `{path}`" for key, path in summary["section_files"].items())
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_draft_sections()
    for key, path in summary["section_files"].items():
        _write_text(path, summary["section_text"][key])
    summary.update({"output_dir": output_dir, "summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draft bounded paper method/results sections.")
    parser.add_argument("--output_dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
