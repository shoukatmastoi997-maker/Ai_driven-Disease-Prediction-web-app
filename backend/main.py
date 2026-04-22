from __future__ import annotations
import io
import json
import sqlite3
import warnings
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

warnings.filterwarnings("ignore", message="You have both PyFPDF & fpdf2 installed.*")
from fpdf import FPDF
from pydantic import BaseModel, Field

try:
    from backend.torch_artifacts import (
        explain_with_grad_times_input,
        global_feature_importance as torch_global_feature_importance,
        load_artifacts,
        predict_top_k,
    )
except Exception:  # pragma: no cover
    from torch_artifacts import (
        explain_with_grad_times_input,
        global_feature_importance as torch_global_feature_importance,
        load_artifacts,
        predict_top_k,
    )


BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DATA_PATH = BASE_DIR / "processed_disease_dataset.csv"
DB_PATH = BASE_DIR / "predictions.db"


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ARTIFACTS = load_artifacts(device=DEVICE)
SYMPTOM_COLUMNS = ARTIFACTS.symptom_columns
SYMPTOM_INDEX = {name: idx for idx, name in enumerate(SYMPTOM_COLUMNS)}
SYMPTOM_SET = set(SYMPTOM_COLUMNS)
PROCESSED_DF = pd.read_csv(PROCESSED_DATA_PATH) if PROCESSED_DATA_PATH.exists() else pd.DataFrame()


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


