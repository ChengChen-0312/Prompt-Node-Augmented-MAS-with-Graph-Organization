from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List, Tuple

import numpy as np
import torch

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.args import Args
from experiment import process_dataset as gdata
from experiment.model import ARGDesigner
from experiment.train_ARGDesigner import train, validate


DEFAULT_DATA_DIR = "experiment/PromptEdgeData_mmlu_r183"
DEFAULT_OUTPUT_DIR = "experiment/mmlu/output/mmlu_promptedge_pn_graph_policy_r186_short"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r186_promptedge_short_pretrain_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r186_promptedge_short_pretrain_report.md"


def identity_collate(batch):
    return batch


def build_pretrain_args(
    data_dir: str,
    output_dir: str,
    epochs: int,
    batch_size: int,
    lr: float,
    seed: int,
) -> Any:
    args = Args().update_args()
    args.dataset = "mmlu"
    args.dataset_name = "mmlu"
    args.data_dir = data_dir
    args.experiment_path = output_dir
    args.pretrain = True
    args.epochs = epochs
    args.lr = lr
    args.batch_size = batch_size
    args.num_workers = 0
    args.seed = seed
    args.device = "cpu"
    args.model_name = "best_model.pth"
    args.save_model = True
    args.epochs_validate = 1
    return args


def split_graphs(graphs: List[Any], seed: int, train_ratio: float = 0.9) -> Tuple[List[Any], List[Any]]:
    shuffled = list(graphs)
    random.Random(seed).shuffle(shuffled)
    split = max(1, int(len(shuffled) * train_ratio))
    if split >= len(shuffled):
        split = len(shuffled) - 1
    return shuffled[:split], shuffled[split:]


def infer_observed_role_mapping(
    graphs: List[Any],
    fallback_role_to_id: Dict[str, int],
) -> Tuple[Dict[str, int], Dict[int, str]]:
    observed = set()
    for graph in graphs:
        for _, data in graph.nodes(data=True):
            role = data.get("role")
            if role:
                observed.add(str(role))
    ordered = [role for role in sorted(fallback_role_to_id, key=fallback_role_to_id.get) if role in observed]
    for role in sorted(observed):
        if role not in ordered:
            ordered.append(role)
    role_to_id = {role: idx for idx, role in enumerate(ordered)}
    id_to_role = {idx: role for role, idx in role_to_id.items()}
    return role_to_id, id_to_role


def run_short_pretrain(
    data_dir: str,
    output_dir: str,
    summary_json: str,
    report_md: str,
    epochs: int,
    batch_size: int,
    lr: float,
    seed: int,
    run_id: str = "R186",
    role_scope: str = "dataset",
) -> Dict[str, Any]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    args = build_pretrain_args(data_dir, output_dir, epochs, batch_size, lr, seed)
    graph_dataset, _ = gdata.load_graph_dataset(args, pretrain=True)
    if role_scope == "observed":
        args.role_mapping, args.id_to_role = infer_observed_role_mapping(
            graph_dataset.graph_list,
            graph_dataset.role_to_id,
        )
    else:
        args.role_mapping = graph_dataset.role_to_id
        args.id_to_role = graph_dataset.id_to_role
    args.START_TOKEN_ID = len(args.role_mapping)
    args.END_TOKEN_ID = len(args.role_mapping) + 1

    data_statistics = gdata.get_data_statistics(graph_dataset)
    data_statistics["num_node_labels"] = len(args.role_mapping) + 2
    data_statistics["num_edge_labels"] = 1

    train_graphs, val_graphs = split_graphs(graph_dataset.graph_list, seed=seed)
    train_dataset = gdata.GraphListDataset(train_graphs, args)
    val_dataset = gdata.GraphListDataset(val_graphs, args)
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        drop_last=True,
        num_workers=0,
        collate_fn=identity_collate,
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        drop_last=False,
        num_workers=0,
        collate_fn=identity_collate,
    )

    with open(os.path.join(output_dir, "configuration.txt"), "w", encoding="utf-8") as f:
        json.dump(args.__dict__, f, indent=2)

    model = ARGDesigner(args, data_statistics).to(args.device)
    train(args, model, train_loader, val_loader)
    final_val_loss, final_val_role_accuracy = validate(args, model, val_loader)

    best_model_path = os.path.join(output_dir, "best_model.pth")
    summary = {
        "run_id": run_id,
        "title": "MMLU PN-capable short graph-policy pretrain",
        "claim_boundary": (
            "Short no-API graph-policy pretraining only. No answer accuracy claim and "
            "no MMLU transfer claim."
        ),
        "no_api": True,
        "broad_api": False,
        "data_dir": data_dir,
        "output_dir": output_dir,
        "epochs": epochs,
        "batch_size": batch_size,
        "lr": lr,
        "seed": seed,
        "role_scope": role_scope,
        "dataset_graphs": len(graph_dataset),
        "train_graphs": len(train_graphs),
        "val_graphs": len(val_graphs),
        "role_mapping_size": len(args.role_mapping),
        "pn_roles_present": sorted(
            set(args.role_mapping).intersection({"PN_Memory", "PN_Verifier", "PN_Router"})
        ),
        "data_statistics": data_statistics,
        "final_validation_loss": float(final_val_loss),
        "final_validation_role_accuracy": float(final_val_role_accuracy),
        "best_model_path": best_model_path,
        "best_model_exists": os.path.exists(best_model_path),
        "configuration_path": os.path.join(output_dir, "configuration.txt"),
        "configuration_exists": os.path.exists(os.path.join(output_dir, "configuration.txt")),
        "next_action": "R187 should audit generated graph samples before any transfer API smoke.",
    }

    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))

    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {summary['run_id']} MMLU PN-Capable Short Pretrain",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Result",
            "",
            f"- Dataset graphs: `{summary['dataset_graphs']}`",
            f"- Train/val graphs: `{summary['train_graphs']}/{summary['val_graphs']}`",
            f"- Epochs: `{summary['epochs']}`",
            f"- Batch size: `{summary['batch_size']}`",
            f"- Role mapping size: `{summary['role_mapping_size']}`",
            f"- PN roles present: `{summary['pn_roles_present']}`",
            f"- Final validation loss: `{summary['final_validation_loss']:.4f}`",
            f"- Final validation role accuracy: `{summary['final_validation_role_accuracy']:.2f}`",
            f"- Best model exists: `{summary['best_model_exists']}`",
            "",
            "## Boundary",
            "",
            "This is a graph-policy checkpoint only. It has not been evaluated on MMLU answers and cannot support an accuracy claim.",
            "",
            "## Next",
            "",
            summary["next_action"],
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run short PN-capable MMLU graph-policy pretrain.")
    parser.add_argument("--data_dir", default=DEFAULT_DATA_DIR)
    parser.add_argument("--output_dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run_id", default="R186")
    parser.add_argument("--role_scope", choices=["dataset", "observed"], default="dataset")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_short_pretrain(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        summary_json=args.summary_json,
        report_md=args.report_md,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        seed=args.seed,
        run_id=args.run_id,
        role_scope=args.role_scope,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
