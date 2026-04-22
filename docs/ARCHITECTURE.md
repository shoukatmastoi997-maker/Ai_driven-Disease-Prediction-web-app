# Architecture

## Backend (FastAPI)

- `backend/main.py`
  - Loads PyTorch artifacts via `backend/torch_artifacts.py`
  - Validates symptoms against `symptom_columns.json`
  - Stores predictions in `backend/predictions.db`
  - Generates PDF reports via `/api/report/{id}`

- `backend/torch_artifacts.py`
  - Defines the MLP model
  - Loads artifacts for inference
  - Provides:
    - `predict_top_k(...)`
    - `explain_with_grad_times_input(...)` (simple XAI)
    - dataset-frequency feature importance

## Frontend (React)

- `frontend/src/pages/PredictPage.jsx` — patient intake + symptom selection
- `frontend/src/pages/ResultsPage.jsx` — top predictions + PDF download
- `frontend/src/pages/DashboardPage.jsx` — Patient Database (history + report view/print)
- `frontend/src/services/api.js` — API wrapper

