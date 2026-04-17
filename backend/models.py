from pydantic import BaseModel, Field
from typing import Any, Optional


class PredictionRequest(BaseModel):
    """Request model for prediction endpoint."""
    name: str = Field(min_length=1, max_length=100)
    fname: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=120)
    gender: str = Field(min_length=1, max_length=30)
    basic_info: str = Field(default="", max_length=500)
    symptoms: list[str] = Field(min_length=1, max_length=131)


class PredictionRecord(BaseModel):
    """Response model for prediction history."""
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


class TopPrediction(BaseModel):
    """Model for top prediction items."""
    disease: str
    probability: float
    percent: float


class SymptomContribution(BaseModel):
    """Model for symptom contribution in XAI."""
    symptom: str
    contribution: float
    abs_contribution: float


class Explanation(BaseModel):
    """Model for prediction explanation."""
    method: str
    top_contributors: list[SymptomContribution]


class FeatureImportance(BaseModel):
    """Model for feature importance."""
    symptom: str
    importance: float