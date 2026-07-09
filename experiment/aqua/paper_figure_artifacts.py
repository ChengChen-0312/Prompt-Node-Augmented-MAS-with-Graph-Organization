import argparse
import csv
import html
import json
import math
import os
import shutil
import subprocess
from typing import Any, Dict, Iterable, List, Optional, Tuple


MAIN_ABLATION_VARIANTS = [
    ("ARG baseline", "arg", "ARG baseline", "primary baseline"),
    ("PN result ensemble", "ensemble", "PN result ensemble", "complementarity; harms exist"),
    ("R034 single-router contract", "r034", "R034 single-router contract", "single-view PN signal"),
    ("R035 multi-contract only", "r035_pure", "R035 multi-contract only", "main mechanism candidate"),
    (
        "R035 multi-contract + invalid fallback",
        "r035_full",
        "R035 multi-contract + invalid fallback",
        "full system; fallback separated",
    ),
]


def load_json(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _parse_fraction(value: str) -> Tuple[int, int]:
    left, right = str(value).split("/", 1)
    return int(left), int(right)


def _rate(value: str) -> float:
    numerator, denominator = _parse_fraction(value)
    return numerator / denominator * 100 if denominator else 0.0


def _variant_rows_by_name(ablation_summary: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {row.get("variant", ""): row for row in ablation_summary.get("rows", [])}


def _main_row(
    key: str,
    display: str,
    claim_role: str,
    source: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "key": key,
        "display": display,
        "overall": source["overall"],
        "overall_rate": _rate(source["overall"]),
        "clean": source["clean"],
        "clean_rate": _rate(source["clean"]),
        "noisy_or_ambiguous": source["noisy_or_ambiguous"],
        "noisy_or_ambiguous_rate": _rate(source["noisy_or_ambiguous"]),
        "delta_vs_baseline": source["delta_vs_baseline"],
        "fix_harm": source["fix_harm"],
        "clean_fix_harm": source["clean_fix_harm"],
        "switches": source["switches"],
        "claim_role": claim_role,
    }


def build_main_result_rows(
    ablation_summary: Dict[str, Any],
    objective_summary: Optional[Dict[str, Any]] = None,
    margin_summary: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    by_name = _variant_rows_by_name(ablation_summary)
    rows: List[Dict[str, Any]] = []
    for variant_name, key, display, claim_role in MAIN_ABLATION_VARIANTS:
        if variant_name in by_name:
            rows.append(_main_row(key, display, claim_role, by_name[variant_name]))

    if objective_summary:
        summary = objective_summary["posthoc_audit_summary"]
        rows.append(
            _main_row(
                "r039",
                "R039 objective-guided selector",
                "rejected as main due clean harm",
                summary,
            )
        )
    if margin_summary:
        summary = margin_summary["posthoc_audit_summary"]
        margin = margin_summary.get("min_score_margin")
        display = f"R040 margin-gated objective" if margin is None else f"R040 margin-gated objective"
        rows.append(_main_row("r040", display, "safe system candidate", summary))
    return rows


def _latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "{": r"\{",
        "}": r"\}",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def render_main_results_latex_table(rows: List[Dict[str, Any]]) -> str:
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{AQuA first200 exploratory results under the ARG-Designer-compatible evaluation setup. Clean and noisy/ambiguous splits come from post-hoc option-binding audit; selector decisions do not use audit labels.}",
        r"\label{tab:aqua_first200_main_results}",
        r"\small",
        r"\begin{tabular}{lccccccc}",
        r"\toprule",
        r"Variant & Overall & Clean & Noisy/Amb. & $\Delta$ & Fix/Harm & Clean F/H & Switches \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            "{} & {} & {} & {} & {:+d} & {} & {} & {} \\\\".format(
                _latex_escape(row["display"]),
                _latex_escape(row["overall"]),
                _latex_escape(row["clean"]),
                _latex_escape(row["noisy_or_ambiguous"]),
                int(row["delta_vs_baseline"]),
                _latex_escape(row["fix_harm"]),
                _latex_escape(row["clean_fix_harm"]),
                _latex_escape(row["switches"]),
            )
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            "",
            r"\vspace{0.25em}",
            r"\begin{minipage}{0.97\textwidth}",
            r"\footnotesize Claim roles: "
            + "; ".join(
                f"{_latex_escape(row['display'])}: {_latex_escape(row['claim_role'])}" for row in rows
            )
            + r".",
            r"\end{minipage}",
            r"\end{table*}",
            "",
        ]
    )
    return "\n".join(lines)


