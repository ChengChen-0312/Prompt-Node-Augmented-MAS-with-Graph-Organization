import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.offline_utility_selector import (
    build_contract_consensus_records,
    build_multi_contract_union_records,
    common_task_ids,
    load_prefix_result_sets,
    normalize_option,
)


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_audit_labels(paths: Iterable[str]) -> Dict[str, str]:
    labels: Dict[str, str] = {}
    for path in paths:
        for record in load_jsonl(path):
            labels[record["task_id"]] = str(record.get("clean_label", "unknown")).lower()
    return labels


def solved(prediction: Any, true_answer: Any) -> bool:
    return normalize_option(prediction) == normalize_option(true_answer)


def ratio_text(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}"


def summarize_variant_records(
    variant: str,
    records: List[Dict[str, Any]],
    audit_labels: Dict[str, str],
    notes: str = "",
) -> Dict[str, Any]:
    total = len(records)
    total_solved = 0
    baseline_solved = 0
    clean_total = 0
    clean_solved = 0
    noisy_total = 0
    noisy_solved = 0
    fixes = 0
    harms = 0
    clean_fixes = 0
    clean_harms = 0
    noisy_fixes = 0
    noisy_harms = 0
    switch_sources: Counter[str] = Counter()

    for record in records:
        task_id = record["task_id"]
        is_clean = audit_labels.get(task_id, "unknown") == "clean"
        record_solved = solved(record.get("predicted_answer"), record.get("true_answer"))
        record_baseline_solved = solved(
            record.get("baseline_prediction"), record.get("true_answer")
        )
        source = str(record.get("selected_source", "baseline"))
        if source != "baseline":
            switch_sources[source] += 1

        total_solved += int(record_solved)
        baseline_solved += int(record_baseline_solved)

        if is_clean:
            clean_total += 1
            clean_solved += int(record_solved)
        else:
            noisy_total += 1
            noisy_solved += int(record_solved)

        if not record_baseline_solved and record_solved:
            fixes += 1
            clean_fixes += int(is_clean)
            noisy_fixes += int(not is_clean)
        if record_baseline_solved and not record_solved:
            harms += 1
            clean_harms += int(is_clean)
            noisy_harms += int(not is_clean)

    return {
        "variant": variant,
        "total": total,
        "solved": total_solved,
        "overall": ratio_text(total_solved, total),
        "clean_total": clean_total,
        "clean_solved": clean_solved,
        "clean": ratio_text(clean_solved, clean_total),
        "noisy_or_ambiguous_total": noisy_total,
        "noisy_or_ambiguous_solved": noisy_solved,
        "noisy_or_ambiguous": ratio_text(noisy_solved, noisy_total),
        "baseline_solved": baseline_solved,
        "delta_vs_baseline": total_solved - baseline_solved,
        "fixes": fixes,
        "harms": harms,
        "fix_harm": f"{fixes}/{harms}",
        "clean_fixes": clean_fixes,
        "clean_harms": clean_harms,
        "clean_fix_harm": f"{clean_fixes}/{clean_harms}",
        "noisy_fixes": noisy_fixes,
        "noisy_harms": noisy_harms,
        "noisy_fix_harm": f"{noisy_fixes}/{noisy_harms}",
        "switches": sum(switch_sources.values()),
        "switch_sources": dict(sorted(switch_sources.items())),
        "notes": notes,
    }


def format_delta(delta: int) -> str:
    return f"+{delta}" if delta >= 0 else str(delta)


def format_markdown_table(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "| Variant | Overall | Clean | Noisy/Ambiguous | Delta vs ARG | Fix/Harm | Clean Fix/Harm | Switches | Notes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {variant} | `{overall}` | `{clean}` | `{noisy}` | `{delta}` | `{fix_harm}` | `{clean_fix_harm}` | `{switches}` | {notes} |".format(
                variant=row["variant"],
                overall=row["overall"],
                clean=row["clean"],
                noisy=row["noisy_or_ambiguous"],
                delta=format_delta(int(row["delta_vs_baseline"])),
                fix_harm=row["fix_harm"],
                clean_fix_harm=row["clean_fix_harm"],
                switches=row["switches"],
                notes=row.get("notes", ""),
            )
        )
    return "\n".join(lines)


def build_prediction_records(
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
    task_ids: Iterable[str],
    source: str,
) -> List[Dict[str, Any]]:
    records = []
    for task_id in task_ids:
        baseline_record = result_sets["baseline"][task_id]
        ensemble_record = result_sets["ensemble"][task_id]
        baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
        ensemble_prediction = normalize_option(ensemble_record.get("predicted_answer"))
        prediction = baseline_prediction if source == "baseline" else ensemble_prediction
        true_answer = baseline_record.get("true_answer") or ensemble_record.get("true_answer")
        records.append(
            {
                "task_id": task_id,
                "true_answer": true_answer,
                "predicted_answer": prediction,
                "baseline_prediction": baseline_prediction,
                "ensemble_prediction": ensemble_prediction,
                "selected_source": (
                    "baseline"
                    if source == "baseline" or prediction == baseline_prediction
                    else "ensemble"
                ),
            }
        )
    return records


def add_slice_prefix(records: List[Dict[str, Any]], prefix: str) -> List[Dict[str, Any]]:
    for record in records:
        record["slice_prefix"] = prefix
    return records


