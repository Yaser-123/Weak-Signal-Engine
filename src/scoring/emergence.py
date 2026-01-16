# src/scoring/emergence.py

from typing import Dict, Any
from datetime import datetime, timedelta


def compute_emergence(
    proto_cluster: Dict[str, Any],
    recent_days: int = 30
) -> Dict[str, Any]:
    now = datetime.utcnow()
    cutoff = now - timedelta(days=recent_days)

    timestamps = [
        datetime.fromisoformat(signal["timestamp"])
        for signal in proto_cluster["signals"]
    ]

    recent_count = sum(1 for ts in timestamps if ts >= cutoff)
    total_count = len(timestamps)

    growth_ratio = recent_count / total_count if total_count > 0 else 0.0

    if growth_ratio >= 0.6:
        emergence_level = "rapid"
    elif growth_ratio >= 0.3:
        emergence_level = "stable"
    else:
        emergence_level = "dormant"

    return {
        "recent_count": recent_count,
        "total_count": total_count,
        "growth_ratio": round(growth_ratio, 2),
        "emergence_level": emergence_level
    }