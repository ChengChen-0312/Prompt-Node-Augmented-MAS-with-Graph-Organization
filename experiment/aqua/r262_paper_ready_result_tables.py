from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Tuple


def parse_accuracy(value: str) -> Tuple[int, int]:
    left, right = str(value).strip().split("/", 1)
    return int(left), int(right)


def build_result_table(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    arg = next(row for row in rows if row["run_id"] == "ARG")
    arg_correct, _ = parse_accuracy(arg["accuracy"])
    arg_cost = float(arg.get("cost") or 0.0)
    table: List[Dict[str, Any]] = []
    for row in rows:
        correct, total = parse_accuracy(row["accuracy"])
        cost = float(row.get("cost") or 0.0)
        out = dict(row)
        out.update(
            {
                "correct": correct,
                "total": total,
                "accuracy_rate": round(correct / total, 6) if total else None,
                "delta_vs_arg_correct": correct - arg_correct,
                "cost_ratio_vs_arg": round(cost / arg_cost, 6) if arg_cost else None,
                "correct_per_dollar": round(correct / cost, 6) if cost else None,
            }
        )
        table.append(out)
    return table


def assess_cost_boundary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    normalized = []
    for row in rows:
        out = dict(row)
        if "correct" not in out or "total" not in out:
            out["correct"], out["total"] = parse_accuracy(out["accuracy"])
        if out.get("correct_per_dollar") is None:
            cost = float(out.get("cost") or 0.0)
            out["correct_per_dollar"] = out["correct"] / cost if cost else None
        normalized.append(out)
    best_correct = max(int(row["correct"]) for row in normalized)
    best_accuracy_rows = [row for row in normalized if int(row["correct"]) == best_correct]
    best_accuracy = best_accuracy_rows[0]
    fresh_rows = [
        row for row in normalized if row.get("fresh_integrated") and row.get("run_id") != "ARG"
    ]
    best_fresh_cost = min(fresh_rows, key=lambda row: float(row.get("cost") or 1e9)) if fresh_rows else {}
    cost_normalized_rows = [row for row in normalized if row.get("correct_per_dollar") is not None]
    best_cost_normalized = max(cost_normalized_rows, key=lambda row: float(row["correct_per_dollar"]))
    r065 = next((row for row in normalized if row.get("run_id") == "R065"), {})
    return {
        "best_accuracy_run": best_accuracy.get("run_id"),
        "best_accuracy_runs": [row.get("run_id") for row in best_accuracy_rows],
        "best_accuracy": f"{best_accuracy.get('correct')}/{best_accuracy.get('total')}",
        "best_fresh_cost_run": best_fresh_cost.get("run_id"),
        "best_cost_normalized_run": best_cost_normalized.get("run_id"),
        "r065_is_expensive_teacher": bool(r065)
        and not bool(r065.get("fresh_integrated"))
        and float(r065.get("cost") or 0.0) > 2.5,
    }


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl_first(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                return json.loads(line)
    return {}


def build_default_rows(repo_root: str) -> List[Dict[str, Any]]:
    aqua = os.path.join(repo_root, "experiment", "aqua")
    arg = load_jsonl_first(os.path.join(aqua, "res_logs", "aqua_tail34_arg_baseline_summary.jsonl"))
    r065 = load_json(os.path.join(aqua, "res_logs", "aqua_tail34_objective_guided_selector_summary.json"))
    r068 = load_json(os.path.join(aqua, "res_logs", "aqua_tail34_r068_selective_multiview_summary.json"))
    r069 = load_json(os.path.join(aqua, "res_logs", "aqua_tail34_r069_integrated_selective_multiview_summary.json"))
    r072 = load_json(os.path.join(aqua, "res_logs", "aqua_tail34_r072_integrated_cascade_summary.json"))
    r147 = load_json(os.path.join(aqua, "res_logs", "aqua_tail34_r147_frozen_selector_replay_summary.json"))

    r068_cost = r068.get("cost_estimate", {})
    return [
        {
            "run_id": "ARG",
            "name": "ARG tail34 baseline",
            "accuracy": f"{arg['solved_tasks']}/{arg['total_tasks']}",
            "fix_harm": "0/0",
            "clean_fix_harm": "0/0",
            "cost": float(arg["cost"]),
            "fresh_integrated": True,
            "claim_boundary": "baseline",
        },
        {
            "run_id": "R065",
            "name": "objective-guided multi-view teacher",
            "accuracy": r065["summary"]["overall"],
            "fix_harm": r065["summary"]["fix_harm"],
            "clean_fix_harm": r065["posthoc_audit_summary"]["clean_fix_harm"],
            "cost": float(r068_cost["full_multiview_cost"]),
            "fresh_integrated": False,
            "claim_boundary": "expensive replay teacher",
        },
        {
            "run_id": "R068",
            "name": "selective multi-view replay",
            "accuracy": r068["summary"]["overall"],
            "fix_harm": r068["summary"]["fix_harm"],
            "clean_fix_harm": r068["summary"]["clean_fix_harm"],
            "cost": float(r068_cost["estimated_cost"]),
            "fresh_integrated": False,
            "claim_boundary": r068["claim_boundary"],
        },
        {
            "run_id": "R069",
            "name": "fresh integrated selective multi-view",
            "accuracy": r069["overall"],
            "fix_harm": r069["fix_harm"],
            "clean_fix_harm": r069["clean_fix_harm"],
            "cost": float(r069["cost"]),
            "fresh_integrated": True,
            "claim_boundary": r069.get("boundary", "fresh integrated"),
        },
        {
            "run_id": "R072",
            "name": "fresh integrated cascade",
            "accuracy": r072["overall"],
            "fix_harm": r072["fix_harm"],
            "clean_fix_harm": r072["clean_fix_harm"],
            "cost": float(r072["cost"]),
            "fresh_integrated": True,
            "claim_boundary": r072.get("boundary", "fresh integrated cascade"),
        },
        {
            "run_id": "R147",
            "name": "frozen selector replay",
            "accuracy": r147["selected_accuracy"],
            "fix_harm": r147["fix_harm"],
            "clean_fix_harm": r147["clean_fix_harm"],
            "cost": float(r147["selected_estimated_cost"]),
            "fresh_integrated": False,
            "claim_boundary": "frozen selector replay",
        },
    ]


def run_table_export(summary_json: str, report_md: str, repo_root: str) -> Dict[str, Any]:
    rows = build_result_table(build_default_rows(repo_root))
    boundary = assess_cost_boundary(rows)
    summary = {
        "run_id": "R262",
        "title": "AQuA paper-ready result tables",
        "claim_boundary": "No-API table export only; supports paper framing, not new accuracy claims.",
        "no_api": True,
        "rows": rows,
        "cost_boundary": boundary,
        "next": "R263 R065-distilled low-cost selector search",
    }
    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    lines = [
        "# R262 AQuA Paper-Ready Result Tables",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Run | Accuracy | Delta vs ARG | Fix/Harm | Clean Fix/Harm | Cost | Cost x ARG | Boundary |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| `{row['run_id']}` {row['name']} | `{row['accuracy']}` | `{row['delta_vs_arg_correct']}` | `{row['fix_harm']}` | `{row['clean_fix_harm']}` | `${row['cost']:.6f}` | `{row['cost_ratio_vs_arg']}` | {row['claim_boundary']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary Assessment",
            "",
            f"- Best accuracy run: `{summary['cost_boundary']['best_accuracy_run']}`",
            f"- Best fresh-cost run: `{summary['cost_boundary']['best_fresh_cost_run']}`",
            f"- Best cost-normalized run: `{summary['cost_boundary']['best_cost_normalized_run']}`",
            f"- R065 is expensive teacher: `{summary['cost_boundary']['r065_is_expensive_teacher']}`",
            "",
            "## Interpretation",
            "",
            "R065 remains the best AQuA accuracy teacher, but it is not the deployment method. The next step is to distill its trigger behavior into a cheaper selector and evaluate that selector without API.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export AQuA paper-ready result tables.")
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    parser.add_argument("--repo_root", default=os.getcwd())
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_table_export(
        summary_json=args.summary_json,
        report_md=args.report_md,
        repo_root=args.repo_root,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