def collect_variant_records(prefixes: List[str], base_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    variants: Dict[str, List[Dict[str, Any]]] = {
        "ARG baseline": [],
        "PN result ensemble": [],
        "R034 single-router contract": [],
        "Single-candidate contract": [],
        "Single-conservative contract": [],
        "Single-calibrated contract": [],
        "R035 direct-consensus only": [],
        "R035 strong-contract only": [],
        "R035 multi-contract only": [],
        "R035 multi-contract + invalid fallback": [],
        "Sensitivity: strong>=2": [],
        "Sensitivity: strict direct>=3 strong>=4": [],
    }

    for prefix in prefixes:
        result_sets = load_prefix_result_sets(prefix, base_dir)
        task_ids = common_task_ids(result_sets)
        variants["ARG baseline"].extend(
            add_slice_prefix(build_prediction_records(result_sets, task_ids, "baseline"), prefix)
        )
        variants["PN result ensemble"].extend(
            add_slice_prefix(build_prediction_records(result_sets, task_ids, "ensemble"), prefix)
        )
        for label, method_key in [
            ("R034 single-router contract", "router"),
            ("Single-candidate contract", "candidate"),
            ("Single-conservative contract", "conservative"),
            ("Single-calibrated contract", "calibrated"),
        ]:
            variants[label].extend(
                add_slice_prefix(
                    build_contract_consensus_records(
                        result_sets,
                        task_ids,
                        method_key=method_key,
                        use_invalid_fallback=False,
                    ),
                    prefix,
                )
            )
        variants["R035 direct-consensus only"].extend(
            add_slice_prefix(
                build_multi_contract_union_records(
                    result_sets,
                    task_ids,
                    min_direct_methods=2,
                    min_strong_methods=999,
                    use_invalid_fallback=False,
                ),
                prefix,
            )
        )
        variants["R035 strong-contract only"].extend(
            add_slice_prefix(
                build_multi_contract_union_records(
                    result_sets,
                    task_ids,
                    min_direct_methods=999,
                    min_strong_methods=3,
                    use_invalid_fallback=False,
                ),
                prefix,
            )
        )
        variants["R035 multi-contract only"].extend(
            add_slice_prefix(
                build_multi_contract_union_records(
                    result_sets,
                    task_ids,
                    min_direct_methods=2,
                    min_strong_methods=3,
                    use_invalid_fallback=False,
                ),
                prefix,
            )
        )
        variants["R035 multi-contract + invalid fallback"].extend(
            add_slice_prefix(
                build_multi_contract_union_records(
                    result_sets,
                    task_ids,
                    min_direct_methods=2,
                    min_strong_methods=3,
                    use_invalid_fallback=True,
                ),
                prefix,
            )
        )
        variants["Sensitivity: strong>=2"].extend(
            add_slice_prefix(
                build_multi_contract_union_records(
                    result_sets,
                    task_ids,
                    min_direct_methods=2,
                    min_strong_methods=2,
                    use_invalid_fallback=False,
                ),
                prefix,
            )
        )
        variants["Sensitivity: strict direct>=3 strong>=4"].extend(
            add_slice_prefix(
                build_multi_contract_union_records(
                    result_sets,
                    task_ids,
                    min_direct_methods=3,
                    min_strong_methods=4,
                    use_invalid_fallback=False,
                ),
                prefix,
            )
        )
    return variants


def build_ablation_rows(
    prefixes: List[str],
    audit_files: List[str],
    base_dir: str,
) -> List[Dict[str, Any]]:
    audit_labels = load_audit_labels(audit_files)
    variants = collect_variant_records(prefixes, base_dir)
    notes = {
        "ARG baseline": "reference",
        "PN result ensemble": "label-free result majority",
        "R034 single-router contract": "single PN trace",
        "Single-candidate contract": "single PN graph-selection trace",
        "Single-conservative contract": "single abstention trace",
        "Single-calibrated contract": "single utility-gated trace",
        "R035 direct-consensus only": "router agrees with direct agents in >=2 PN variants",
        "R035 strong-contract only": "same strong router option in >=3 PN variants",
        "R035 multi-contract only": "pure virtual-node mechanism",
        "R035 multi-contract + invalid fallback": "mechanism plus invalid-answer fallback",
        "Sensitivity: strong>=2": "lower strong-contract threshold",
        "Sensitivity: strict direct>=3 strong>=4": "stricter agreement threshold",
    }
    return [
        summarize_variant_records(label, records, audit_labels, notes=notes.get(label, ""))
        for label, records in variants.items()
    ]


def write_json(path: str, payload: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PromptNode contract ablation tables.")
    parser.add_argument("--prefix", action="append", dest="prefixes", default=[])
    parser.add_argument("--audit-file", action="append", dest="audit_files", default=[])
    parser.add_argument("--base-dir", default=os.path.dirname(__file__))
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--summary-json", required=True)
    args = parser.parse_args()

    prefixes = args.prefixes or ["aqua_100", "aqua_next100"]
    audit_files = args.audit_files or [
        os.path.join(args.base_dir, "aqua_100_option_binding_audit.jsonl"),
        os.path.join(args.base_dir, "aqua_next100_option_binding_audit.jsonl"),
    ]
    rows = build_ablation_rows(prefixes, audit_files, args.base_dir)
    title = "# AQuA First200 PromptNode Contract Ablation Table\n\n"
    body = format_markdown_table(rows)
    write_text(args.output_md, title + body + "\n")
    write_json(args.summary_json, {"prefixes": prefixes, "audit_files": audit_files, "rows": rows})
    print(json.dumps({"output_md": args.output_md, "summary_json": args.summary_json}, indent=2))


if __name__ == "__main__":
    main()