def _ensure_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                name TEXT NOT NULL,
                fname TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                basic_info TEXT,
                symptoms TEXT NOT NULL,
                predicted_disease TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                confidence REAL NOT NULL,
                top_predictions TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _save_prediction(
    *,
    created_at: str,
    name: str,
    fname: str,
    age: int,
    gender: str,
    basic_info: str,
    symptoms: list[str],
    predicted_disease: str,
    risk_level: str,
    confidence: float,
    top_predictions: list[dict[str, Any]],
) -> int:
    dt = datetime.fromisoformat(created_at)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO predictions (
                created_at, date, time, name, fname, age, gender, basic_info,
                symptoms, predicted_disease, risk_level, confidence, top_predictions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                dt.date().isoformat(),
                dt.time().strftime("%H:%M:%S"),
                name,
                fname,
                age,
                gender,
                basic_info,
                json.dumps(symptoms),
                predicted_disease,
                risk_level,
                confidence,
                json.dumps(top_predictions),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


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


def _parse_history_row(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "id": row[0],
        "created_at": row[1],
        "date": row[2],
        "time": row[3],
        "name": row[4],
        "fname": row[5],
        "age": row[6],
        "gender": row[7],
        "basic_info": row[8],
        "symptoms": json.loads(row[9]),
        "predicted_disease": row[10],
        "risk_level": row[11],
        "confidence": row[12],
        "top_predictions": json.loads(row[13]),
    }


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
    _ensure_db()


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
    record_id = _save_prediction(
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
def history(limit: int = Query(default=50, ge=1, le=500)) -> list[dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, date, time, name, fname, age, gender, basic_info,
                   symptoms, predicted_disease, risk_level, confidence, top_predictions
            FROM predictions
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
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
def history_full(limit: int = Query(default=100, ge=1, le=1000)) -> list[dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, date, time, name, fname, age, gender, basic_info,
                   symptoms, predicted_disease, risk_level, confidence, top_predictions
            FROM predictions
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_parse_history_row(row) for row in rows]


@app.get("/api/analytics")
def analytics() -> dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        disease_rows = conn.execute(
            "SELECT predicted_disease, COUNT(*) FROM predictions GROUP BY predicted_disease ORDER BY COUNT(*) DESC"
        ).fetchall()
        risk_rows = conn.execute(
            "SELECT risk_level, COUNT(*) FROM predictions GROUP BY risk_level ORDER BY COUNT(*) DESC"
        ).fetchall()
        progression_rows = conn.execute(
            """
            SELECT date, risk_level, COUNT(*) as c
            FROM predictions
            GROUP BY date, risk_level
            ORDER BY date ASC
            """
        ).fetchall()
        symptom_rows = conn.execute("SELECT symptoms FROM predictions").fetchall()
        total_predictions = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]

    if disease_rows:
        disease_frequency = [{"disease": row[0], "count": int(row[1])} for row in disease_rows]
    elif not PROCESSED_DF.empty and "Disease" in PROCESSED_DF.columns:
        counts = PROCESSED_DF["Disease"].value_counts()
        disease_frequency = [{"disease": str(k), "count": int(v)} for k, v in counts.items()]
    else:
        disease_frequency = []

    if not PROCESSED_DF.empty:
        available_symptom_cols = [c for c in SYMPTOM_COLUMNS if c in PROCESSED_DF.columns]
        if available_symptom_cols:
            sums = PROCESSED_DF[available_symptom_cols].sum().sort_values(ascending=False).head(20)
            symptom_occurrence = [{"symptom": str(k), "count": int(v)} for k, v in sums.items()]
        else:
            symptom_occurrence = []
    else:
        symptom_counter: Counter[str] = Counter()
        for row in symptom_rows:
            for symptom in json.loads(row[0]):
                symptom_counter[symptom] += 1
        symptom_occurrence = [
            {"symptom": symptom, "count": count}
            for symptom, count in symptom_counter.most_common(20)
        ]

    risk_distribution = [{"risk_level": row[0], "count": int(row[1])} for row in risk_rows]

    progression_map: dict[str, dict[str, int]] = {}
    for date_str, risk, count in progression_rows:
        if date_str not in progression_map:
            progression_map[date_str] = {"High": 0, "Moderate": 0, "Low": 0}
        progression_map[date_str][str(risk)] = int(count)

    severity_progression = [
        {
            "date": date_key,
            "high": values["High"],
            "moderate": values["Moderate"],
            "low": values["Low"],
        }
        for date_key, values in progression_map.items()
    ]

    top_disease = disease_frequency[0] if disease_frequency else None
    top_disease_trend: list[dict[str, Any]] = []
    if top_disease and disease_rows:
        with sqlite3.connect(DB_PATH) as conn:
            trend_rows = conn.execute(
                """
                SELECT date, COUNT(*) as c
                FROM predictions
                WHERE predicted_disease = ?
                GROUP BY date
                ORDER BY date ASC
                """,
                (top_disease["disease"],),
            ).fetchall()
        top_disease_trend = [{"date": row[0], "count": int(row[1])} for row in trend_rows]

    return {
        "disease_frequency": disease_frequency,
        "symptom_occurrence": symptom_occurrence,
        "risk_distribution": risk_distribution,
        "severity_progression": severity_progression,
        "total_predictions": int(total_predictions),
        "top_disease": top_disease,
        "top_disease_trend": top_disease_trend,
    }


@app.get("/api/report/{record_id}")
def generate_report(record_id: int) -> StreamingResponse:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT id, created_at, date, time, name, fname, age, gender, basic_info,
                   symptoms, predicted_disease, risk_level, confidence, top_predictions
            FROM predictions
            WHERE id = ?
            """,
            (record_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Prediction record not found.")

    record = _parse_history_row(row)
    top_predictions = record["top_predictions"]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Disease Prediction Report", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Record ID: {record['id']}", ln=True)
    pdf.cell(0, 8, f"Generated at: {record['created_at']}", ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Patient Details", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Name: {record['name']}", ln=True)
    pdf.cell(0, 8, f"Father Name: {record['fname']}", ln=True)
    pdf.cell(0, 8, f"Age: {record['age']}", ln=True)
    pdf.cell(0, 8, f"Gender: {record['gender']}", ln=True)
    if record["basic_info"]:
        pdf.multi_cell(0, 8, f"Basic Info: {record['basic_info']}")
    pdf.ln(2)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Prediction Summary", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Predicted Disease: {record['predicted_disease']}", ln=True)
    pdf.cell(0, 8, f"Risk Level: {record['risk_level']}", ln=True)
    pdf.cell(0, 8, f"Confidence: {record['confidence'] * 100:.2f}%", ln=True)
    pdf.multi_cell(0, 8, f"Guidance: {_risk_guidance(record['risk_level'])}")
    pdf.ln(2)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Symptoms", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, ", ".join(record["symptoms"]))
    pdf.ln(2)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Top Predictions", ln=True)
    pdf.set_font("Arial", "", 11)
    for item in top_predictions:
        pdf.cell(0, 8, f"- {item['disease']}: {item['percent']:.2f}%", ln=True)

    rendered = pdf.output(dest="S")
    if isinstance(rendered, (bytes, bytearray)):
        content = bytes(rendered)
    else:
        content = str(rendered).encode("latin-1")
    filename = f"prediction_report_{record_id}.pdf"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
