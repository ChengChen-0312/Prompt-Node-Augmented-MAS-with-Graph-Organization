import argparse
import json
import os
from typing import Any, Dict, Iterable, List


def load_jsonl_records(path: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_audit_labels(paths: Iterable[str]) -> Dict[str, str]:
    labels: Dict[str, str] = {}
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                task_id = record.get("task_id")
                clean_label = record.get("clean_label")
                if task_id and clean_label:
                    labels[str(task_id)] = str(clean_label)
    return labels


def _format_counts(counts: Dict[str, Any]) -> str:
    if not counts:
        return "none"
    pairs = []
    for option, count in sorted(counts.items(), key=lambda item: (-int(item[1]), str(item[0]))):
        pairs.append(f"{option}={count}")
    return ", ".join(pairs)


def _format_rule_evidence(features: Dict[str, Any]) -> str:
    parts = []
    direct_counts = features.get("direct_consensus_counts") or {}
    strong_counts = features.get("strong_option_counts") or {}
    if direct_counts:
        parts.append(f"direct-consensus {_format_counts(direct_counts)}")
    if strong_counts:
        parts.append(f"strong {_format_counts(strong_counts)}")
    return "; ".join(parts) if parts else "none"


def _format_method_contracts(features: Dict[str, Any]) -> str:
    method_features = features.get("method_features") or {}
    method_keys = features.get("method_keys") or sorted(method_features)
    parts = []
    for method_key in method_keys:
        feature = method_features.get(method_key) or {}
        option = feature.get("router_option") or "-"
        binding_status = feature.get("router_binding_status") or "WEAK"
        direct_count = feature.get("direct_majority_count", 0)
        match = "yes" if feature.get("router_matches_direct_majority") else "no"
        parts.append(f"{method_key}:{option}/{binding_status}/direct={direct_count}/match={match}")
    return "; ".join(parts) if parts else "none"


def _shorten_question(question: Any, max_chars: int = 180) -> str:
    text = " ".join(str(question or "").split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def build_case_studies(
    records: Iterable[Dict[str, Any]],
    audit_labels: Dict[str, str],
) -> List[Dict[str, Any]]:
    studies = []
    for record in records:
        task_id = str(record.get("task_id", ""))
        audit_label = audit_labels.get(task_id, "unknown")
        true_answer = record.get("true_answer")
        baseline_prediction = record.get("baseline_prediction")
        selected_prediction = record.get("predicted_answer")

        if audit_label != "clean":
            continue
        if record.get("selected_source") != "multi_contract_union":
            continue
        if selected_prediction != true_answer:
            continue
        if baseline_prediction == true_answer:
            continue

        features = record.get("selector_features") or {}
        studies.append(
            {
                "task_id": task_id,
                "slice_prefix": record.get("slice_prefix", ""),
                "case_type": "clean_fix",
                "audit_label": audit_label,
                "true_answer": true_answer,
                "baseline_prediction": baseline_prediction,
                "ensemble_prediction": record.get("ensemble_prediction"),
                "selected_prediction": selected_prediction,
                "selected_source": record.get("selected_source"),
                "rule_evidence": _format_rule_evidence(features),
                "method_contracts": _format_method_contracts(features),
                "question_short": _shorten_question(record.get("question")),
            }
        )
    return studies


def _md_cell(value: Any) -> str:
    text = str(value if value is not None else "")
    return " ".join(text.replace("|", "\\|").split())


def render_markdown(studies: List[Dict[str, Any]], title: str) -> str:
    lines = [
        f"# {title}",
        "",
        "**Claim boundary**: These are exploratory first200 case studies. They illustrate the R035 pure multi-contract PromptNode mechanism, but they are not held-out tail34 or transfer validation claims.",
        "",
        "## Clean Fix Table",
        "",
        "| Task | Slice | Audit | Gold | ARG | Ensemble | Selected | Evidence |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for study in studies:
        lines.append(
            "| {task_id} | {slice_prefix} | {audit_label} | {true_answer} | "
            "{baseline_prediction} | {ensemble_prediction} | {selected_prediction} | {rule_evidence} |".format(
                **{key: _md_cell(value) for key, value in study.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Per-View Contract Evidence",
            "",
            "| Task | PromptNode view contracts | Question excerpt |",
            "| --- | --- | --- |",
        ]
    )
    for study in studies:
        lines.append(
            "| {task_id} | {method_contracts} | {question_short} |".format(
                **{key: _md_cell(value) for key, value in study.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Observation: every listed row is clean under the option-binding audit, ARG is wrong, and R035 pure multi-contract PromptNode selection is correct.",
            "",
            "Interpretation: these cases support the mechanism-level story that multiple virtual PromptNode views can provide safe option-binding evidence beyond the ARG baseline.",
            "",
            "Next step: repeat this extraction on pre-registered tail34 and transfer multiple-choice math once same-model traces are available.",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: str, payload: Any) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def write_text(path: str, content: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract paper-ready PromptNode clean-fix case studies from selector results."
    )
    parser.add_argument(
        "--selector-file",
        default="aqua_first200_multi_contract_union_only_selector_results.jsonl",
    )
    parser.add_argument(
        "--audit-file",
        action="append",
        default=["aqua_100_option_binding_audit.jsonl", "aqua_next100_option_binding_audit.jsonl"],
    )
    parser.add_argument(
        "--output-md",
        default="run_logs/aqua_first200_multi_contract_case_studies.md",
    )
    parser.add_argument(
        "--output-json",
        default="res_logs/aqua_first200_multi_contract_case_studies.json",
    )
    parser.add_argument("--title", default="AQuA First200 R035 PromptNode Clean-Fix Case Studies")
    args = parser.parse_args()

    base_dir = os.path.dirname(__file__)
    selector_file = args.selector_file
    if not os.path.isabs(selector_file):
        selector_file = os.path.join(base_dir, selector_file)
    audit_files = [
        path if os.path.isabs(path) else os.path.join(base_dir, path)
        for path in args.audit_file
    ]
    output_md = args.output_md if os.path.isabs(args.output_md) else os.path.join(base_dir, args.output_md)
    output_json = (
        args.output_json if os.path.isabs(args.output_json) else os.path.join(base_dir, args.output_json)
    )

    records = load_jsonl_records(selector_file)
    audit_labels = load_audit_labels(audit_files)
    studies = build_case_studies(records, audit_labels)
    write_json(output_json, {"count": len(studies), "case_studies": studies})
    write_text(output_md, render_markdown(studies, args.title))
    print(f"case_studies={len(studies)}")
    print(f"wrote_json={output_json}")
    print(f"wrote_md={output_md}")


if __name__ == "__main__":
    main()
