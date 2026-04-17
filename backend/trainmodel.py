import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score
import warnings

warnings.filterwarnings("ignore")
df = pd.read_csv("Disease/processed_disease_dataset.csv")

# Ensure no null values
df.dropna(inplace=True)
for col in df.columns[1:]:
    df[col] = df[col].astype(int)

print("Dataset shape:", df.shape)
print("Total diseases:", df["Disease"].nunique())
X = df.drop("Disease", axis=1)
y = df["Disease"]


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=400,          # more trees = better stability
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    class_weight="balanced",   # handle imbalance
    random_state=42,
    n_jobs=-1                  # use all CPU cores
)

model.fit(X_train, y_train)
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print("\nModel Accuracy:", round(accuracy * 100, 2), "%")

cv_scores = cross_val_score(model, X, y, cv=5, n_jobs=-1)

print("Cross Validation Accuracy:", round(cv_scores.mean() * 100, 2), "%")
probs = model.predict_proba(X_test)

sample_probs = probs[0]

top3_indices = np.argsort(sample_probs)[-3:][::-1]
top3_diseases = model.classes_[top3_indices]
top3_probabilities = sample_probs[top3_indices]

print("\nTop 3 Predictions for First Test Case:")
for disease, prob in zip(top3_diseases, top3_probabilities):
    print(f"{disease} → {round(prob * 100, 2)}%")
importances = pd.Series(model.feature_importances_, index=X.columns)
top_features = importances.sort_values(ascending=False).head(10)

print("\nTop Important Symptoms:")
print(top_features)
joblib.dump(model, "disease_prediction_model.pkl")
joblib.dump(X.columns.tolist(), "symptom_columns.pkl")

print("\nModel and symptom columns saved successfully.")
