from __future__ import annotations
import warnings
from datetime import datetime
from typing import Any

import numpy as np
import torch
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

warnings.filterwarnings("ignore", message="You have both PyFPDF & fpdf2 installed.*")
from pydantic import BaseModel, Field

try:
    from backend.database import (
        ensure_db,
        get_analytics_data,
        get_prediction_by_id,
        list_predictions,
        list_predictions_summary,
        save_prediction,
        save_report,
    )
    from backend.pdf_generator import generate_pdf_report
    from backend.torch_artifacts import (
        explain_with_grad_times_input,
        global_feature_importance as torch_global_feature_importance,
        load_artifacts,
        predict_top_k,
    )
except Exception:  # pragma: no cover
    from database import (
        ensure_db,
        get_analytics_data,
        get_prediction_by_id,
        list_predictions,
        list_predictions_summary,
        save_prediction,
        save_report,
    )
    from pdf_generator import generate_pdf_report
    from torch_artifacts import (
        explain_with_grad_times_input,
        global_feature_importance as torch_global_feature_importance,
        load_artifacts,
        predict_top_k,
    )


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ARTIFACTS = load_artifacts(device=DEVICE)
SYMPTOM_COLUMNS = ARTIFACTS.symptom_columns
SYMPTOM_INDEX = {name: idx for idx, name in enumerate(SYMPTOM_COLUMNS)}
SYMPTOM_SET = set(SYMPTOM_COLUMNS)


class PredictionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    fname: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=120)
    gender: str = Field(min_length=1, max_length=30)
    basic_info: str = Field(default="", max_length=500)
    symptoms: list[str] = Field(min_length=1, max_length=131)


class PredictionRecord(BaseModel):
    id: int
    created_at: str
    name: str
    fname: str
    age: int
    gender: str
    symptoms: list[str]
    predicted_disease: str
    risk_level: str
    confidence: float


def _normalize_symptom(value: str) -> str:
    return str(value).strip().lower()


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set()
    output: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output


def _validate_symptoms(raw_symptoms: list[str]) -> list[str]:
    cleaned = [_normalize_symptom(s) for s in raw_symptoms if str(s).strip()]
    deduped = _dedupe_keep_order(cleaned)
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


def _symptoms_to_vector(symptoms: list[str]) -> np.ndarray:
    vector = np.zeros(len(SYMPTOM_COLUMNS), dtype=int)
    for symptom in symptoms:
        idx = SYMPTOM_INDEX[symptom]
        vector[idx] = 1
    return vector


def _risk_level(confidence: float) -> str:
    if confidence >= 0.70:
        return "High"
    if confidence >= 0.40:
        return "Moderate"
    return "Low"


def _risk_guidance(risk_level: str) -> str:
    mapping = {
        "High": "Seek medical attention promptly. Consider consultation within 24 hours.",
        "Moderate": "Monitor symptoms closely and schedule a medical consultation soon.",
        "Low": "Risk appears lower, but continue monitoring and consult a doctor if symptoms worsen.",
    }
    return mapping.get(risk_level, "Consult a qualified medical professional.")


def _explain_prediction(vector: np.ndarray, predicted_disease: str, top_n: int = 10) -> dict[str, Any]:
    try:
        class_index = int(ARTIFACTS.disease_classes.index(predicted_disease))
    except ValueError:
        class_index = 0
    return explain_with_grad_times_input(ARTIFACTS, vector, class_index=class_index, top_n=top_n, device=DEVICE)


def _global_feature_importance(top_n: int = 15) -> list[dict[str, Any]]:
    return torch_global_feature_importance(SYMPTOM_COLUMNS, top_n=top_n)


def _prediction_top_k(vector: np.ndarray, k: int = 5) -> tuple[str, list[dict[str, Any]], float]:
    prediction, top_predictions, confidence, _ = predict_top_k(ARTIFACTS, vector, k=k, device=DEVICE)
    return prediction, top_predictions, confidence


