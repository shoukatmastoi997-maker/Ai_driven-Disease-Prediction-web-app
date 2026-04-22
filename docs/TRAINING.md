# Training (PyTorch)

The model is a simple MLP (feed-forward network) trained on:

- `backend/processed_disease_dataset.csv`

Artifacts produced (and required for inference):

- `backend/disease_prediction_model.pt` (PyTorch weights)
- `backend/symptom_columns.json` (ordered input feature list)
- `backend/disease_classes.json` (ordered class labels)

## Train Command

From repo root:

```powershell
backend\.venv\Scripts\python backend\trainmodel.py --epochs 25
```

## Useful Options

```powershell
backend\.venv\Scripts\python backend\trainmodel.py `
  --epochs 50 `
  --batch-size 256 `
  --lr 0.002 `
  --dropout 0.2 `
  --hidden 256 128
```

Notes:

- More epochs usually improves accuracy.
- If you change dataset columns, re-train so `symptom_columns.json` matches.

