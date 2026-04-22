from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

try:
    from backend.torch_artifacts import (
        DISEASE_CLASSES_JSON,
        MODEL_PATH,
        PROCESSED_DATA_PATH,
        SYMPTOM_COLUMNS_JSON,
        DiseaseMLP,
    )
except Exception:  # pragma: no cover
    from torch_artifacts import (
        DISEASE_CLASSES_JSON,
        MODEL_PATH,
        PROCESSED_DATA_PATH,
        SYMPTOM_COLUMNS_JSON,
        DiseaseMLP,
    )


def _train_test_split(
    x: np.ndarray, y: np.ndarray, *, test_size: float = 0.2, seed: int = 42
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(int(seed))
    indices = np.arange(len(x))
    rng.shuffle(indices)
    split = int(round(len(x) * (1.0 - float(test_size))))
    train_idx, test_idx = indices[:split], indices[split:]
    return x[train_idx], x[test_idx], y[train_idx], y[test_idx]


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a PyTorch deep learning model for disease prediction.")
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=2e-3)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--hidden", nargs="*", type=int, default=[256, 128])
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not PROCESSED_DATA_PATH.exists():
        raise SystemExit(f"Missing dataset: {PROCESSED_DATA_PATH}")

    df = pd.read_csv(PROCESSED_DATA_PATH).dropna()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "disease" not in df.columns:
        raise SystemExit("Dataset must contain a 'Disease' column.")

    symptom_columns = [c for c in df.columns if c != "disease"]
    disease_classes = sorted({str(x) for x in df["disease"].astype(str).tolist()})
    class_to_idx = {name: idx for idx, name in enumerate(disease_classes)}

    x = df[symptom_columns].fillna(0).astype(np.float32).to_numpy(copy=True)
    y = df["disease"].astype(str).map(class_to_idx).astype(np.int64).to_numpy(copy=True)

    x_train, x_test, y_train, y_test = _train_test_split(x, y, test_size=0.2, seed=args.seed)
    train_ds = TensorDataset(torch.tensor(x_train), torch.tensor(y_train))
    test_x = torch.tensor(x_test)
    test_y = torch.tensor(y_test)

    train_loader = DataLoader(train_ds, batch_size=int(args.batch_size), shuffle=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(int(args.seed))

    model = DiseaseMLP(
        input_dim=x.shape[1],
        num_classes=len(disease_classes),
        hidden_dims=args.hidden,
        dropout=float(args.dropout),
    ).to(device)

    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(args.lr))

    for epoch in range(1, int(args.epochs) + 1):
        model.train()
        running = 0.0
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch_x)
            loss = loss_fn(logits, batch_y)
            loss.backward()
            optimizer.step()
            running += float(loss.item()) * float(batch_x.shape[0])

        model.eval()
        with torch.no_grad():
            logits = model(test_x.to(device))
            preds = torch.argmax(logits, dim=1).cpu()
            acc = float((preds == test_y).float().mean().item()) if len(test_y) else 0.0
        avg_loss = running / max(1, len(train_ds))
        print(f"epoch={epoch:03d} loss={avg_loss:.4f} test_acc={acc*100:.2f}%")

    SYMPTOM_COLUMNS_JSON.write_text(json.dumps(symptom_columns, indent=2), encoding="utf-8")
    DISEASE_CLASSES_JSON.write_text(json.dumps(disease_classes, indent=2), encoding="utf-8")

    payload = {
        "state_dict": model.to("cpu").state_dict(),
        "hidden_dims": [int(x) for x in args.hidden],
        "dropout": float(args.dropout),
    }
    torch.save(payload, MODEL_PATH)

    print(f"\nSaved: {MODEL_PATH}")
    print(f"Saved: {SYMPTOM_COLUMNS_JSON}")
    print(f"Saved: {DISEASE_CLASSES_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