def write_main_results_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = [
        "key",
        "display",
        "overall",
        "overall_rate",
        "clean",
        "clean_rate",
        "noisy_or_ambiguous",
        "noisy_or_ambiguous_rate",
        "delta_vs_baseline",
        "fix_harm",
        "clean_fix_harm",
        "switches",
        "claim_role",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _svg_text(x: float, y: float, text: Any, size: int = 12, anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Times, DejaVu Serif, serif" '
        f'font-size="{size}" text-anchor="{anchor}" fill="#222">{html.escape(str(text))}</text>'
    )


def _svg_rect(x: float, y: float, width: float, height: float, fill: str, stroke: str = "none") -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(width, 0):.1f}" height="{height:.1f}" '
        f'fill="{fill}" stroke="{stroke}" />'
    )


def render_main_results_svg(rows: List[Dict[str, Any]]) -> str:
    width = 980
    row_height = 44
    top = 26
    left = 240
    plot_width = 600
    height = top + row_height * len(rows) + 80
    max_rate = max(
        [float(row["overall_rate"]) for row in rows] + [float(row["clean_rate"]) for row in rows]
    )
    axis_min = 75
    axis_max = max(90, int(math.ceil(max_rate / 5.0) * 5))
    axis_span = axis_max - axis_min
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white" />',
    ]
    for tick in range(axis_min, axis_max + 1, 5):
        x = left + (tick - axis_min) / axis_span * plot_width
        parts.append(f'<line x1="{x:.1f}" y1="{top - 8}" x2="{x:.1f}" y2="{height - 52}" stroke="#ddd" />')
        parts.append(_svg_text(x, height - 34, tick, 10, anchor="middle"))
    parts.append(_svg_text(left + plot_width / 2, height - 12, "Accuracy (%)", 11, anchor="middle"))
    colors = {"overall": "#4C78A8", "clean": "#F58518"}
    for idx, row in enumerate(rows):
        y = top + idx * row_height
        parts.append(_svg_text(12, y + 18, row["display"], 11))
        for bar_idx, metric in enumerate(["overall", "clean"]):
            rate = float(row[f"{metric}_rate"])
            x0 = left
            y0 = y + 3 + bar_idx * 18
            bar_w = (rate - axis_min) / axis_span * plot_width
            parts.append(_svg_rect(x0, y0, bar_w, 13, colors[metric]))
            parts.append(_svg_text(x0 + max(bar_w, 2) + 5, y0 + 10, f"{rate:.1f}", 10))
    legend_y = height - 58
    parts.append(_svg_rect(left, legend_y, 12, 12, colors["overall"]))
    parts.append(_svg_text(left + 18, legend_y + 11, "Overall", 10))
    parts.append(_svg_rect(left + 92, legend_y, 12, 12, colors["clean"]))
    parts.append(_svg_text(left + 110, legend_y + 11, "Clean audit split", 10))
    parts.append("</svg>")
    return "\n".join(parts)


def build_contract_coverage_rows(objective_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    summary = objective_summary["summary"]
    total = int(summary["total_tasks"])
    switch_total = int(summary.get("r035_pure_switch_tasks", 0))
    excluded = ", ".join(objective_summary.get("objective_inputs_exclude", [])) or "gold/audit labels"

    def row(label: str, numerator: int, denominator: int) -> Dict[str, Any]:
        return {
            "label": label,
            "value": f"{numerator}/{denominator}",
            "rate": numerator / denominator * 100 if denominator else 0.0,
            "note": f"objective excludes: {excluded}",
        }

    return [
        row("Positive top-score", int(summary["positive_top_score_tasks"]), total),
        row("Top-score ties", int(summary["top_score_ties"]), total),
        row("R035 top-option agreement", int(summary["r035_switch_top_option_agreement"]), switch_total),
        row(
            "R035 unique-top agreement",
            int(summary["r035_switch_unique_top_option_agreement"]),
            switch_total,
        ),
    ]


def render_contract_coverage_svg(rows: List[Dict[str, Any]]) -> str:
    width = 760
    left = 230
    top = 26
    row_height = 42
    plot_width = 430
    height = top + len(rows) * row_height + 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white" />',
    ]
    for tick in range(0, 101, 25):
        x = left + tick / 100 * plot_width
        parts.append(f'<line x1="{x:.1f}" y1="{top - 8}" x2="{x:.1f}" y2="{height - 42}" stroke="#ddd" />')
        parts.append(_svg_text(x, height - 22, tick, 10, anchor="middle"))
    for idx, row in enumerate(rows):
        y = top + idx * row_height
        rate = float(row["rate"])
        parts.append(_svg_text(12, y + 20, row["label"], 11))
        parts.append(_svg_rect(left, y + 5, rate / 100 * plot_width, 18, "#54A24B"))
        parts.append(_svg_text(left + rate / 100 * plot_width + 6, y + 19, f"{row['value']} ({rate:.1f}%)", 10))
    parts.append(_svg_text(left + plot_width / 2, height - 2, "Rate (%)", 11, anchor="middle"))
    parts.append("</svg>")
    return "\n".join(parts)


