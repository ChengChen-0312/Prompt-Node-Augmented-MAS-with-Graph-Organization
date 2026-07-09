from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from typing import Any, Dict, List

import torch
from torch_geometric.data import Data

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.args import Args
from experiment import process_dataset as gdata
from experiment.model import ARGDesigner
from experiment.mmlu.mmlu_prompt_set import ROLE_DESCRIPTION


DEFAULT_MANIFEST = "experiment/mmlu/promptedge_targets/mmlu_r183_promptedge_targets.jsonl"
DEFAULT_OUTPUT_DIR = "experiment/PromptEdgeData_mmlu_r183"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r184_promptedge_training_dry_run_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r184_promptedge_training_dry_run_report.md"


def record_to_pyg_data(record: Dict[str, Any]) -> Data:
    data = Data()
    roles = list(record["roles"])
    data.x = [
        {
            "role": role,
            "constraint": ROLE_DESCRIPTION.get(role, ""),
        }
        for role in roles
    ]
    edges = record.get("edges", [])
    data.edge_index = (
        torch.tensor(edges, dtype=torch.long).t().contiguous()
        if edges
        else torch.zeros((2, 0), dtype=torch.long)
    )
    data.num_nodes = len(roles)
    data.question = record.get("question", "")
    data.task = record.get("question", "")
    data.mode = "PromptEdgeTarget"
    data.is_correct = bool(record.get("is_correct", True))
    data.target_kind = record.get("target_kind", "")
    data.source_graph_path = record.get("source_graph_path", "")
    data.source_question_hash = record.get("source_question_hash", "")
    data.promptedge_meta = list(record.get("promptedge_meta", []))
    data.decision_exposure_policy = record.get("decision_exposure_policy", "terminal")
    return data


