# src/dashboard/feed.py

from typing import List, Dict, Any

from src.scoring.emergence import compute_emergence


EMERGENCE_PRIORITY = {
    "rapid": 3,
    "stable": 2,
    "dormant": 1
}


def build_emerging_feed(
    proto_clusters: List[Dict[str, Any]],
    recent_days: int = 30
) -> List[Dict[str, Any]]:
    feed = []

    for cluster in proto_clusters:
        emergence = compute_emergence(cluster, recent_days=recent_days)

        feed.append({
            "cluster_id": cluster["cluster_id"],
            "signal_count": cluster["signal_count"],
            "emergence_level": emergence["emergence_level"],
            "growth_ratio": emergence["growth_ratio"],
            "created_at": cluster["created_at"],
            "representative_title": cluster["signals"][0]["text"][:120] if cluster["signals"] else "No signals"
        })

    feed.sort(
        key=lambda x: (
            EMERGENCE_PRIORITY[x["emergence_level"]],
            x["growth_ratio"]
        ),
        reverse=True
    )

    return feed