def render_latex_includes() -> str:
    return "\n".join(
        [
            r"% === Fig. 3: AQuA first200 exploratory result comparison ===",
            r"\begin{figure*}[t]",
            r"    \centering",
            r"    \includegraphics[width=0.95\textwidth]{figures/fig3_aqua_first200_results.pdf}",
            r"    \caption{Exploratory AQuA first200 accuracy under the ARG-Designer-compatible setup. The clean split contains 167 audited clean rows. R035 multi-contract only isolates the virtual PromptNode mechanism; R035 full additionally includes invalid-answer fallback.}",
            r"    \label{fig:aqua_first200_results}",
            r"\end{figure*}",
            "",
            r"% === Fig. 4: Contract-coverage objective diagnostics ===",
            r"\begin{figure}[t]",
            r"    \centering",
            r"    \includegraphics[width=0.48\textwidth]{figures/fig4_contract_coverage.pdf}",
            r"    \caption{Label-free contract-coverage objective diagnostics on AQuA first200. The objective covers all three R035 clean-switch options at the top-option level, but ties remain frequent, motivating margin-gated or trained graph selection.}",
            r"    \label{fig:contract_coverage}",
            r"\end{figure}",
            "",
            r"% === Table: AQuA first200 main results ===",
            r"\input{figures/TABLE_aqua_first200_main_results.tex}",
            "",
        ]
    )


def write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def maybe_convert_svg_to_pdf(svg_path: str, pdf_path: str) -> bool:
    converter = shutil.which("rsvg-convert")
    if not converter:
        return False
    subprocess.run([converter, "-f", "pdf", "-o", pdf_path, svg_path], check=True)
    return True


def build_artifacts(
    ablation_summary_path: str,
    objective_summary_path: str,
    ungated_summary_path: str,
    margin_summary_path: str,
    output_dir: str,
) -> Dict[str, Any]:
    ablation_summary = load_json(ablation_summary_path)
    objective_summary = load_json(objective_summary_path)
    ungated_summary = load_json(ungated_summary_path)
    margin_summary = load_json(margin_summary_path)

    rows = build_main_result_rows(ablation_summary, ungated_summary, margin_summary)
    coverage_rows = build_contract_coverage_rows(objective_summary)

    os.makedirs(output_dir, exist_ok=True)
    paths = {
        "main_csv": os.path.join(output_dir, "aqua_first200_main_results.csv"),
        "main_table": os.path.join(output_dir, "TABLE_aqua_first200_main_results.tex"),
        "fig3_svg": os.path.join(output_dir, "fig3_aqua_first200_results.svg"),
        "fig3_pdf": os.path.join(output_dir, "fig3_aqua_first200_results.pdf"),
        "fig4_svg": os.path.join(output_dir, "fig4_contract_coverage.svg"),
        "fig4_pdf": os.path.join(output_dir, "fig4_contract_coverage.pdf"),
        "latex_includes": os.path.join(output_dir, "latex_includes.tex"),
        "data_json": os.path.join(output_dir, "aqua_first200_paper_figure_data.json"),
    }

    write_main_results_csv(paths["main_csv"], rows)
    write_text(paths["main_table"], render_main_results_latex_table(rows))
    write_text(paths["fig3_svg"], render_main_results_svg(rows))
    write_text(paths["fig4_svg"], render_contract_coverage_svg(coverage_rows))
    write_text(paths["latex_includes"], render_latex_includes())
    write_text(paths["data_json"], json.dumps({"main_results": rows, "contract_coverage": coverage_rows}, indent=2))
    fig3_pdf = maybe_convert_svg_to_pdf(paths["fig3_svg"], paths["fig3_pdf"])
    fig4_pdf = maybe_convert_svg_to_pdf(paths["fig4_svg"], paths["fig4_pdf"])
    return {"paths": paths, "fig3_pdf": fig3_pdf, "fig4_pdf": fig4_pdf}


def main() -> None:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    parser = argparse.ArgumentParser(description="Generate paper figures/tables for AQuA first200 PromptNode results.")
    parser.add_argument(
        "--ablation-summary",
        default=os.path.join(base_dir, "experiment/aqua/res_logs/aqua_first200_contract_ablation_summary.json"),
    )
    parser.add_argument(
        "--objective-summary",
        default=os.path.join(base_dir, "experiment/aqua/res_logs/aqua_first200_contract_graph_objective_summary.json"),
    )
    parser.add_argument(
        "--ungated-summary",
        default=os.path.join(base_dir, "experiment/aqua/res_logs/aqua_first200_objective_guided_selector_summary.json"),
    )
    parser.add_argument(
        "--margin-summary",
        default=os.path.join(base_dir, "experiment/aqua/res_logs/aqua_first200_margin3_objective_guided_selector_summary.json"),
    )
    parser.add_argument("--output-dir", default=os.path.join(base_dir, "figures"))
    args = parser.parse_args()

    result = build_artifacts(
        args.ablation_summary,
        args.objective_summary,
        args.ungated_summary,
        args.margin_summary,
        args.output_dir,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
