import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from datasets.aqua_dataset import aqua_data_process
from mas_framework.llm.llm_registry import LLMRegistry


AUDIT_FIELDS = {
    "clean_label": "ambiguous",
    "gold_binding_status": "unknown",
    "target_preserved": False,
    "option_mismatch": False,
    "rationale_issue": "unknown",
    "faithful_answer": "UNKNOWN",
    "confidence": "low",
    "brief_reason": "",
}


def _compact(value: Any, limit: int = 1800) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + " ...[truncated]"


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _gold_option_text(raw_record: Dict[str, Any], processed_record: Dict[str, Any]) -> str:
    gold = raw_record.get("correct", processed_record.get("answer", ""))
    for option in raw_record.get("options", []):
        if str(option).strip().startswith(f"{gold})"):
            return str(option).strip()
    return str(gold)


def build_audit_prompt(
    processed_record: Dict[str, Any],
    raw_record: Dict[str, Any],
    task_id: str,
    result_records: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, str]]:
    result_records = result_records or {}
    result_lines = []
    for name, record in result_records.items():
        result_lines.append(
            f"[{name}] predicted={record.get('predicted_answer')}; solved={record.get('is_solved')}; "
            f"raw={_compact(record.get('raw_response'), 900)}"
        )
    result_block = "\n".join(result_lines) if result_lines else "- no prior model results"

    system_prompt = (
        "You audit AQuA multiple-choice math rows for option-binding quality. "
        "You are not helping a model answer this row. You judge whether the dataset gold label "
        "and official rationale are clean, noisy, or ambiguous. Do not use hidden task ids or "
        "memorized dataset answers; use only the visible task, choices, gold label, rationale, "
        "and optional model outputs."
    )
    user_prompt = (
        f"task_id: {task_id}\n"
        f"question: {raw_record.get('question', processed_record.get('task', ''))}\n"
        f"choices: {json.dumps(raw_record.get('options', []), ensure_ascii=False)}\n"
        f"gold label: {raw_record.get('correct', processed_record.get('answer'))}\n"
        f"gold option text: {_gold_option_text(raw_record, processed_record)}\n"
        f"official rationale: {raw_record.get('rationale', processed_record.get('step', ''))}\n\n"
        f"prior model outputs:\n{result_block}\n\n"
        "Return only JSON with exactly these keys:\n"
        "{\n"
        '  "clean_label": "clean|noisy|ambiguous",\n'
        '  "gold_binding_status": "exact|equivalent|unsupported|contradictory|unknown",\n'
        '  "target_preserved": true,\n'
        '  "option_mismatch": false,\n'
        '  "rationale_issue": "none|arithmetic_error|shifted_target|underspecified_event|invalid_logic|unknown",\n'
        '  "faithful_answer": "A|B|C|D|E|NONE|UNKNOWN",\n'
        '  "confidence": "high|medium|low",\n'
        '  "brief_reason": "one sentence"\n'
        "}\n"
        "Before choosing clean/noisy/ambiguous, verify every arithmetic equation and algebra step in the "
        "official rationale. If the rationale writes an equation such as a=b*x and then solves x incorrectly, "
        "mark arithmetic_error and contradictory/noisy unless a different correct rationale still supports the gold option. "
        "If prior model outputs consistently derive a value absent from choices, evaluate whether the choice set itself is mismatched.\n"
        "Clean means the gold option is exactly or equivalently supported by the stated target and rationale. "
        "Noisy means the rationale/gold contradicts arithmetic, solves a shifted target, or the faithful answer is absent. "
        "Ambiguous means the row is under-specified or multiple interpretations are plausible."
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def parse_audit_response(text: str) -> Dict[str, Any]:
    raw_text = text or ""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, flags=re.S | re.I)
    json_text = match.group(1) if match else raw_text
    if not match:
        brace_match = re.search(r"\{.*\}", raw_text, flags=re.S)
        if brace_match:
            json_text = brace_match.group(0)
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError:
        parsed = {}

    audit = dict(AUDIT_FIELDS)
    audit.update({key: parsed.get(key, default) for key, default in AUDIT_FIELDS.items()})
    audit["raw_audit_response"] = raw_text
    return audit


