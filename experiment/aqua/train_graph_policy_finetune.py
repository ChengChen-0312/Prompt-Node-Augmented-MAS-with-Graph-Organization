import argparse
import json
import os
import sys
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.aqua_adapter import AquaGraphDataset  # noqa: E402
from experiment.model import ARGDesigner  # noqa: E402
from experiment.process_dataset import GraphListDataset, get_data_statistics  # noqa: E402
from experiment.train_ARGDesigner import train  # noqa: E402


PN_ROLES = {"PN_Memory", "PN_Verifier", "PN_Router"}
DEFAULT_OUTPUT_DIR = "experiment/aqua/output/aqua_pn_graph_policy_r054"


def load_json(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _role_mapping_from_config(model_dir: str) -> Dict[str, int]:
    config_path = os.path.join(model_dir, "configuration.txt")
    if not os.path.exists(config_path):
        return {}
    return load_json(config_path).get("role_mapping", {})


def _has_promptnode_roles(model_dir: str) -> bool:
    return PN_ROLES.issubset(set(_role_mapping_from_config(model_dir)))


def find_latest_promptnode_base_model(base_dir: str = "experiment/aqua/output") -> str:
    candidates: List[str] = []
    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"Base output directory not found: {base_dir}")
    for name in sorted(os.listdir(base_dir)):
        path = os.path.join(base_dir, name)
        if not os.path.isdir(path):
            continue
        if not os.path.exists(os.path.join(path, "best_model.pth")):
            continue
        if not os.path.exists(os.path.join(path, "configuration.txt")):
            continue
        if _has_promptnode_roles(path):
            candidates.append(path)
    if not candidates:
        raise FileNotFoundError(f"No PromptNode-compatible base model found in {base_dir}")
    return candidates[-1]


def validate_checkpoint_role_compatibility(base_model_dir: str) -> Dict[str, int]:
    role_mapping = _role_mapping_from_config(base_model_dir)
    if not role_mapping:
        raise ValueError(f"No role_mapping found in {base_model_dir}/configuration.txt")
    missing = sorted(PN_ROLES - set(role_mapping))
    if missing:
        raise ValueError(
            "Base checkpoint is missing PromptNode roles "
            f"{missing}; use a 7-role PromptNode-compatible base model."
        )
    return role_mapping


def prepare_finetune_args(
    base_model_dir: str,
    finetune_data_dir: str,
    output_dir: str,
    epochs: int,
    batch_size: int,
    lr: float,
    device: str,
    max_train_graphs: int = 0,
) -> SimpleNamespace:
    validate_checkpoint_role_compatibility(base_model_dir)
    config = load_json(os.path.join(base_model_dir, "configuration.txt"))
    config["dataset"] = "aqua"
    config["dataset_name"] = "aqua"
    config["data_dir"] = "experiment/ColdStartData_Aqua"
    config["data_dir_ef"] = finetune_data_dir
    config["experiment_path"] = output_dir
    config["pretrain"] = False
    config["model_name"] = "ef_best_model.pth"
    config["epochs"] = epochs
    config["epochs_validate"] = 1
    config["batch_size"] = batch_size
    config["lr"] = lr
    config["device"] = device
    config["save_model"] = True
    config["max_train_graphs"] = max_train_graphs
    config["base_model_dir"] = base_model_dir
    config["is_dag"] = True
    config["max_head_and_tail"] = None
    if "max_prev_node" not in config or config["max_prev_node"] is None:
        config["max_prev_node"] = 8
    return SimpleNamespace(**config)


def build_finetune_components(args: SimpleNamespace) -> Dict[str, Any]:
    sample_size = int(getattr(args, "max_train_graphs", 0) or 0)
    efficient_dataset = AquaGraphDataset(
        data_dir=args.data_dir,
        data_dir_ef=args.data_dir_ef,
        sample_size=sample_size,
        pretrain=False,
    )
    if not efficient_dataset.graph_list:
        raise ValueError(f"No graph-policy finetune .pt files found in {args.data_dir_ef}")

    args.role_mapping = efficient_dataset.role_to_id
    args.id_to_role = efficient_dataset.id_to_role
    args.START_TOKEN_ID = len(args.role_mapping)
    args.END_TOKEN_ID = len(args.role_mapping) + 1
    data_statistics = get_data_statistics(efficient_dataset.graph_list)
    data_statistics["num_node_labels"] = len(args.role_mapping) + 2
    data_statistics["num_edge_labels"] = 1
    dataset_finetune = GraphListDataset(efficient_dataset.graph_list, args)
    dataloader = torch.utils.data.DataLoader(
        dataset_finetune,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=lambda x: x,
    )
    return {
        "args": args,
        "dataset": dataset_finetune,
        "dataloader": dataloader,
        "stats": data_statistics,
    }


