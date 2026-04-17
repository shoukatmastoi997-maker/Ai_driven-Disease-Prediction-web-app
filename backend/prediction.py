import numpy as np
import pandas as pd
from typing import Any, Optional

from backend.config import MODEL, SYMPTOM_COLUMNS, EXPLAINER, shap
from backend.utils import symptoms_to_vector


def prediction_top_k(vector: np.ndarray, k: int = 5) -> tuple[str, list[dict[str, Any]], float]:
    """Get top k predictions for symptom vector."""
    x_input = pd.DataFrame([vector], columns=SYMPTOM_COLUMNS)
    prediction = str(MODEL.predict(x_input)[0])
    
    if hasattr(MODEL, "predict_proba"):
        probabilities = np.array(MODEL.predict_proba(x_input)[0], dtype=float)
        top_indices = np.argsort(probabilities)[-k:][::-1]
        top_predictions = [
            {
                "disease": str(MODEL.classes_[idx]),
                "probability": float(probabilities[idx]),
                "percent": round(float(probabilities[idx]) * 100, 2),
            }
            for idx in top_indices
        ]
        confidence = float(top_predictions[0]["probability"])
        return prediction, top_predictions, confidence
    
    top_predictions = [{"disease": prediction, "probability": 1.0, "percent": 100.0}]
    return prediction, top_predictions, 1.0


def extract_shap_values(shap_values: Any, class_idx: int) -> np.ndarray:
    """Extract SHAP values for a specific class."""
    if isinstance(shap_values, list):
        return np.array(shap_values[class_idx][0], dtype=float)
    
    arr = np.array(shap_values)
    if arr.ndim == 3:
        return np.array(arr[0, :, class_idx], dtype=float)
    if arr.ndim == 2:
        return np.array(arr[0], dtype=float)
    
    return np.zeros(len(SYMPTOM_COLUMNS), dtype=float)


def explain_prediction(vector: np.ndarray, predicted_disease: str, top_n: int = 10) -> dict[str, Any]:
    """Explain prediction using SHAP or fallback method."""
    selected_symptom_indices = np.where(vector == 1)[0].tolist()
    
    if not selected_symptom_indices:
        return {"method": "none", "top_contributors": []}
    
    try:
        global EXPLAINER
        if shap is None:
            raise RuntimeError("SHAP is not installed.")
        
        if EXPLAINER is None:
            EXPLAINER = shap.TreeExplainer(MODEL)
        
        class_idx = int(np.where(MODEL.classes_ == predicted_disease)[0][0])
        shap_values = EXPLAINER.shap_values(np.array([vector]))
        class_shap = extract_shap_values(shap_values, class_idx)
        
        pairs = [
            {
                "symptom": SYMPTOM_COLUMNS[idx],
                "contribution": float(class_shap[idx]),
                "abs_contribution": float(abs(class_shap[idx])),
            }
            for idx in selected_symptom_indices
        ]
        pairs.sort(key=lambda item: item["abs_contribution"], reverse=True)
        return {"method": "shap", "top_contributors": pairs[:top_n]}
    
    except Exception:
        if hasattr(MODEL, "feature_importances_"):
            importances = np.array(MODEL.feature_importances_)
        else:
            importances = np.ones(len(SYMPTOM_COLUMNS), dtype=float)
        
        pairs = [
            {
                "symptom": SYMPTOM_COLUMNS[idx],
                "contribution": float(importances[idx]),
                "abs_contribution": float(abs(importances[idx])),
            }
            for idx in selected_symptom_indices
        ]
        pairs.sort(key=lambda item: item["abs_contribution"], reverse=True)
        return {"method": "feature_importance_fallback", "top_contributors": pairs[:top_n]}


def global_feature_importance(top_n: int = 15) -> list[dict[str, Any]]:
    """Get global feature importance from model."""
    if hasattr(MODEL, "feature_importances_"):
        values = np.array(MODEL.feature_importances_, dtype=float)
        top_idx = np.argsort(values)[-top_n:][::-1]
        return [
            {"symptom": SYMPTOM_COLUMNS[i], "importance": float(values[i])}
            for i in top_idx
        ]
    return []