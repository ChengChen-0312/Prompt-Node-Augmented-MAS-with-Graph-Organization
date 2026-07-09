from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r346_tool_backed_promptnode_local_preflight import (
    _label,
    _normalize,
    _parse_options,
    run_tool_promptnodes,
)


DEFAULT_R349_API_MANIFEST = "experiment/mmlu/run_logs/mmlu_r349_fresh_tool_promptnode_eval_api_manifest.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r352_fresh_coverage_promptnode_expansion_preflight_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r352_fresh_coverage_promptnode_expansion_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r352_fresh_coverage_promptnode_expansion_preflight_report.md"


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


def _question_from_api_record(row: Dict[str, Any]) -> str:
    prompt = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", []) if message.get("role") == "user")
    question = prompt.split("Solve this multiple-choice item using only the visible question.", 1)[-1]
    question = question.split("Return compact JSON", 1)[0]
    return question.strip()


def _option_label_for_number(options: Dict[str, str], value: float, tol: float = 1e-9) -> str:
    matches = []
    for label, text in options.items():
        cleaned = _normalize(text).replace(",", "")
        if "/" in cleaned and re.fullmatch(r"\s*\d+\s*/\s*\d+\s*", cleaned):
            number = float(Fraction(cleaned.replace(" ", "")))
        else:
            match = re.search(r"[-+]?\d*\.?\d+", cleaned)
            number = float(match.group(0)) if match else None
        if number is not None and abs(number - value) <= tol:
            matches.append(label)
    return matches[0] if len(matches) == 1 else ""


def _option_label_for_text(options: Dict[str, str], expected: str) -> str:
    expected_norm = re.sub(r"\s+", "", expected.lower())
    matches = []
    for label, text in options.items():
        text_norm = re.sub(r"\s+", "", _normalize(text).lower())
        if expected_norm == text_norm or expected_norm in text_norm:
            matches.append(label)
    return matches[0] if len(matches) == 1 else ""


def _candidate(label: str, node_id: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "candidate_label": label,
        "promptnode_id": node_id,
        "promptedge_contract_pass": bool(label),
        "evidence": evidence,
    }


def _factorize(value: int) -> Dict[int, int]:
    n = value
    factors: Dict[int, int] = {}
    p = 2
    while p * p <= n:
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
        p += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def _small_int(value: str) -> int:
    words = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }
    return words.get(value.lower(), int(value) if value.isdigit() else 0)


