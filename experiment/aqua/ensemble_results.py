import argparse
import json
import os
from collections import Counter
from typing import Any, Dict, List, Optional


VALID_OPTIONS = {"A", "B", "C", "D", "E"}


def load_jsonl_by_task(path: str) -> Dict[str, Dict[str, Any]]:
    records = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            records[record["task_id"]] = record
    return records


def majority_vote_prediction(
    method_predictions: Dict[str, Optional[str]],
    method_order: List[str],
    tie_breaker: str,
) -> Optional[str]:
    votes = [
        method_predictions.get(method)
        for method in method_order
        if method_predictions.get(method) in VALID_OPTIONS
    ]
    if not votes:
        return None
    counts = Counter(votes)
    top_count = counts.most_common(1)[0][1]
    tied = {option for option, count in counts.items() if count == top_count}
    tie_prediction = method_predictions.get(tie_breaker)
    if tie_prediction in tied:
        return tie_prediction
    for method in method_order:
        prediction = method_predictions.get(method)
        if prediction in tied:
            return prediction
    return None


def build_ensemble_records(
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
    method_order: List[str],
    tie_breaker: str,
) -> List[Dict[str, Any]]:
    reference_name = method_order[0]
    reference = result_sets[reference_name]
    records = []
    for task_id, reference_record in reference.items():
        method_predictions = {
            method: result_sets.get(method, {}).get(task_id, {}).get("predicted_answer")
            for method in method_order
        }
        predicted = majority_vote_prediction(method_predictions, method_order, tie_breaker)
        true_answer = reference_record.get("true_answer")
        records.append({
            "task_id": task_id,
            "question": reference_record.get("question"),
            "true_answer": true_answer,
            "predicted_answer": predicted,
            "is_solved": predicted == true_answer,
            "method_predictions": method_predictions,
            "method_order": method_order,
            "tie_breaker": tie_breaker,
        })
    return records


def parse_method_file(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--method_file must use name=path")
    name, path = value.split("=", 1)
    if not name:
        raise argparse.ArgumentTypeError("method name cannot be empty")
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"result file not found: {path}")
    return name, path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a label-free ensemble from AQuA result JSONL files.")
    parser.add_argument("--method_file", action="append", type=parse_method_file, required=True)
    parser.add_argument("--tie_breaker", required=True)
    parser.add_argument("--output_file", required=True)
    parser.add_argument("--summary_file", required=True)
    args = parser.parse_args()

    method_order = [name for name, _path in args.method_file]
    if args.tie_breaker not in method_order:
        raise ValueError("--tie_breaker must be one of the method names")

    result_sets = {
        name: load_jsonl_by_task(path)
        for name, path in args.method_file
    }
    records = build_ensemble_records(result_sets, method_order, args.tie_breaker)

    with open(args.output_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    solved = sum(1 for record in records if record["is_solved"])
    summary = {
        "total_tasks": len(records),
        "solved_tasks": solved,
        "pass_at_1": solved / len(records) * 100 if records else 0.0,
        "method_order": method_order,
        "tie_breaker": args.tie_breaker,
        "detail_file": args.output_file,
    }
    os.makedirs(os.path.dirname(args.summary_file), exist_ok=True)
    with open(args.summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