def build_model(args: SimpleNamespace, stats: Dict[str, Any]) -> ARGDesigner:
    model = ARGDesigner(args, stats).to(args.device)
    checkpoint_path = os.path.join(args.base_model_dir, "best_model.pth")
    checkpoint = torch.load(checkpoint_path, map_location=args.device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    return model


def run_forward_smoke(model: ARGDesigner, batch: List[Any], args: SimpleNamespace) -> Dict[str, Any]:
    task_embeddings = []
    for graph in batch:
        embedding = graph.graph.get("task_embedding")
        if embedding is None:
            raise ValueError("Graph missing task_embedding")
        if isinstance(embedding, torch.Tensor):
            task_embeddings.append(embedding.to(args.device).float())
        else:
            task_embeddings.append(torch.tensor(embedding, device=args.device).float())
    stacked = torch.stack(task_embeddings)
    log_probs, role_accuracy = model(batch, stacked)
    loss = -log_probs.mean()
    return {
        "batch_size": len(batch),
        "log_probs_shape": list(log_probs.shape),
        "finite_loss": bool(torch.isfinite(loss).item()),
        "loss": float(loss.item()),
        "role_accuracy": float(role_accuracy),
    }


def run_graph_policy_finetune(args: SimpleNamespace, smoke_only: bool = False) -> Dict[str, Any]:
    os.makedirs(args.experiment_path, exist_ok=True)
    components = build_finetune_components(args)
    model = build_model(args, components["stats"])
    first_batch = next(iter(components["dataloader"]))
    smoke = run_forward_smoke(model, first_batch, args)
    if not smoke["finite_loss"]:
        raise RuntimeError("Forward smoke produced non-finite loss")

    if not smoke_only:
        train(args, model, components["dataloader"])

    config_payload = dict(vars(args))
    config_payload["device"] = str(config_payload.get("device"))
    write_json(os.path.join(args.experiment_path, "configuration.txt"), config_payload)
    summary = {
        "base_model_dir": args.base_model_dir,
        "finetune_data_dir": args.data_dir_ef,
        "output_dir": args.experiment_path,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "max_train_graphs": args.max_train_graphs,
        "dataset_size": len(components["dataset"]),
        "data_statistics": components["stats"],
        "role_mapping_size": len(args.role_mapping),
        "promptnode_roles_present": sorted(PN_ROLES.intersection(args.role_mapping)),
        "forward_smoke": smoke,
        "smoke_only": smoke_only,
        "model_file": os.path.join(args.experiment_path, args.model_name),
        "claim_boundary": (
            "Graph-generator finetune infrastructure only. This run trains or smoke-checks ARGDesigner's "
            "graph generator on PromptNode graph-policy .pt files and does not evaluate AQuA answer accuracy."
        ),
    }
    write_json(os.path.join(args.experiment_path, "r054_graph_policy_finetune_summary.json"), summary)
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    smoke = summary["forward_smoke"]
    return "\n".join(
        [
            "# R054 PromptNode Graph-Policy Finetune",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Base model: `{summary['base_model_dir']}`",
            f"- Finetune data: `{summary['finetune_data_dir']}`",
            f"- Output dir: `{summary['output_dir']}`",
            f"- Dataset size: `{summary['dataset_size']}`",
            f"- Epochs: `{summary['epochs']}`",
            f"- Batch size: `{summary['batch_size']}`",
            f"- Max train graphs: `{summary['max_train_graphs']}`",
            f"- PromptNode roles present: `{', '.join(summary['promptnode_roles_present'])}`",
            f"- Forward finite loss: `{smoke['finite_loss']}`",
            f"- Forward loss: `{smoke['loss']:.4f}`",
            f"- Smoke only: `{summary['smoke_only']}`",
            "",
            "## Interpretation",
            "",
            "R054 is the first direct training-path step after R053: the PromptNode graph-policy `.pt` files are loaded "
            "through the normal AQuA graph adapter, initialized from a PromptNode-compatible ARGDesigner checkpoint, "
            "and passed through the existing graph-generator loss. This is not an answer-accuracy result.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune ARGDesigner on R053 PromptNode graph-policy .pt files.")
    parser.add_argument("--base-model-dir")
    parser.add_argument("--base-output-dir", default="experiment/aqua/output")
    parser.add_argument("--finetune-data-dir", default="experiment/FinetuneData_AQuA_PN_GraphPolicy_R053")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--max-train-graphs", type=int, default=0)
    parser.add_argument("--smoke-only", action="store_true")
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_graph_policy_finetune_r054.md",
    )
    return parser.parse_args()


def main() -> None:
    cli = parse_args()
    base_model_dir = cli.base_model_dir or find_latest_promptnode_base_model(cli.base_output_dir)
    args = prepare_finetune_args(
        base_model_dir=base_model_dir,
        finetune_data_dir=cli.finetune_data_dir,
        output_dir=cli.output_dir,
        epochs=cli.epochs,
        batch_size=cli.batch_size,
        lr=cli.lr,
        device=cli.device,
        max_train_graphs=cli.max_train_graphs,
    )
    summary = run_graph_policy_finetune(args, smoke_only=cli.smoke_only)
    write_text(cli.report_md, render_report(summary))
    print(
        "R054 graph-policy finetune: "
        f"dataset={summary['dataset_size']} epochs={summary['epochs']} "
        f"smoke_only={summary['smoke_only']} finite_loss={summary['forward_smoke']['finite_loss']} "
        f"output={summary['output_dir']}"
    )


if __name__ == "__main__":
    main()