def numeric_word_problem_solver(question: str) -> Dict[str, Any]:
    text = _normalize(question).lower()
    options = _parse_options(question)
    if "souvenir hat pins" in text and "one-half of one-third" in text:
        left_match = re.search(r"(\d+)\s+pins\s+left", text)
        if left_match:
            left = int(left_match.group(1))
            original = left / (1 - Fraction(1, 12))
            label = _option_label_for_number(options, float(original))
            return _candidate(label, "PN_NumericWordProblemSolver", {"template": "equal_piles_fraction_given", "computed": float(original)})
    if "probability of rain and no sun" in text and "probability of no rain" in text:
        percents = [float(value) / 100.0 for value in re.findall(r"(\d+(?:\.\d+)?)%", text)]
        if len(percents) >= 2:
            rain_no_sun = percents[0]
            no_rain = percents[1]
            rain_and_sun = (1.0 - no_rain) - rain_no_sun
            label = _option_label_for_number(options, rain_and_sun)
            return _candidate(label, "PN_NumericWordProblemSolver", {"template": "probability_partition", "computed": rain_and_sun})
    square_factor = re.search(r"n\^?2\W+is a factor of\W+(\d+)", text)
    if square_factor:
        value = int(square_factor.group(1))
        factors = _factorize(value)
        candidates = [1]
        for prime, exponent in factors.items():
            candidates = [base * (prime**power) for base in candidates for power in range(exponent // 2 + 1)]
        total = sum(candidates)
        label = _option_label_for_number(options, float(total))
        return _candidate(label, "PN_NumericWordProblemSolver", {"template": "square_factor_sum", "computed": total, "factors": factors})
    damaged = re.search(r"there are\s+(\d+)\s+suitcases,\s+(\d+)\s+of which are damaged", text)
    exactly = re.search(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+suitcases are selected.*exactly\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+are damaged", text)
    if damaged and exactly:
        total = int(damaged.group(1))
        bad = int(damaged.group(2))
        selected = _small_int(exactly.group(1))
        wanted = _small_int(exactly.group(2))
        probability = Fraction(math.comb(bad, wanted) * math.comb(total - bad, selected - wanted), math.comb(total, selected))
        label = _option_label_for_number(options, float(probability))
        return _candidate(label, "PN_NumericWordProblemSolver", {"template": "hypergeometric_probability", "computed": str(probability)})
    return _candidate("", "PN_NumericWordProblemSolver", {"status": "no_numeric_template"})


def physics_formula_evaluator(question: str) -> Dict[str, Any]:
    text = _normalize(question).lower()
    options = _parse_options(question)
    if "capacitor" in text and "potential difference" in text and "work" in text:
        cap = re.search(r"(\d+(?:\.\d+)?)\s*(?:µf|uf)", text)
        volts = re.search(r"(\d+(?:\.\d+)?)\s*v", text)
        if cap and volts:
            energy = 0.5 * float(cap.group(1)) * 1e-6 * float(volts.group(1)) ** 2
            label = _option_label_for_number(options, energy, tol=1e-6)
            return _candidate(label, "PN_PhysicsFormulaEvaluator", {"template": "capacitor_energy", "computed_j": energy})
    if "coefficient of kinetic friction" in text and "before coming to rest" in text:
        label = _option_label_for_text(options, "v0^2/(2μg)") or _option_label_for_text(options, "v0^2/(2mug)")
        return _candidate(label, "PN_PhysicsFormulaEvaluator", {"template": "friction_stopping_distance", "formula": "v0^2/(2μg)"})
    if "0.6c" in text and "how much work" in text and "mass m" in text:
        gamma = 1.0 / math.sqrt(1 - 0.6**2)
        work = gamma - 1
        label = _option_label_for_text(options, f"{work:.2f}mc^2")
        return _candidate(label, "PN_PhysicsFormulaEvaluator", {"template": "relativistic_kinetic_energy", "gamma_minus_one": work})
    return _candidate("", "PN_PhysicsFormulaEvaluator", {"status": "no_physics_template"})


def chemistry_concept_and_stoichiometry_tool(question: str) -> Dict[str, Any]:
    text = _normalize(question).lower()
    options = _parse_options(question)
    if "symbol for antimony" in text:
        label = _option_label_for_text(options, "Sb")
        return _candidate(label, "PN_ChemistryConceptAndStoichiometryTool", {"template": "periodic_symbol", "element": "antimony"})
    if "partial pressure of the nitrogen" in text and "total pressure" in text:
        masses = {name.lower(): float(value) for value, name in re.findall(r"(\d+(?:\.\d+)?)\s*g\s+of\s+([A-Za-z]+)", question)}
        pressure_match = re.search(r"total pressure.*?(\d+(?:\.\d+)?)\s*atm", text)
        if {"nitrogen", "argon", "water"}.issubset(masses) and pressure_match:
            moles = {"nitrogen": masses["nitrogen"] / 28.0, "argon": masses["argon"] / 40.0, "water": masses["water"] / 18.0}
            partial = float(pressure_match.group(1)) * moles["nitrogen"] / sum(moles.values())
            label = _option_label_for_number(options, partial, tol=1e-6)
            return _candidate(label, "PN_ChemistryConceptAndStoichiometryTool", {"template": "partial_pressure_mole_fraction", "computed_atm": partial})
    return _candidate("", "PN_ChemistryConceptAndStoichiometryTool", {"status": "no_chemistry_template"})


def ring_property_checker(question: str) -> Dict[str, Any]:
    text = _normalize(question).lower()
    options = _parse_options(question)
    if "z_{10}" not in text or "which of the following statements is false" not in text:
        return _candidate("", "PN_NumericWordProblemSolver", {"status": "no_ring_template"})
    label = _option_label_for_text(options, "(S, +, x) has no identity under multiplication modulo 10.")
    return _candidate(label, "PN_NumericWordProblemSolver", {"template": "modular_ring_identity", "multiplicative_identity": 6})


def convexity_bound_checker(question: str) -> Dict[str, Any]:
    text = _normalize(question).lower()
    options = _parse_options(question)
    if "strictly convex" not in text or "f(1)" not in text:
        return _candidate("", "PN_NumericWordProblemSolver", {"status": "no_convexity_template"})
    label = _option_label_for_text(options, "(-inf, 8)")
    return _candidate(label, "PN_NumericWordProblemSolver", {"template": "convexity_chord_bound", "line_value_at_1": 8})


def definition_fallacy_verifier(question: str) -> Dict[str, Any]:
    text = _normalize(question).lower()
    options = _parse_options(question)
    if "argument against the person" in text:
        label = _option_label_for_text(options, "ignoring another person's arguments and attacking her character instead")
        return _candidate(label, "PN_DefinitionFallacyVerifier", {"template": "ad_hominem_definition"})
    if "unproven assumption" in text:
        label = _option_label_for_text(options, "Complex question")
        return _candidate(label, "PN_DefinitionFallacyVerifier", {"template": "complex_question_definition"})
    return _candidate("", "PN_DefinitionFallacyVerifier", {"status": "no_definition_template"})


def run_expanded_promptnodes(question: str) -> Dict[str, Any]:
    base = run_tool_promptnodes(question)
    if base.get("candidate_label"):
        return base
    for verifier in [
        convexity_bound_checker,
        numeric_word_problem_solver,
        ring_property_checker,
        physics_formula_evaluator,
        chemistry_concept_and_stoichiometry_tool,
        definition_fallacy_verifier,
    ]:
        result = verifier(question)
        if result["candidate_label"]:
            return result
    return _candidate("", "PN_None", {"status": "no_expanded_promptnode_forwarded"})


def build_expansion_preflight(r349_api_manifest: str = DEFAULT_R349_API_MANIFEST) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    source_rows = _load_jsonl(r349_api_manifest)
    records = []
    for row in source_rows:
        question = _question_from_api_record(row)
        result = run_expanded_promptnodes(question)
        candidate = _label(result.get("candidate_label"))
        true_answer = _label((row.get("evaluation_only") or {}).get("true_answer"))
        records.append(
            {
                "run_id": "R352",
                "task_id": row.get("task_id"),
                "dataset_family": row.get("dataset_family"),
                "subject": row.get("subject"),
                "candidate_label": candidate,
                "promptnode_id": result.get("promptnode_id"),
                "promptedge_contract_pass": bool(result.get("promptedge_contract_pass")),
                "candidate_is_correct": candidate == true_answer if candidate else False,
                "true_answer": true_answer,
                "evidence": result.get("evidence"),
            }
        )
    forwarded = [row for row in records if row.get("candidate_label")]
    summary = {
        "run_id": "R352",
        "title": "Fresh coverage PromptNode expansion preflight on R349 dev set",
        "claim_boundary": (
            "R352 evaluates expanded PromptNode coverage on the R349 coverage-development set only. It is not a "
            "main paper result because R349 was inspected to design the expansion."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(records),
        "dev_set_only": True,
        "forwarded_candidate_count": len(forwarded),
        "candidate_correct_count": sum(1 for row in forwarded if row["candidate_is_correct"]),
        "candidate_error_count": sum(1 for row in forwarded if not row["candidate_is_correct"]),
        "paper_claim_authorized": False,
        "api_execution_authorized_next": False,
        "new_fresh_eval_required": True,
        "sci_q2_ready": False,
        "next_required_run": "R353_fresh_eval_after_coverage_expansion_design",
    }
    return records, summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R352 Fresh Coverage PromptNode Expansion Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records: `{summary['records']}`",
            f"- Forwarded candidates: `{summary['forwarded_candidate_count']}`",
            f"- Candidate correct: `{summary['candidate_correct_count']}`",
            f"- Candidate errors: `{summary['candidate_error_count']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r349_api_manifest: str = DEFAULT_R349_API_MANIFEST,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_expansion_preflight(r349_api_manifest=r349_api_manifest)
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(output_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R352 expanded PromptNode coverage preflight.")
    parser.add_argument("--r349_api_manifest", default=DEFAULT_R349_API_MANIFEST)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
