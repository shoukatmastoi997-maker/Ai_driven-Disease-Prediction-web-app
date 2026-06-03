from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

try:
    from backend.config import DB_PATH, PROCESSED_DATA_PATH
except ImportError:  # pragma: no cover
    from config import DB_PATH, PROCESSED_DATA_PATH

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS PATIENT (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Fname TEXT NOT NULL,
    Age INTEGER NOT NULL,
    Gender TEXT NOT NULL,
    basic_info TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS SYMPTOM (
    symptom_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symptom_name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS DISEASE (
    disease_id INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_name TEXT NOT NULL UNIQUE,
    description TEXT,
    icd_code TEXT
);

CREATE TABLE IF NOT EXISTS PREDICTIONS (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    Date TEXT NOT NULL,
    Time TEXT NOT NULL,
    Symptoms TEXT NOT NULL,
    predicted_disease TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    Confidence REAL NOT NULL,
    top_predictions TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES PATIENT(patient_id)
);

CREATE TABLE IF NOT EXISTS PREDICTION_SYMPTOM (
    prediction_id INTEGER NOT NULL,
    symptom_id INTEGER NOT NULL,
    PRIMARY KEY (prediction_id, symptom_id),
    FOREIGN KEY (prediction_id) REFERENCES PREDICTIONS(Id) ON DELETE CASCADE,
    FOREIGN KEY (symptom_id) REFERENCES SYMPTOM(symptom_id)
);

CREATE TABLE IF NOT EXISTS PREDICTION_TOP_PREDICTION (
    prediction_id INTEGER NOT NULL,
    disease_id INTEGER NOT NULL,
    probability REAL NOT NULL,
    Rank INTEGER NOT NULL,
    PRIMARY KEY (prediction_id, disease_id),
    FOREIGN KEY (prediction_id) REFERENCES PREDICTIONS(Id) ON DELETE CASCADE,
    FOREIGN KEY (disease_id) REFERENCES DISEASE(disease_id)
);

CREATE TABLE IF NOT EXISTS REPORTS (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    report_path TEXT,
    generated_at TEXT NOT NULL,
    FOREIGN KEY (prediction_id) REFERENCES PREDICTIONS(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS MODEL_ARTIFACTS (
    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    training_dataset TEXT NOT NULL,
    created_on TEXT NOT NULL
);
"""

_FLAT_SELECT = """
SELECT
    pr.Id,
    pr.created_at,
    pr.Date,
    pr.Time,
    pt.Name,
    pt.Fname,
    pt.Age,
    pt.Gender,
    pt.basic_info,
    pr.Symptoms,
    pr.predicted_disease,
    pr.risk_level,
    pr.Confidence,
    pr.top_predictions
FROM PREDICTIONS pr
JOIN PATIENT pt ON pr.patient_id = pt.patient_id
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _is_legacy_predictions_table(conn: sqlite3.Connection) -> bool:
    """Detect the old flat `predictions` table (SQLite folds name case)."""
    row = conn.execute(
        """
        SELECT sql FROM sqlite_master
        WHERE type = 'table' AND lower(name) = 'predictions'
        """
    ).fetchone()
    if not row or not row[0]:
        return False
    ddl = str(row[0]).lower()
    return "patient_id" not in ddl and "name" in ddl


def _rename_legacy_predictions_table(conn: sqlite3.Connection) -> None:
    """Rename flat table so it does not collide with normalized PREDICTIONS."""
    if not _is_legacy_predictions_table(conn):
        return
    conn.execute("ALTER TABLE predictions RENAME TO predictions_legacy")


def _ensure_predictions_table(conn: sqlite3.Connection) -> None:
    """Recreate PREDICTIONS if a partial migration left helper tables without it."""
    row = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name = 'PREDICTIONS'
        """
    ).fetchone()
    if row:
        return
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS PREDICTIONS (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            Date TEXT NOT NULL,
            Time TEXT NOT NULL,
            Symptoms TEXT NOT NULL,
            predicted_disease TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            Confidence REAL NOT NULL,
            top_predictions TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES PATIENT(patient_id)
        )
        """
    )


def ensure_db(
    *,
    symptom_columns: list[str],
    disease_classes: list[str],
) -> None:
    """Create normalized tables, seed reference data, and migrate legacy rows."""
    with _connect() as conn:
        _rename_legacy_predictions_table(conn)
        conn.executescript(_SCHEMA_SQL)
        _ensure_predictions_table(conn)
        _seed_symptoms(conn, symptom_columns)
        _seed_diseases(conn, disease_classes)
        _seed_model_artifact(conn)
        _migrate_legacy_predictions(conn)
        conn.commit()


def _seed_symptoms(conn: sqlite3.Connection, symptom_columns: list[str]) -> None:
    for name in symptom_columns:
        conn.execute(
            """
            INSERT OR IGNORE INTO SYMPTOM (symptom_name, description)
            VALUES (?, ?)
            """,
            (name, f"Symptom indicator: {name.replace('_', ' ')}"),
        )


def _seed_diseases(conn: sqlite3.Connection, disease_classes: list[str]) -> None:
    for name in disease_classes:
        conn.execute(
            """
            INSERT OR IGNORE INTO DISEASE (disease_name, description, icd_code)
            VALUES (?, ?, ?)
            """,
            (name, f"Predictable disease: {name}", ""),
        )


def _seed_model_artifact(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM MODEL_ARTIFACTS").fetchone()[0]
    if existing:
        return
    created_on = datetime.now().isoformat(timespec="seconds")
    dataset = PROCESSED_DATA_PATH.name if PROCESSED_DATA_PATH.exists() else "processed_disease_dataset.csv"
    conn.execute(
        """
        INSERT INTO MODEL_ARTIFACTS (model_name, model_version, training_dataset, created_on)
        VALUES (?, ?, ?, ?)
        """,
        ("DiseaseMLP", "1.0", dataset, created_on),
    )


def _get_symptom_id(conn: sqlite3.Connection, symptom_name: str) -> int:
    row = conn.execute(
        "SELECT symptom_id FROM SYMPTOM WHERE symptom_name = ?",
        (symptom_name,),
    ).fetchone()
    if row:
        return int(row[0])
    cursor = conn.execute(
        "INSERT INTO SYMPTOM (symptom_name, description) VALUES (?, ?)",
        (symptom_name, f"Symptom indicator: {symptom_name.replace('_', ' ')}"),
    )
    return int(cursor.lastrowid)


def _get_disease_id(conn: sqlite3.Connection, disease_name: str) -> int:
    row = conn.execute(
        "SELECT disease_id FROM DISEASE WHERE disease_name = ?",
        (disease_name,),
    ).fetchone()
    if row:
        return int(row[0])
    cursor = conn.execute(
        "INSERT INTO DISEASE (disease_name, description, icd_code) VALUES (?, ?, ?)",
        (disease_name, f"Predictable disease: {disease_name}", ""),
    )
    return int(cursor.lastrowid)


def _insert_patient(
    conn: sqlite3.Connection,
    *,
    name: str,
    fname: str,
    age: int,
    gender: str,
    basic_info: str,
    created_at: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO PATIENT (Name, Fname, Age, Gender, basic_info, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, fname, age, gender, basic_info or None, created_at),
    )
    return int(cursor.lastrowid)


def _link_prediction_symptoms(
    conn: sqlite3.Connection,
    prediction_id: int,
    symptoms: list[str],
) -> None:
    for symptom in symptoms:
        symptom_id = _get_symptom_id(conn, symptom)
        conn.execute(
            """
            INSERT OR IGNORE INTO PREDICTION_SYMPTOM (prediction_id, symptom_id)
            VALUES (?, ?)
            """,
            (prediction_id, symptom_id),
        )


def _link_prediction_top_predictions(
    conn: sqlite3.Connection,
    prediction_id: int,
    top_predictions: list[dict[str, Any]],
) -> None:
    for rank, item in enumerate(top_predictions, start=1):
        disease_name = str(item["disease"])
        probability = float(item.get("probability", item.get("percent", 0) / 100.0))
        disease_id = _get_disease_id(conn, disease_name)
        conn.execute(
            """
            INSERT OR REPLACE INTO PREDICTION_TOP_PREDICTION
                (prediction_id, disease_id, probability, Rank)
            VALUES (?, ?, ?, ?)
            """,
            (prediction_id, disease_id, probability, rank),
        )


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
    """Save a prediction across normalized tables; returns prediction Id."""
    dt = datetime.fromisoformat(created_at)
    with _connect() as conn:
        patient_id = _insert_patient(
            conn,
            name=name,
            fname=fname,
            age=age,
            gender=gender,
            basic_info=basic_info,
            created_at=created_at,
        )
        cursor = conn.execute(
            """
            INSERT INTO PREDICTIONS (
                patient_id, created_at, Date, Time, Symptoms,
                predicted_disease, risk_level, Confidence, top_predictions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                created_at,
                dt.date().isoformat(),
                dt.time().strftime("%H:%M:%S"),
                json.dumps(symptoms),
                predicted_disease,
                risk_level,
                confidence,
                json.dumps(top_predictions),
            ),
        )
        prediction_id = int(cursor.lastrowid)
        _link_prediction_symptoms(conn, prediction_id, symptoms)
        _link_prediction_top_predictions(conn, prediction_id, top_predictions)
        conn.commit()
        return prediction_id


def save_report(*, prediction_id: int, report_path: str) -> int:
    """Record a generated PDF report for a prediction."""
    generated_at = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO REPORTS (prediction_id, report_path, generated_at)
            VALUES (?, ?, ?)
            """,
            (prediction_id, report_path, generated_at),
        )
        conn.commit()
        return int(cursor.lastrowid)


def parse_history_row(row: tuple[Any, ...]) -> dict[str, Any]:
    """Parse a flat joined row into the API-facing dictionary."""
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


def _build_history_query(
    *,
    search: str | None,
    risk_level: str | None,
) -> tuple[str, list[Any]]:
    query = _FLAT_SELECT
    clauses: list[str] = []
    params: list[Any] = []

    if search:
        clauses.append("(LOWER(pt.Name) LIKE ? OR LOWER(pr.predicted_disease) LIKE ?)")
        search_term = f"%{search.strip().lower()}%"
        params.extend([search_term, search_term])

    if risk_level:
        clauses.append("LOWER(pr.risk_level) = LOWER(?)")
        params.append(risk_level.strip())

    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY pr.created_at DESC LIMIT ?"
    return query, params


def list_predictions(
    *,
    limit: int,
    search: str | None = None,
    risk_level: str | None = None,
) -> list[dict[str, Any]]:
    """Return full prediction records for dashboard/history-full."""
    query, params = _build_history_query(search=search, risk_level=risk_level)
    params.append(limit)
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [parse_history_row(row) for row in rows]


def list_predictions_summary(
    *,
    limit: int,
    search: str | None = None,
    risk_level: str | None = None,
) -> list[dict[str, Any]]:
    """Return compact history rows matching the /api/history response."""
    parsed = list_predictions(limit=limit, search=search, risk_level=risk_level)
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


def get_prediction_by_id(record_id: int) -> Optional[dict[str, Any]]:
    """Get a specific prediction by Id."""
    with _connect() as conn:
        row = conn.execute(
            f"{_FLAT_SELECT} WHERE pr.Id = ?",
            (record_id,),
        ).fetchone()
    return parse_history_row(row) if row else None


def get_analytics_data(*, symptom_columns: list[str]) -> dict[str, Any]:
    """Aggregate analytics from normalized tables (same API shape as before)."""
    with _connect() as conn:
        disease_rows = conn.execute(
            """
            SELECT predicted_disease, COUNT(*)
            FROM PREDICTIONS
            GROUP BY predicted_disease
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()
        risk_rows = conn.execute(
            """
            SELECT risk_level, COUNT(*)
            FROM PREDICTIONS
            GROUP BY risk_level
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()
        progression_rows = conn.execute(
            """
            SELECT Date, risk_level, COUNT(*) as c
            FROM PREDICTIONS
            GROUP BY Date, risk_level
            ORDER BY Date ASC
            """
        ).fetchall()
        symptom_rows = conn.execute("SELECT Symptoms FROM PREDICTIONS").fetchall()
        total_predictions = conn.execute("SELECT COUNT(*) FROM PREDICTIONS").fetchone()[0]

    processed_df = pd.read_csv(PROCESSED_DATA_PATH) if PROCESSED_DATA_PATH.exists() else pd.DataFrame()

    if disease_rows:
        disease_frequency = [{"disease": row[0], "count": int(row[1])} for row in disease_rows]
    elif not processed_df.empty and "Disease" in processed_df.columns:
        counts = processed_df["Disease"].value_counts()
        disease_frequency = [{"disease": str(k), "count": int(v)} for k, v in counts.items()]
    else:
        disease_frequency = []

    if not processed_df.empty:
        available_symptom_cols = [c for c in symptom_columns if c in processed_df.columns]
        if available_symptom_cols:
            sums = processed_df[available_symptom_cols].sum().sort_values(ascending=False).head(20)
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
        with _connect() as conn:
            trend_rows = conn.execute(
                """
                SELECT Date, COUNT(*) as c
                FROM PREDICTIONS
                WHERE predicted_disease = ?
                GROUP BY Date
                ORDER BY Date ASC
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


def _migrate_legacy_predictions(conn: sqlite3.Connection) -> None:
    """Move rows from the old single-table `predictions_legacy` store if present."""
    legacy = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name = 'predictions_legacy'
        """
    ).fetchone()
    if not legacy:
        return

    rows = conn.execute(
        """
        SELECT id, created_at, date, time, name, fname, age, gender, basic_info,
               symptoms, predicted_disease, risk_level, confidence, top_predictions
        FROM predictions_legacy
        ORDER BY id ASC
        """
    ).fetchall()
    if not rows:
        conn.execute("DROP TABLE IF EXISTS predictions_legacy")
        return

    existing = conn.execute("SELECT COUNT(*) FROM PREDICTIONS").fetchone()[0]
    if existing:
        conn.execute("DROP TABLE IF EXISTS predictions_legacy")
        return

    for row in rows:
        (
            _legacy_id,
            created_at,
            date_str,
            time_str,
            name,
            fname,
            age,
            gender,
            basic_info,
            symptoms_json,
            predicted_disease,
            risk_level,
            confidence,
            top_predictions_json,
        ) = row
        symptoms = json.loads(symptoms_json)
        top_predictions = json.loads(top_predictions_json)

        patient_id = _insert_patient(
            conn,
            name=name,
            fname=fname,
            age=int(age),
            gender=gender,
            basic_info=basic_info or "",
            created_at=created_at,
        )
        cursor = conn.execute(
            """
            INSERT INTO PREDICTIONS (
                patient_id, created_at, Date, Time, Symptoms,
                predicted_disease, risk_level, Confidence, top_predictions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                created_at,
                date_str,
                time_str,
                symptoms_json,
                predicted_disease,
                risk_level,
                float(confidence),
                top_predictions_json,
            ),
        )
        prediction_id = int(cursor.lastrowid)
        _link_prediction_symptoms(conn, prediction_id, symptoms)
        _link_prediction_top_predictions(conn, prediction_id, top_predictions)

    conn.execute("DROP TABLE IF EXISTS predictions_legacy")


# Backward-compatible aliases
get_predictions = list_predictions