def materialize_manifest(manifest_jsonl: str, output_dir: str) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    for stale in glob.glob(os.path.join(output_dir, "mmlu_pe_*_True.pt")):
        os.remove(stale)

    materialized = 0
    unique_questions = set()
    with open(manifest_jsonl, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            data = record_to_pyg_data(record)
            q_hash = record.get("source_question_hash", f"{idx:04d}")
            unique_questions.add(q_hash)
            out_path = os.path.join(output_dir, f"mmlu_pe_{idx:04d}_{q_hash[:10]}_True.pt")
            torch.save(data, out_path)
            materialized += 1

    return {
        "manifest_jsonl": manifest_jsonl,
        "output_dir": output_dir,
        "materialized_graphs": materialized,
        "unique_questions": len(unique_questions),
    }


def run_forward_dry_run(data_dir: str, sample_size: int = 24, batch_size: int = 2) -> Dict[str, Any]:
    args = Args().update_args()
    args.dataset = "mmlu"
    args.dataset_name = "mmlu"
    args.data_dir = data_dir
    args.device = "cpu"
    args.batch_size = batch_size
    args.num_workers = 0
    args.dataset_sample_size = sample_size
    args.epochs = 1
    args.save_model = False
    args.experiment_path = "experiment/mmlu/output/mmlu_r184_dry_run_no_save"
    args.model_name = "dry_run.pth"

    graph_dataset, _ = gdata.load_graph_dataset(args, pretrain=True)
    args.role_mapping = graph_dataset.role_to_id
    args.id_to_role = graph_dataset.id_to_role
    args.START_TOKEN_ID = len(args.role_mapping)
    args.END_TOKEN_ID = len(args.role_mapping) + 1

    data_statistics = gdata.get_data_statistics(graph_dataset)
    data_statistics["num_node_labels"] = len(args.role_mapping) + 2
    data_statistics["num_edge_labels"] = 1

    mapped_dataset = gdata.GraphListDataset(graph_dataset.graph_list, args)
    graphs = [mapped_dataset[i] for i in range(min(batch_size, len(mapped_dataset)))]
    task_embeddings = []
    for graph in graphs:
        emb = graph.graph.get("task_embedding")
        if isinstance(emb, torch.Tensor):
            task_embeddings.append(emb.float())
        else:
            task_embeddings.append(torch.tensor(emb).float())
    task_embedding = torch.stack(task_embeddings)

    model = ARGDesigner(args, data_statistics).to(args.device)
    model.eval()
    with torch.no_grad():
        log_ll, role_accuracy = model(graphs, task_embedding)
        loss = -torch.mean(log_ll)
        sample_graphs = model.sample(
            num_samples=1,
            batch_size=1,
            task_embedding=task_embedding[0],
            question_id=0,
            vis=False,
        )

    pn_roles = {"PN_Memory", "PN_Verifier", "PN_Router"}
    role_mapping_keys = set(args.role_mapping.keys())
    return {
        "data_dir": data_dir,
        "sample_size_requested": sample_size,
        "dataset_graphs_loaded": len(graph_dataset),
        "batch_size": len(graphs),
        "role_mapping_size": len(args.role_mapping),
        "pn_roles_present": sorted(pn_roles.intersection(role_mapping_keys)),
        "pn_roles_missing": sorted(pn_roles - role_mapping_keys),
        "data_statistics": data_statistics,
        "finite_forward_loss": bool(torch.isfinite(loss).item()),
        "forward_loss": float(loss.item()),
        "role_accuracy": float(role_accuracy),
        "sample_graph_count": len(sample_graphs),
        "sample_generation_ok": len(sample_graphs) == 1,
        "sample_role_mapping_contains_pn": pn_roles.issubset(role_mapping_keys),
    }


def old_checkpoint_role_mapping_size(config_path: str) -> int:
    if not os.path.exists(config_path):
        return 0
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return len(cfg.get("role_mapping", {}))


def run(
    manifest_jsonl: str,
    output_dir: str,
    summary_json: str,
    report_md: str,
    sample_size: int,
    batch_size: int,
) -> Dict[str, Any]:
    materialized = materialize_manifest(manifest_jsonl, output_dir)
    dry_run = run_forward_dry_run(output_dir, sample_size=sample_size, batch_size=batch_size)
    old_size = old_checkpoint_role_mapping_size(
        "experiment/mmlu/output/mmlu_arg_base_model_r159/configuration.txt"
    )
    summary = {
        "run_id": "R184",
        "title": "MMLU PN-capable graph-policy training dry-run",
        "claim_boundary": (
            "Training-path dry-run only. No API evaluation, no trained checkpoint claim, "
            "and no PromptNode/PromptEdge accuracy claim."
        ),
        "no_api": True,
        "broad_api": False,
        "materialized": materialized,
        "dry_run": dry_run,
        "old_mmlu_arg_checkpoint_role_mapping_size": old_size,
        "old_checkpoint_direct_finetune_compatible": old_size == dry_run["role_mapping_size"],
        "requires_pn_capable_pretrain_or_expanded_checkpoint": old_size != dry_run["role_mapping_size"],
        "next_action": (
            "Run a short PN-capable pretraining job from the materialized PromptEdge data, "
            "then audit generated graphs before any MMLU transfer API smoke."
        ),
    }

    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    dry = summary["dry_run"]
    mat = summary["materialized"]
    return "\n".join(
        [
            "# R184 MMLU PN-Capable Training Dry-Run",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Materialization",
            "",
            f"- Materialized graphs: `{mat['materialized_graphs']}`",
            f"- Unique questions: `{mat['unique_questions']}`",
            f"- Output dir: `{mat['output_dir']}`",
            "",
            "## Forward Dry-Run",
            "",
            f"- Dataset graphs loaded: `{dry['dataset_graphs_loaded']}`",
            f"- Role mapping size: `{dry['role_mapping_size']}`",
            f"- PN roles present: `{dry['pn_roles_present']}`",
            f"- Finite forward loss: `{dry['finite_forward_loss']}`",
            f"- Forward loss: `{dry['forward_loss']:.4f}`",
            f"- Role accuracy: `{dry['role_accuracy']:.2f}`",
            f"- Sample generation ok: `{dry['sample_generation_ok']}`",
            "",
            "## Compatibility",
            "",
            f"- Old MMLU ARG checkpoint role mapping size: `{summary['old_mmlu_arg_checkpoint_role_mapping_size']}`",
            f"- Direct finetune compatible with PN role mapping: `{summary['old_checkpoint_direct_finetune_compatible']}`",
            f"- Requires PN-capable pretrain or expanded checkpoint: `{summary['requires_pn_capable_pretrain_or_expanded_checkpoint']}`",
            "",
            "## Next",
            "",
            summary["next_action"],
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run MMLU PN-capable graph-policy training path.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST)
    parser.add_argument("--output_dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--sample_size", type=int, default=24)
    parser.add_argument("--batch_size", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run(
        manifest_jsonl=args.manifest_jsonl,
        output_dir=args.output_dir,
        summary_json=args.summary_json,
        report_md=args.report_md,
        sample_size=args.sample_size,
        batch_size=args.batch_size,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
