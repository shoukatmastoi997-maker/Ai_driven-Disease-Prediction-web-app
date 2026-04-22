import numpy as np
from typing import Any, Optional

try:
    from backend.torch_artifacts import (
        explain_with_grad_times_input,
        global_feature_importance as _torch_global_feature_importance,
        load_artifacts,
        predict_top_k,
    )
except Exception:  # pragma: no cover
    from torch_artifacts import (
        explain_with_grad_times_input,
        global_feature_importance as _torch_global_feature_importance,
        load_artifacts,
        predict_top_k,
    )

ARTIFACTS = load_artifacts()


def prediction_top_k(vector: np.ndarray, k: int = 5) -> tuple[str, list[dict[str, Any]], float]:
    """Get top k predictions for symptom vector."""
    prediction, top_predictions, confidence, _ = predict_top_k(ARTIFACTS, vector, k=k)
    return prediction, top_predictions, confidence


def explain_prediction(vector: np.ndarray, predicted_disease: str, top_n: int = 10) -> dict[str, Any]:
    """Explain prediction using gradient * input saliency."""
    try:
        class_index = int(ARTIFACTS.disease_classes.index(predicted_disease))
    except ValueError:
        class_index = 0
    return explain_with_grad_times_input(ARTIFACTS, vector, class_index=class_index, top_n=top_n)


def global_feature_importance(top_n: int = 15) -> list[dict[str, Any]]:
    """Global feature importance from dataset frequency."""
    return _torch_global_feature_importance(ARTIFACTS.symptom_columns, top_n=top_n)
