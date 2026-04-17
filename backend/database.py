import sqlite3
import json
from datetime import datetime
from typing import Any, Optional

from backend.config import DB_PATH, PROCESSED_DATA_PATH
import pandas as pd


def ensure_db() -> None:
    """Ensure database and tables exist."""
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


def save_prediction(
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
    """Save prediction to database."""
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


def parse_history_row(row: tuple[Any, ...]) -> dict[str, Any]:
    """Parse a database row into a dictionary."""
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


def get_predictions(limit: int) -> list[dict[str, Any]]:
    """Get recent predictions from database."""
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
    
    return [parse_history_row(row) for row in rows]


def get_prediction_by_id(record_id: int) -> Optional[dict[str, Any]]:
    """Get a specific prediction by ID."""
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
    
    return parse_history_row(row) if row else None