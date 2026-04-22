# Disease Prediction (PyTorch + FastAPI + React)

This project predicts a likely disease from a selected set of symptoms, stores each prediction in SQLite, and generates a printable PDF report for each patient record.

## Project Structure

- `backend/` — FastAPI API + PyTorch model + SQLite storage + PDF report generator
- `frontend/` — Vite + React UI (Predict, Results, Database)

## Features

- PyTorch deep learning model (MLP) trained on `backend/processed_disease_dataset.csv`
- Predict endpoint stores each prediction in `backend/predictions.db`
- Database page lists saved records (no analytics) and lets you open/print each PDF report
- Results page shows top predictions + simple XAI (gradient × input) for selected symptoms

## Requirements

- Windows 10/11 (works on Linux/macOS too)
- Python 3.10+ (repo includes a `backend/.venv/` folder, but you can recreate it)
- Node.js 18+ for the frontend

## Backend Setup (FastAPI)

From the repo root:

1) Create / activate a venv (recommended):

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python -m pip install --upgrade pip
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

2) Train the PyTorch model (generates the required artifacts in `backend/`):

```powershell
backend\.venv\Scripts\python backend\trainmodel.py --epochs 25
```

This creates:

- `backend/disease_prediction_model.pt`
- `backend/symptom_columns.json`
- `backend/disease_classes.json`

3) Start the API:

```powershell
backend\.venv\Scripts\python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

- `GET http://localhost:8000/health`

## Frontend Setup (React)

From the repo root:

1) Install and run:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

If PowerShell blocks `npm`, always use `npm.cmd` (Windows execution policy).

2) Configure API base URL (optional):

- `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## How to Use

1) Open the frontend in the browser (shown by Vite, usually `http://localhost:5173`).
2) Go to **Predict**:
   - Fill patient info
   - Select symptoms
   - Submit to get a prediction
3) Go to **Results**:
   - View top predictions and download the PDF
4) Go to **Database**:
   - View stored patient records from SQLite
   - Click any row or “View/Print” to open the PDF report and print it

## Documentation

- `docs/API.md` — endpoints and payloads
- `docs/TRAINING.md` — model training details and knobs
- `docs/ARCHITECTURE.md` — how backend/frontend fit together

