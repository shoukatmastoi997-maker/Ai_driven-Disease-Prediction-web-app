from __future__ import annotations
from pathlib import Path
import warnings
from typing import Any

warnings.filterwarnings("ignore", message="You have both PyFPDF & fpdf2 installed.*")

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DATA_PATH = BASE_DIR / "processed_disease_dataset.csv"
DB_PATH = BASE_DIR / "predictions.db"


def load_artifacts() -> tuple[Any, list[str]]:
    """Load torch model and symptom columns."""
    try:
        from backend.torch_artifacts import load_artifacts as _load
    except Exception:  # pragma: no cover
        from torch_artifacts import load_artifacts as _load

    artifacts = _load()
    return artifacts.model, artifacts.symptom_columns


# Load artifacts at module level
MODEL, SYMPTOM_COLUMNS = load_artifacts()
SYMPTOM_INDEX = {name: idx for idx, name in enumerate(SYMPTOM_COLUMNS)}
SYMPTOM_SET = set(SYMPTOM_COLUMNS)
