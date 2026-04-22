# API Reference

Base URL (default): `http://localhost:8000`

## Health

### `GET /health`

Returns basic service + model status.

## Symptoms

### `GET /api/symptoms`

Returns the list of valid symptoms (schema for the trained model).

## Feature Importance

### `GET /api/feature-importance?top_n=15`

Returns symptom “importance” based on dataset frequency (not model weights).

## Predict

### `POST /api/predict`

Body:

```json
{
  "name": "Patient Name",
  "fname": "Father Name",
  "age": 30,
  "gender": "Male",
  "basic_info": "Optional notes",
  "symptoms": ["headache", "fatigue"]
}
```

Returns:

- `record_id` for the saved record in SQLite
- `prediction`, `confidence`, `top_predictions`
- `risk_level`, `risk_guidance`
- `xai` with `method` and `top_contributors`

## History (Database)

### `GET /api/history?limit=50`

Returns a lightweight list of stored records.

### `GET /api/history-full?limit=100`

Returns full stored rows including `basic_info` and `top_predictions`.

## PDF Report

### `GET /api/report/{record_id}`

Returns a PDF report for a stored record.

The frontend Database page fetches this as a blob and opens a printable viewer.

