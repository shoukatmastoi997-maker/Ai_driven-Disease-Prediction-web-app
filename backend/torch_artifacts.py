from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import torch
from torch import nn


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "disease_prediction_model.pt"
SYMPTOM_COLUMNS_JSON = BASE_DIR / "symptom_columns.json"
DISEASE_CLASSES_JSON = BASE_DIR / "disease_classes.json"
PROCESSED_DATA_PATH = BASE_DIR / "processed_disease_dataset.csv"


def _read_json_list(path: Path) -> list[str]:
    if not path.exists():
        raise RuntimeError(f"Missing required file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
        raise RuntimeError(f"{path.name} must be a JSON list of strings.")
    return [x.strip().lower() for x in data if str(x).strip()]


class DiseaseMLP(nn.Module):
    def __init__(
        self,
        *,
        input_dim: int,
        num_classes: int,
        hidden_dims: Iterable[int] = (256, 128),
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        dims = [int(input_dim), *[int(x) for x in hidden_dims], int(num_classes)]
        layers: list[nn.Module] = []
        for in_dim, out_dim in zip(dims[:-2], dims[1:-1], strict=False):
            layers.append(nn.Linear(in_dim, out_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(p=float(dropout)))
        layers.append(nn.Linear(dims[-2], dims[-1]))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


@dataclass(frozen=True)
class TorchArtifacts:
    model: DiseaseMLP
    symptom_columns: list[str]
    disease_classes: list[str]


def load_artifacts(device: torch.device | None = None) -> TorchArtifacts:
    device = device or torch.device("cpu")
    _ensure_artifacts_exist()
    symptom_columns = _read_json_list(SYMPTOM_COLUMNS_JSON)
    disease_classes = _read_json_list(DISEASE_CLASSES_JSON)

    payload: dict[str, Any] = torch.load(MODEL_PATH, map_location="cpu")
    state_dict = payload.get("state_dict")
    hidden_dims = payload.get("hidden_dims", [256, 128])
    dropout = float(payload.get("dropout", 0.2))

    model = DiseaseMLP(
        input_dim=len(symptom_columns),
        num_classes=len(disease_classes),
        hidden_dims=hidden_dims,
        dropout=dropout,
    )
    if not isinstance(state_dict, dict):
        raise RuntimeError(f"{MODEL_PATH.name} is missing a valid state_dict.")
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    return TorchArtifacts(model=model, symptom_columns=symptom_columns, disease_classes=disease_classes)


def _ensure_artifacts_exist() -> None:
    if SYMPTOM_COLUMNS_JSON.exists() and DISEASE_CLASSES_JSON.exists() and MODEL_PATH.exists():
        return
    _train_and_save_default()


def _train_and_save_default() -> None:
    if not PROCESSED_DATA_PATH.exists():
        raise RuntimeError(
            f"Missing dataset: {PROCESSED_DATA_PATH}. Cannot auto-train model artifacts. "
            "Provide artifacts (model + json schema) or restore the dataset."
        )

    df = pd.read_csv(PROCESSED_DATA_PATH).dropna()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "disease" not in df.columns:
        raise RuntimeError("Dataset must contain a 'Disease' column.")

    symptom_columns = [c for c in df.columns if c != "disease"]
    disease_classes = sorted({str(x) for x in df["disease"].astype(str).tolist()})
    class_to_idx = {name: idx for idx, name in enumerate(disease_classes)}

    x = df[symptom_columns].fillna(0).astype(np.float32).to_numpy(copy=True)
    y = df["disease"].astype(str).map(class_to_idx).astype(np.int64).to_numpy(copy=True)

    rng = np.random.default_rng(42)
    indices = np.arange(len(x))
    rng.shuffle(indices)
    split = int(round(len(x) * 0.8))
    train_idx, test_idx = indices[:split], indices[split:]
    x_train, y_train = x[train_idx], y[train_idx]

    train_ds = torch.utils.data.TensorDataset(torch.tensor(x_train), torch.tensor(y_train))
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=128, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(42)

    model = DiseaseMLP(input_dim=x.shape[1], num_classes=len(disease_classes)).to(device)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3)

    # Short auto-train to keep first-run startup reasonable.
    epochs = 10
    for _ in range(epochs):
        model.train()
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch_x)
            loss = loss_fn(logits, batch_y)
            loss.backward()
            optimizer.step()

    SYMPTOM_COLUMNS_JSON.write_text(json.dumps(symptom_columns, indent=2), encoding="utf-8")
    DISEASE_CLASSES_JSON.write_text(json.dumps(disease_classes, indent=2), encoding="utf-8")
    torch.save(
        {"state_dict": model.to("cpu").state_dict(), "hidden_dims": [256, 128], "dropout": 0.2},
        MODEL_PATH,
    )


def predict_top_k(
    artifacts: TorchArtifacts,
    vector: np.ndarray,
    *,
    k: int = 5,
    device: torch.device | None = None,
) -> tuple[str, list[dict[str, Any]], float, int]:
    device = device or torch.device("cpu")
    x = torch.tensor(vector.astype(np.float32), device=device).unsqueeze(0)
    with torch.no_grad():
        logits = artifacts.model(x)
        probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy().astype(float)

    top_indices = np.argsort(probs)[-max(1, int(k)) :][::-1]
    top_predictions = [
        {
            "disease": str(artifacts.disease_classes[int(idx)]),
            "probability": float(probs[int(idx)]),
            "percent": round(float(probs[int(idx)]) * 100, 2),
        }
        for idx in top_indices
    ]
    predicted_index = int(top_indices[0])
    prediction = str(artifacts.disease_classes[predicted_index])
    confidence = float(top_predictions[0]["probability"])
    return prediction, top_predictions, confidence, predicted_index


def explain_with_grad_times_input(
    artifacts: TorchArtifacts,
    vector: np.ndarray,
    *,
    class_index: int,
    top_n: int = 10,
    device: torch.device | None = None,
) -> dict[str, Any]:
    selected_indices = np.where(vector == 1)[0].tolist()
    if not selected_indices:
        return {"method": "none", "top_contributors": []}

    device = device or torch.device("cpu")
    x = torch.tensor(vector.astype(np.float32), device=device).unsqueeze(0)
    x.requires_grad_(True)

    logits = artifacts.model(x)
    target = logits[0, int(class_index)]
    artifacts.model.zero_grad(set_to_none=True)
    if x.grad is not None:
        x.grad.zero_()
    target.backward()

    grad = x.grad.detach().squeeze(0).cpu().numpy().astype(float)
    contrib = grad * vector.astype(float)
    pairs = [
        {
            "symptom": artifacts.symptom_columns[int(idx)],
            "contribution": float(contrib[int(idx)]),
            "abs_contribution": float(abs(contrib[int(idx)])),
        }
        for idx in selected_indices
    ]
    pairs.sort(key=lambda item: item["abs_contribution"], reverse=True)
    return {"method": "grad_x_input", "top_contributors": pairs[: int(top_n)]}


def global_feature_importance(symptom_columns: list[str], *, top_n: int = 15) -> list[dict[str, Any]]:
    if not PROCESSED_DATA_PATH.exists():
        return []
    df = pd.read_csv(PROCESSED_DATA_PATH)
    available = [c for c in symptom_columns if c in df.columns]
    if not available:
        return []
    counts = df[available].fillna(0).astype(int).sum().sort_values(ascending=False).head(int(top_n))
    total = float(df.shape[0]) if df.shape[0] else 1.0
    return [{"symptom": str(symptom), "importance": float(count) / total} for symptom, count in counts.items()]
