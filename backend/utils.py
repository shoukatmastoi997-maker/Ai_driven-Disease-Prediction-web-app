from typing import Any
import numpy as np
from fastapi import HTTPException

try:
    from backend.config import SYMPTOM_SET, SYMPTOM_INDEX, SYMPTOM_COLUMNS
except ImportError:  # pragma: no cover
    from config import SYMPTOM_SET, SYMPTOM_INDEX, SYMPTOM_COLUMNS


def normalize_symptom(value: str) -> str:
    """Normalize symptom string to lowercase and strip whitespace."""
    return str(value).strip().lower()


def dedupe_keep_order(items: list[str]) -> list[str]:
    """Remove duplicates while preserving order."""
    seen = set()
    output: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output


def validate_symptoms(raw_symptoms: list[str]) -> list[str]:
    """Validate and clean symptoms list."""
    cleaned = [normalize_symptom(s) for s in raw_symptoms if str(s).strip()]
    deduped = dedupe_keep_order(cleaned)
    
    if not deduped:
        raise HTTPException(status_code=422, detail="At least one symptom is required.")
    
    invalid = sorted(set(deduped) - SYMPTOM_SET)
    if invalid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Some symptoms are invalid.",
                "invalid_symptoms": invalid,
            },
        )
    return deduped


def symptoms_to_vector(symptoms: list[str]) -> np.ndarray:
    """Convert symptoms list to binary vector."""
    vector = np.zeros(len(SYMPTOM_COLUMNS), dtype=int)
    for symptom in symptoms:
        idx = SYMPTOM_INDEX[symptom]
        vector[idx] = 1
    return vector


def risk_level(confidence: float) -> str:
    """Determine risk level based on confidence score."""
    if confidence >= 0.70:
        return "High"
    if confidence >= 0.40:
        return "Moderate"
    return "Low"


def risk_guidance(risk_level: str) -> str:
    """Get guidance message based on risk level."""
    mapping = {
        "High": "Seek medical attention promptly. Consider consultation within 24 hours.",
        "Moderate": "Monitor symptoms closely and schedule a medical consultation soon.",
        "Low": "Risk appears lower, but continue monitoring and consult a doctor if symptoms worsen.",
    }
    return mapping.get(risk_level, "Consult a qualified medical professional.")