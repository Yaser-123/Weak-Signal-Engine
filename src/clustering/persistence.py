# src/clustering/persistence.py

from typing import Dict, Any


def check_persistence(
    contextualized_output: Dict[str, Any],
    min_similar: int = 2
) -> Dict[str, Any]:
    similar_count = contextualized_output.get("similar_count", 0)

    is_persistent = similar_count >= min_similar

    reason = (
        f"Found {similar_count} semantically similar past signals."
        if is_persistent
        else f"Only {similar_count} similar signals found; treated as noise."
    )

    return {
        "is_persistent": is_persistent,
        "similar_count": similar_count,
        "reason": reason
    }