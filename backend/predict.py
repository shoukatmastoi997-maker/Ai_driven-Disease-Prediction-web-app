from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "disease_prediction_model.pkl"
SYMPTOMS_PATH = BASE_DIR / "symptom_columns.pkl"


def predict_from_symptoms(symptoms: list[str], top_k: int = 5) -> None:
    model = joblib.load(MODEL_PATH)
    symptom_columns = [s.strip().lower() for s in joblib.load(SYMPTOMS_PATH)]
    symptom_index = {name: idx for idx, name in enumerate(symptom_columns)}

    cleaned: list[str] = []
    for symptom in symptoms:
        normalized = symptom.strip().lower()
        if normalized and normalized not in cleaned:
            cleaned.append(normalized)

    invalid = sorted([s for s in cleaned if s not in symptom_index])
    if invalid:
        print("Invalid symptoms:", ", ".join(invalid))
        print("Use only symptoms present in symptom_columns.pkl.")
        return

    vector = np.zeros(len(symptom_columns), dtype=int)
    for symptom in cleaned:
        vector[symptom_index[symptom]] = 1

    x_input = pd.DataFrame([vector], columns=symptom_columns)
    prediction = model.predict(x_input)[0]
    print(f"\nPredicted Disease: {prediction}")

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(x_input)[0]
        top_indices = np.argsort(probabilities)[-top_k:][::-1]
        print(f"\nTop {top_k} Possible Diseases:")
        for idx in top_indices:
            print(f"- {model.classes_[idx]} -> {probabilities[idx] * 100:.2f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict disease from symptoms")
    parser.add_argument(
        "--symptoms",
        nargs="+",
        required=True,
        help="Space-separated symptoms, e.g. --symptoms shivering continuous_sneezing",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Number of top predictions")
    args = parser.parse_args()

    predict_from_symptoms(args.symptoms, top_k=max(1, args.top_k))
