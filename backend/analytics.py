from typing import Any

try:
    from backend.config import SYMPTOM_COLUMNS
    from backend.database import get_analytics_data as _get_analytics_data
except ImportError:  # pragma: no cover
    from config import SYMPTOM_COLUMNS
    from database import get_analytics_data as _get_analytics_data


def get_analytics_data() -> dict[str, Any]:
    """Get analytics data from normalized database tables."""
    return _get_analytics_data(symptom_columns=SYMPTOM_COLUMNS)
