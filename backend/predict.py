from __future__ import annotations

import argparse
import numpy as np

try:
    from backend.torch_artifacts import load_artifacts, predict_top_k
except Exception:  # pragma: no cover
    from torch_artifacts import load_artifacts, predict_top_k


def predict_from_symptoms(symptoms: list[str], top_k: int = 5) -> None:
    artifacts = load_artifacts()
    symptom_columns = artifacts.symptom_columns
    symptom_index = {name: idx for idx, name in enumerate(symptom_columns)}

    cleaned: list[str] = []
    for symptom in symptoms:
        normalized = symptom.strip().lower()
        if normalized and normalized not in cleaned:
            cleaned.append(normalized)

    invalid = sorted([s for s in cleaned if s not in symptom_index])
    if invalid:
        print("Invalid symptoms:", ", ".join(invalid))
        print("Use only symptoms present in symptom_columns.json.")
        return

    vector = np.zeros(len(symptom_columns), dtype=int)
    for symptom in cleaned:
        vector[symptom_index[symptom]] = 1

    prediction, top_predictions, confidence, _ = predict_top_k(artifacts, vector, k=top_k)
    print(f"\nPredicted Disease: {prediction} ({confidence * 100:.2f}%)")
    print(f"\nTop {max(1, top_k)} Possible Diseases:")
    for item in top_predictions:
        print(f"- {item['disease']} -> {item['percent']:.2f}%")


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
