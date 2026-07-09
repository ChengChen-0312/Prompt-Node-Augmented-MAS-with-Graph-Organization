from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from fractions import Fraction
from functools import reduce
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import sympy as sp


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R337_RESULTS = "experiment/mmlu/run_logs/mmlu_r337_prospective_selector_eval_expand24_results.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r346_tool_backed_promptnode_local_preflight_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r346_tool_backed_promptnode_local_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r346_tool_backed_promptnode_local_preflight_report.md"
VALID_LABELS = {"A", "B", "C", "D", "E"}


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


def _label(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text[:1] if text[:1] in VALID_LABELS else ""


def _normalize(text: str) -> str:
    return str(text or "").replace("–", "-").replace("−", "-").replace("—", "-")


def _visible_item(row: Dict[str, Any]) -> str:
    content = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", []) if message.get("role") == "user")
    content = re.sub(r"^Held-out MMLU multiple-choice item:\s*", "", content.strip())
    return content.split("\n\nPromptNode identities:", 1)[0].strip()


def _stem(item: str) -> str:
    return re.split(r"\n\s*Option\s+A\s*:", item, maxsplit=1, flags=re.I)[0]


def _parse_options(item: str) -> Dict[str, str]:
    matches = re.findall(r"Option\s+([A-E])\s*:\s*(.*?)(?=\n\s*Option\s+[A-E]\s*:|\Z)", item, flags=re.I | re.S)
    return {label.upper(): value.strip() for label, value in matches}


def _coord_pairs(text: str) -> List[Tuple[int, int]]:
    pairs = []
    for x, y in re.findall(r"\(\s*([+-]?\s*\d+)\s*,\s*([+-]?\s*\d+)\s*\)", _normalize(text)):
        pairs.append((int(x.replace(" ", "")), int(y.replace(" ", ""))))
    return pairs


def _single_coord(text: str) -> Optional[Tuple[int, int]]:
    coords = _coord_pairs(text)
    return coords[0] if len(coords) == 1 else None


def _option_with_integer(options: Dict[str, str], value: int) -> List[str]:
    labels = []
    for label, text in options.items():
        numbers = [int(match) for match in re.findall(r"(?<![A-Za-z])[-+]?\d+(?![A-Za-z])", _normalize(text))]
        if len(numbers) == 1 and numbers[0] == value:
            labels.append(label)
    return labels


def _candidate(label: str, node_id: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "candidate_label": label,
        "promptnode_id": node_id,
        "promptedge_contract_pass": bool(label),
        "evidence": evidence,
    }


def coordinate_transformer(item: str) -> Dict[str, Any]:
    text = _normalize(item).lower()
    if "reflect" not in text or "y = x" not in text:
        return _candidate("", "PN_CoordinateTransformer", {"status": "trigger_not_matched"})
    transformed = {(y, x) for x, y in _coord_pairs(_stem(item))}
    matches = []
    for label, option in _parse_options(item).items():
        coord = _single_coord(option)
        if coord in transformed:
            matches.append(label)
    label = matches[0] if len(matches) == 1 else ""
    return _candidate(
        label,
        "PN_CoordinateTransformer",
        {"status": "ok" if label else "no_unique_match", "transformed_points": sorted(transformed), "matched_labels": matches},
    )


def _prime_power(value: int) -> Tuple[int, int]:
    for p in range(2, int(math.sqrt(value)) + 2):
        n = value
        k = 0
        while n % p == 0:
            n //= p
            k += 1
        if n == 1 and k > 0:
            return p, k
    return value, 1


def _valuation(value: int, prime: int) -> int:
    k = 0
    while value and value % prime == 0:
        value //= prime
        k += 1
    return k if value == 1 else 0


def _partition_count(total: int, max_part: int) -> int:
    dp = [0] * (total + 1)
    dp[0] = 1
    for part in range(1, max_part + 1):
        for subtotal in range(part, total + 1):
            dp[subtotal] += dp[subtotal - part]
    return dp[total]


def finite_abelian_group_enumerator(item: str) -> Dict[str, Any]:
    text = _normalize(item).lower()
    if "abelian group" not in text or "order" not in text:
        return _candidate("", "PN_FiniteAbelianGroupEnumerator", {"status": "trigger_not_matched"})
    order_match = re.search(r"order\s+(\d+)", text)
    property_match = re.search(r"((?:x\s*\+\s*)+x)\s*=\s*0", text)
    if not order_match or not property_match:
        return _candidate("", "PN_FiniteAbelianGroupEnumerator", {"status": "parse_incomplete"})
    order = int(order_match.group(1))
    repeated_x = property_match.group(1).count("x")
    prime, rank = _prime_power(order)
    max_part = _valuation(repeated_x, prime)
    count = _partition_count(rank, max_part) if max_part else 0
    matches = _option_with_integer(_parse_options(item), count)
    label = matches[0] if len(matches) == 1 else ""
    return _candidate(
        label,
        "PN_FiniteAbelianGroupEnumerator",
        {"status": "ok" if label else "no_unique_match", "order": order, "prime": prime, "rank": rank, "exponent_bound": repeated_x, "count": count},
    )


def finite_field_derivative_analyzer(item: str) -> Dict[str, Any]:
    text = _normalize(item).lower()
    if "polynomial" not in text or "derivative" not in text:
        return _candidate("", "PN_FiniteFieldDerivativeAnalyzer", {"status": "trigger_not_matched"})
    field_match = re.search(r"z[_\s]*(\d+)", text)
    degree_match = re.search(r"degree\s+(?:less than or equal to|<=|at most)\s+(\d+)", text)
    if not field_match or not degree_match:
        return _candidate("", "PN_FiniteFieldDerivativeAnalyzer", {"status": "parse_incomplete"})
    prime = int(field_match.group(1))
    max_degree = int(degree_match.group(1))
    nullity = sum(1 for i in range(max_degree + 1) if i % prime == 0)
    rank = sum(1 for i in range(1, max_degree + 1) if i % prime != 0)
    matches = []
    for label, option in _parse_options(item).items():
        parsed = re.search(r"n\s*=\s*(\d+)\s+and\s+r\s*=\s*(\d+)", option, flags=re.I)
        if parsed and int(parsed.group(1)) == nullity and int(parsed.group(2)) == rank:
            matches.append(label)
    label = matches[0] if len(matches) == 1 else ""
    return _candidate(
        label,
        "PN_FiniteFieldDerivativeAnalyzer",
        {"status": "ok" if label else "no_unique_match", "field": prime, "max_degree": max_degree, "nullity": nullity, "rank": rank},
    )


def _split_species(side: str) -> List[str]:
    return [token.strip().replace("__", "").strip() for token in re.split(r"\s+\+\s+", side) if token.strip()]


def _canonical_species(species: str) -> str:
    return _normalize(species).replace(" ", "")


def _formula_and_charge(species: str) -> Tuple[str, int]:
    canonical = _canonical_species(species)
    charge_match = re.match(r"^(.*?)(\d*)([+-])$", canonical)
    if charge_match:
        base = charge_match.group(1)
        digits = charge_match.group(2)
        base_elements = re.findall(r"[A-Z][a-z]?", base)
        if digits and len(base_elements) == 1 and not re.search(r"\d", base):
            formula = base
            magnitude = int(digits)
        else:
            formula = base + digits
            magnitude = 1
        sign = 1 if charge_match.group(3) == "+" else -1
        return formula, sign * magnitude
    return canonical, 0


def _element_counts(formula: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for element, count in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        counts[element] = counts.get(element, 0) + int(count or "1")
    return counts


def _balance_reaction(equation_line: str) -> Tuple[List[str], List[int]]:
    left_text, right_text = re.split(r"<->|->|=>", _normalize(equation_line), maxsplit=1)
    left = _split_species(left_text)
    right = _split_species(right_text)
    species = left + right
    signs = [1] * len(left) + [-1] * len(right)
    parsed = []
    elements = set()
    for item in species:
        formula, charge = _formula_and_charge(item)
        counts = _element_counts(formula)
        elements.update(counts)
        parsed.append((counts, charge))
    rows = []
    for element in sorted(elements):
        rows.append([signs[i] * parsed[i][0].get(element, 0) for i in range(len(species))])
    rows.append([signs[i] * parsed[i][1] for i in range(len(species))])
    nullspace = sp.Matrix(rows).nullspace()
    if not nullspace:
        return species, []
    vector = nullspace[0]
    lcm = 1
    for value in vector:
        lcm = math.lcm(lcm, int(value.q))
    coeffs = [int(value * lcm) for value in vector]
    if any(value < 0 for value in coeffs):
        coeffs = [-value for value in coeffs]
    gcd = reduce(math.gcd, [abs(value) for value in coeffs if value])
    return species, [value // gcd for value in coeffs]


def redox_balance_linear_solver(item: str) -> Dict[str, Any]:
    text = _normalize(item)
    if "<->" not in text and "->" not in text and "=>" not in text:
        return _candidate("", "PN_RedoxBalanceLinearSolver", {"status": "trigger_not_matched"})
    equation_line = next((line for line in text.splitlines() if "<->" in line or "->" in line or "=>" in line), "")
    if not equation_line:
        return _candidate("", "PN_RedoxBalanceLinearSolver", {"status": "parse_incomplete"})
    species, coeffs = _balance_reaction(equation_line)
    if not coeffs:
        return _candidate("", "PN_RedoxBalanceLinearSolver", {"status": "balance_failed"})
    coefficient_by_species = {_canonical_species(item): coeffs[index] for index, item in enumerate(species)}
    matches = []
    checked: Dict[str, bool] = {}
    for label, option in _parse_options(item).items():
        ratio = re.search(r"The\s+(.+?)\s*:\s*(.+?)\s+ratio\s+is\s+(\d+)\s*:\s*(\d+)", _normalize(option), flags=re.I)
        if not ratio:
            continue
        left_species = _canonical_species(ratio.group(1))
        right_species = _canonical_species(ratio.group(2))
        expected = Fraction(int(ratio.group(3)), int(ratio.group(4)))
        actual = None
        if left_species in coefficient_by_species and right_species in coefficient_by_species:
            actual = Fraction(coefficient_by_species[left_species], coefficient_by_species[right_species])
        checked[label] = actual == expected
        if actual == expected:
            matches.append(label)
    label = matches[0] if len(matches) == 1 else ""
    return _candidate(
        label,
        "PN_RedoxBalanceLinearSolver",
        {"status": "ok" if label else "no_unique_match", "coefficients": coefficient_by_species, "checked_options": checked},
    )


def run_tool_promptnodes(item: str) -> Dict[str, Any]:
    for verifier in [
        coordinate_transformer,
        finite_abelian_group_enumerator,
        finite_field_derivative_analyzer,
        redox_balance_linear_solver,
    ]:
        result = verifier(item)
        if result["candidate_label"]:
            return result
    return _candidate("", "PN_None", {"status": "no_tool_forwarded"})


def build_local_preflight(r337_results: str = DEFAULT_R337_RESULTS) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    source_rows = [
        row
        for row in _load_jsonl(r337_results)
        if row.get("control_variant") == "selector_promptnode_promptedge_policy" and row.get("is_correct") is False
    ]
    records = []
    for row in source_rows:
        item = _visible_item(row)
        tool_result = run_tool_promptnodes(item)
        candidate = _label(tool_result.get("candidate_label"))
        true_answer = _label(row.get("true_answer"))
        baseline = _label(row.get("baseline_prediction"))
        records.append(
            {
                "run_id": "R346",
                "task_id": row.get("task_id"),
                "subject": row.get("subject"),
                "baseline_prediction": baseline,
                "true_answer": true_answer,
                "candidate_label": candidate,
                "promptnode_id": tool_result.get("promptnode_id"),
                "promptedge_contract_pass": bool(tool_result.get("promptedge_contract_pass")),
                "evidence": tool_result.get("evidence"),
                "candidate_is_correct": candidate == true_answer if candidate else False,
                "candidate_repairs_baseline": bool(candidate and candidate == true_answer and baseline != true_answer),
                "candidate_harms_baseline": bool(candidate and baseline == true_answer and candidate != true_answer),
            }
        )
    forwarded = [row for row in records if row["candidate_label"]]
    summary = {
        "run_id": "R346",
        "title": "Tool-backed PromptNode local preflight on R337 wrong tasks",
        "claim_boundary": (
            "R346 is a targeted no-API mechanism preflight on R337 wrong tasks. It shows whether deterministic "
            "PromptNodes can produce machine-checkable candidates, but it is not a held-out paper claim."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(records),
        "api_calls": 0,
        "forwarded_candidate_count": len(forwarded),
        "candidate_correct_count": sum(1 for row in records if row["candidate_is_correct"]),
        "candidate_repairs_baseline_count": sum(1 for row in records if row["candidate_repairs_baseline"]),
        "candidate_harms_baseline_count": sum(1 for row in records if row["candidate_harms_baseline"]),
        "uses_true_answers_in_tool": False,
        "uses_task_ids_or_known_wrong_items": False,
        "targeted_mechanism_probe": True,
        "prospective_replay_authorized_next": bool(records),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R347_tool_backed_promptnode_prospective_replay24",
    }
    return records, summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R346 Tool-Backed PromptNode Local Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records: `{summary['records']}`",
            f"- API calls: `{summary['api_calls']}`",
            f"- Forwarded candidates: `{summary['forwarded_candidate_count']}`",
            f"- Candidate correct: `{summary['candidate_correct_count']}`",
            f"- Repairs baseline: `{summary['candidate_repairs_baseline_count']}`",
            f"- Harms baseline: `{summary['candidate_harms_baseline_count']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r337_results: str = DEFAULT_R337_RESULTS,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_local_preflight(r337_results=r337_results)
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(output_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R346 tool-backed PromptNode local preflight.")
    parser.add_argument("--r337_results", default=DEFAULT_R337_RESULTS)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
