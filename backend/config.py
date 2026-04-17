from __future__ import annotations
from pathlib import Path
import warnings
import joblib
from typing import Any

warnings.filterwarnings("ignore", message="You have both PyFPDF & fpdf2 installed.*")

try:
    import shap  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback
    shap = None

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "disease_prediction_model.pkl"
SYMPTOM_COLUMNS_PATH = BASE_DIR / "symptom_columns.pkl"
PROCESSED_DATA_PATH = BASE_DIR / "processed_disease_dataset.csv"
DB_PATH = BASE_DIR / "predictions.db"


def load_artifacts() -> tuple[Any, list[str]]:
    """Load model and symptom columns from pickle files."""
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Missing model file: {MODEL_PATH}")
    if not SYMPTOM_COLUMNS_PATH.exists():
        raise RuntimeError(f"Missing symptom file: {SYMPTOM_COLUMNS_PATH}")
    
    model = joblib.load(MODEL_PATH)
    symptom_columns = joblib.load(SYMPTOM_COLUMNS_PATH)
    
    if not isinstance(symptom_columns, list):
        raise RuntimeError("symptom_columns.pkl must contain a list[str]")
    
    return model, [str(x).strip().lower() for x in symptom_columns]


# Load artifacts at module level
MODEL, SYMPTOM_COLUMNS = load_artifacts()
SYMPTOM_INDEX = {name: idx for idx, name in enumerate(SYMPTOM_COLUMNS)}
SYMPTOM_SET = set(SYMPTOM_COLUMNS)

# Global explainer for SHAP
EXPLAINER = None