def _detect_linear_equation_error(text: str) -> Optional[str]:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    for line_index, line in enumerate(lines):
        equation = re.match(
            r"^(?P<a>-?\d+(?:\.\d+)?)\s*=\s*(?P<b>-?\d+(?:\.\d+)?)\s*\*?\s*x\.?$",
            line,
            flags=re.I,
        )
        if not equation:
            continue
        for solution_line in lines[line_index + 1: line_index + 4]:
            solution = re.match(
                r"^(?:(?P<c1>-?\d+(?:\.\d+)?)\s*=\s*x|x\s*=\s*(?P<c2>-?\d+(?:\.\d+)?))\.?$",
                solution_line,
                flags=re.I,
            )
            if not solution:
                continue
            a = float(equation.group("a"))
            b = float(equation.group("b"))
            if b == 0:
                continue
            stated = float(solution.group("c1") or solution.group("c2"))
            expected = a / b
            if abs(expected - stated) > 1e-6:
                return f"Rationale solves {a:g} = {b:g}x as x={stated:g}, but x={expected:g}."
    return None


def make_audit_record(
    task_id: str,
    processed_record: Dict[str, Any],
    raw_record: Dict[str, Any],
    audit_json: Dict[str, Any],
    result_records: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    record = {
        "task_id": task_id,
        "question": processed_record.get("task"),
        "gold_answer": processed_record.get("answer"),
        "gold_rationale": processed_record.get("step"),
        "raw_options": raw_record.get("options", []),
        "results": result_records or {},
    }
    for key in AUDIT_FIELDS:
        record[key] = audit_json.get(key, AUDIT_FIELDS[key])
    if "raw_audit_response" in audit_json:
        record["raw_audit_response"] = audit_json["raw_audit_response"]

    deterministic_reason = _detect_linear_equation_error(record.get("gold_rationale", ""))
    if deterministic_reason:
        record["clean_label"] = "noisy"
        record["gold_binding_status"] = "contradictory"
        record["rationale_issue"] = "arithmetic_error"
        record["confidence"] = "high"
        record["brief_reason"] = deterministic_reason
        record["deterministic_override"] = True
    else:
        record["deterministic_override"] = False
    return record


def summarize_audits(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "total": len(records),
        "clean_label_counts": dict(Counter(record.get("clean_label", "unknown") for record in records)),
        "rationale_issue_counts": dict(Counter(record.get("rationale_issue", "unknown") for record in records)),
        "gold_binding_status_counts": dict(Counter(record.get("gold_binding_status", "unknown") for record in records)),
        "confidence_counts": dict(Counter(record.get("confidence", "unknown") for record in records)),
    }


def _load_prior_results(paths: List[str]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    loaded = {}
    for path in paths:
        name = os.path.splitext(os.path.basename(path))[0]
        loaded[name] = {row["task_id"]: row for row in _load_jsonl(path)}
    return loaded


async def run_audit(args):
    raw_rows = _load_jsonl(args.dataset_path)
    processed_rows = aqua_data_process(raw_rows)
    with open(args.task_split_path, encoding="utf-8") as f:
        split = json.load(f)
    indices = split["test_indices"]
    if args.limit:
        indices = indices[: args.limit]

    prior = _load_prior_results(args.result_file)
    llm = LLMRegistry.get(args.llm_name)

    records = []
    for idx in indices:
        task_id = f"task_{idx}"
        result_records = {
            name: rows[task_id]
            for name, rows in prior.items()
            if task_id in rows
        }
        messages = build_audit_prompt(processed_rows[idx], raw_rows[idx], task_id, result_records)
        response = await llm.agen(messages, max_tokens=args.max_tokens, temperature=0.0)
        audit = parse_audit_response(response)
        records.append(make_audit_record(task_id, processed_rows[idx], raw_rows[idx], audit, result_records))

        with open(args.output_file, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = summarize_audits(records)
    os.makedirs(os.path.dirname(args.summary_file), exist_ok=True)
    with open(args.summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def parse_args():
    parser = argparse.ArgumentParser(description="Audit AQuA option-binding quality")
    parser.add_argument("--dataset_path", default="../../datasets/AQuA/AQuA.jsonl")
    parser.add_argument("--task_split_path", default="./task_split_aqua.json")
    parser.add_argument("--llm_name", default="gpt-4o-2024-08-06")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output_file", default="aqua_sync20_option_binding_audit.jsonl")
    parser.add_argument("--summary_file", default="res_logs/aqua_sync20_option_binding_audit_summary.json")
    parser.add_argument("--result_file", action="append", default=[])
    parser.add_argument("--max_tokens", type=int, default=500)
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run_audit(parse_args()))
