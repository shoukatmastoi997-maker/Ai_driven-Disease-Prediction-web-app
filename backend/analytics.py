import json
import sqlite3
from collections import Counter
from typing import Any

from backend.config import DB_PATH, PROCESSED_DATA_PATH, SYMPTOM_COLUMNS
import pandas as pd


def get_analytics_data() -> dict[str, Any]:
    """Get analytics data from database and processed dataset."""
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
    
    # Load processed dataset if available
    processed_df = pd.read_csv(PROCESSED_DATA_PATH) if PROCESSED_DATA_PATH.exists() else pd.DataFrame()
    
    # Disease frequency
    if disease_rows:
        disease_frequency = [{"disease": row[0], "count": int(row[1])} for row in disease_rows]
    elif not processed_df.empty and "Disease" in processed_df.columns:
        counts = processed_df["Disease"].value_counts()
        disease_frequency = [{"disease": str(k), "count": int(v)} for k, v in counts.items()]
    else:
        disease_frequency = []
    
    # Symptom occurrence
    if not processed_df.empty:
        available_symptom_cols = [c for c in SYMPTOM_COLUMNS if c in processed_df.columns]
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
    
    # Risk distribution
    risk_distribution = [{"risk_level": row[0], "count": int(row[1])} for row in risk_rows]
    
    # Severity progression
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
    
    # Top disease trend
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