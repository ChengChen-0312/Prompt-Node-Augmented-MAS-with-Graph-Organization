import argparse
import json
import os
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_SOURCE_JSONL = (
    "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/"
    "datasets/MMLU/test.jsonl"
)

DEFAULT_STEM_SUBJECTS = [
    "abstract_algebra",
    "college_mathematics",
    "high_school_mathematics",
    "elementary_mathematics",
    "high_school_statistics",
    "college_physics",
    "high_school_physics",
    "college_chemistry",
    "high_school_chemistry",
    "college_computer_science",
    "high_school_computer_science",
    "machine_learning",
    "electrical_engineering",
    "astronomy",
    "conceptual_physics",
]

VALID_OPTION_LABELS = ["A", "B", "C", "D"]


def load_jsonl_records(path: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def _normalize_choices(raw_choices: Any) -> List[List[str]]:
    if isinstance(raw_choices, dict):
        raw_choices = [[label, value] for label, value in raw_choices.items()]
    choices: List[List[str]] = []
    for item in raw_choices or []:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        label = str(item[0]).strip().upper()
        text = str(item[1]).strip()
        choices.append([label, text])
    choices.sort(key=lambda pair: VALID_OPTION_LABELS.index(pair[0]) if pair[0] in VALID_OPTION_LABELS else 99)
    labels = [label for label, _ in choices]
    if labels != VALID_OPTION_LABELS:
        raise ValueError(f"Expected A-D choices, got {labels}")
    return choices


def _question_with_options(question: str, choices: Sequence[Sequence[str]]) -> str:
    if all(f"Option {label}:" in question for label, _ in choices):
        return question.strip()
    option_lines = [f"Option {label}: {text}" for label, text in choices]
    return "\n".join([question.strip()] + option_lines).strip()


def normalize_jsonl_record(record: Dict[str, Any]) -> Dict[str, Any]:
    metadata = record.get("metadata") or {}
    choices = _normalize_choices(metadata.get("choices") or record.get("choices"))
    subject = str(metadata.get("subject") or record.get("subject") or "").strip()
    task_id = str(record.get("id") or record.get("task_id") or "").strip()
    answer = str(record.get("answer") or record.get("correct_answer") or "").strip().upper()
    if len(answer) > 1:
        answer = answer[0]
    if answer not in VALID_OPTION_LABELS:
        raise ValueError(f"Invalid answer label for {task_id}: {answer!r}")
    if not subject:
        raise ValueError(f"Missing MMLU subject for {task_id}")
    if not task_id:
        raise ValueError("Missing MMLU task id")

    question = _question_with_options(str(record.get("question") or record.get("task") or ""), choices)
    source_index = metadata.get("source_index", record.get("source_index", 0))
    try:
        source_index = int(source_index)
    except (TypeError, ValueError):
        source_index = 0

    return {
        "dataset": "mmlu",
        "task_id": task_id,
        "subject": subject,
        "question": question,
        "task": question,
        "answer": answer,
        "option_labels": [label for label, _ in choices],
        "options": choices,
        "source_file": metadata.get("source_file", record.get("source_file", "")),
        "source_file_format": metadata.get("source_file_format", record.get("source_file_format", "")),
        "source_index": source_index,
    }


def build_transfer_split(
    records: Iterable[Dict[str, Any]],
    subjects: Optional[Sequence[str]] = None,
    max_per_subject: int = 12,
    limit: int = 100,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if max_per_subject <= 0:
        raise ValueError("max_per_subject must be positive")
    if limit <= 0:
        raise ValueError("limit must be positive")

    selected_subjects = list(subjects or DEFAULT_STEM_SUBJECTS)
    subject_set = set(selected_subjects)
    grouped: Dict[str, List[Dict[str, Any]]] = {subject: [] for subject in selected_subjects}
    seen = set()

    for raw_record in records:
        try:
            normalized = normalize_jsonl_record(raw_record)
        except ValueError:
            continue
        subject = normalized["subject"]
        task_id = normalized["task_id"]
        if subject not in subject_set or task_id in seen:
            continue
        grouped[subject].append(normalized)
        seen.add(task_id)

    for subject in selected_subjects:
        grouped[subject].sort(key=lambda item: (item["source_index"], item["task_id"]))

    selected: List[Dict[str, Any]] = []
    for offset in range(max_per_subject):
        for subject in selected_subjects:
            candidates = grouped[subject]
            if offset < len(candidates):
                selected.append(candidates[offset])
                if len(selected) >= limit:
                    break
        if len(selected) >= limit:
            break

    subject_counts = {
        subject: count
        for subject, count in Counter(item["subject"] for item in selected).items()
        if count > 0
    }
    summary = {
        "dataset": "mmlu",
        "split_name": "mmlu_stem_transfer100",
        "total_tasks": len(selected),
        "subject_count": len(subject_counts),
        "subject_counts": subject_counts,
        "subjects": selected_subjects,
        "max_per_subject": max_per_subject,
        "limit": limit,
        "option_labels": VALID_OPTION_LABELS,
        "task_ids": [item["task_id"] for item in selected],
        "claim_boundary": (
            "Data-preparation only. This split does not contain any ARG or PromptNode "
            "accuracy claim until same-model evaluation traces are generated."
        ),
    }
    return selected, summary


def write_jsonl(path: str, records: Sequence[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def render_report(summary: Dict[str, Any]) -> str:
    lines = [
        "# MMLU STEM Transfer Split",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Total tasks: `{summary['total_tasks']}`",
        f"- Subject count: `{summary['subject_count']}`",
        f"- Option labels: `{', '.join(summary['option_labels'])}`",
        f"- Max per subject: `{summary['max_per_subject']}`",
        f"- Limit: `{summary['limit']}`",
        "",
        "| Subject | Count |",
        "| --- | ---: |",
    ]
    for subject in summary["subjects"]:
        count = summary["subject_counts"].get(subject, 0)
        if count:
            lines.append(f"| `{subject}` | `{count}` |")
    lines.extend(
        [
            "",
            "Next step: run ARG-Designer and PromptNode variants on this fixed split with "
            "`gpt-4o-2024-08-06` after quota is restored, then audit option-binding before "
            "turning any result into a paper claim.",
            "",
        ]
    )
    return "\n".join(lines)


def write_split_artifacts(
    records: Sequence[Dict[str, Any]],
    summary: Dict[str, Any],
    source_jsonl: str,
    output_jsonl: str,
    split_file: str,
    summary_json: str,
    report_md: str,
) -> None:
    split = {
        "dataset": "mmlu",
        "split_name": summary["split_name"],
        "source_jsonl": source_jsonl,
        "records_jsonl": output_jsonl,
        "test_indices": list(range(len(records))),
        "task_ids": summary["task_ids"],
        "subjects": summary["subjects"],
        "max_per_subject": summary["max_per_subject"],
        "limit": summary["limit"],
        "option_labels": summary["option_labels"],
        "claim_boundary": summary["claim_boundary"],
    }
    enriched_summary = dict(summary)
    enriched_summary.update(
        {
            "source_jsonl": source_jsonl,
            "output_jsonl": output_jsonl,
            "split_file": split_file,
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )

    write_jsonl(output_jsonl, records)
    write_json(split_file, split)
    write_json(summary_json, enriched_summary)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(enriched_summary))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a deterministic MMLU STEM transfer split.")
    parser.add_argument("--source-jsonl", default=DEFAULT_SOURCE_JSONL)
    parser.add_argument("--output-jsonl", default="experiment/mmlu/mmlu_stem_transfer100.jsonl")
    parser.add_argument("--split-file", default="experiment/mmlu/task_split_mmlu_stem_transfer100.json")
    parser.add_argument("--summary-json", default="experiment/mmlu/res_logs/mmlu_stem_transfer_split_summary.json")
    parser.add_argument("--report-md", default="experiment/mmlu/run_logs/mmlu_stem_transfer_split_report.md")
    parser.add_argument("--max-per-subject", type=int, default=12)
    parser.add_argument("--limit", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_jsonl_records(args.source_jsonl)
    selected, summary = build_transfer_split(
        records,
        subjects=DEFAULT_STEM_SUBJECTS,
        max_per_subject=args.max_per_subject,
        limit=args.limit,
    )
    write_split_artifacts(
        selected,
        summary,
        source_jsonl=args.source_jsonl,
        output_jsonl=args.output_jsonl,
        split_file=args.split_file,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(
        f"Wrote {len(selected)} MMLU STEM transfer tasks across "
        f"{summary['subject_count']} subjects to {args.output_jsonl}"
    )


if __name__ == "__main__":
    main()