app = FastAPI(title="Disease Prediction API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    ensure_db(
        symptom_columns=SYMPTOM_COLUMNS,
        disease_classes=list(ARTIFACTS.disease_classes),
    )


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "model_loaded": True,
        "total_symptoms": len(SYMPTOM_COLUMNS),
        "total_diseases": int(len(ARTIFACTS.disease_classes)),
    }


@app.get("/api/symptoms")
def list_symptoms() -> dict[str, Any]:
    return {"count": len(SYMPTOM_COLUMNS), "symptoms": SYMPTOM_COLUMNS}


@app.get("/api/feature-importance")
def feature_importance(top_n: int = Query(default=15, ge=1, le=50)) -> dict[str, Any]:
    return {"top_features": _global_feature_importance(top_n=top_n)}


@app.post("/api/predict")
def predict(payload: PredictionRequest) -> dict[str, Any]:
    symptoms = _validate_symptoms(payload.symptoms)
    vector = _symptoms_to_vector(symptoms)

    prediction, top_predictions, confidence, predicted_index = predict_top_k(ARTIFACTS, vector, k=5, device=DEVICE)
    risk_level = _risk_level(confidence)
    explanation = explain_with_grad_times_input(
        ARTIFACTS, vector, class_index=predicted_index, top_n=10, device=DEVICE
    )

    created_at = datetime.now().isoformat(timespec="seconds")
    record_id = save_prediction(
        created_at=created_at,
        name=payload.name.strip(),
        fname=payload.fname.strip(),
        age=payload.age,
        gender=payload.gender.strip(),
        basic_info=payload.basic_info.strip(),
        symptoms=symptoms,
        predicted_disease=prediction,
        risk_level=risk_level,
        confidence=confidence,
        top_predictions=top_predictions,
    )

    return {
        "record_id": record_id,
        "created_at": created_at,
        "patient": {
            "name": payload.name.strip(),
            "fname": payload.fname.strip(),
            "age": payload.age,
            "gender": payload.gender.strip(),
            "basic_info": payload.basic_info.strip(),
        },
        "symptoms": symptoms,
        "prediction": prediction,
        "top_predictions": top_predictions,
        "confidence": confidence,
        "risk_level": risk_level,
        "risk_guidance": _risk_guidance(risk_level),
        "xai": explanation,
        "global_feature_importance": _global_feature_importance(top_n=10),
    }


@app.get("/api/history", response_model=list[PredictionRecord])
def history(
    limit: int = Query(default=50, ge=1, le=500),
    search: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    query = """
            SELECT id, created_at, date, time, name, fname, age, gender, basic_info,
                   symptoms, predicted_disease, risk_level, confidence, top_predictions
            FROM predictions
            """
    clauses = []
    params: list[Any] = []

    if search:
        clauses.append("(LOWER(name) LIKE ? OR LOWER(predicted_disease) LIKE ?)")
        search_term = f"%{search.strip().lower()}%"
        params.extend([search_term, search_term])

    if risk_level:
        clauses.append("LOWER(risk_level) = LOWER(?)")
        params.append(risk_level.strip())

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(query, params).fetchall()
    parsed = [_parse_history_row(row) for row in rows]
    return [
        {
            "id": item["id"],
            "created_at": item["created_at"],
            "name": item["name"],
            "fname": item["fname"],
            "age": item["age"],
            "gender": item["gender"],
            "symptoms": item["symptoms"],
            "predicted_disease": item["predicted_disease"],
            "risk_level": item["risk_level"],
            "confidence": item["confidence"],
        }
        for item in parsed
    ]


@app.get("/api/history-full")
def history_full(
    limit: int = Query(default=100, ge=1, le=1000),
    search: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    return list_predictions(limit=limit, search=search, risk_level=risk_level)


@app.get("/api/analytics")
def analytics() -> dict[str, Any]:
    return get_analytics_data(symptom_columns=SYMPTOM_COLUMNS)


@app.get("/api/report/{record_id}")
def generate_report(record_id: int):
    record = get_prediction_by_id(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Prediction record not found.")
    report_path = f"prediction_report_{record_id}.pdf"
    save_report(prediction_id=record_id, report_path=report_path)
    return generate_pdf_report(record)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
