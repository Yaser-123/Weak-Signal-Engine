# src/dashboard/time_filter.py

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta


def compute_time_slider_bounds(clusters: List[Dict[str, Any]]) -> Tuple[int, int, int]:
    """
    Compute dynamic time slider bounds based on actual data.
    
    Args:
        clusters: List of cluster dictionaries with signals containing timestamps
    
    Returns:
        Tuple of (min_value, max_value, default_value) in days
        - min_value: Always 1 day
        - max_value: Days between oldest signal and now (minimum 7 for slider to work)
        - default_value: 30% of max_value, clamped to at least 7 days
    """
    if not clusters:
        # Fallback for empty dataset
        return (1, 30, 7)
    
    # Extract all timestamps from all signals
    all_timestamps = []
    for cluster in clusters:
        for signal in cluster.get("signals", []):
            timestamp_str = signal.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    all_timestamps.append(timestamp)
                except (ValueError, TypeError):
                    continue
    
    if not all_timestamps:
        # Fallback if no valid timestamps found
        return (1, 30, 7)
    
    # Find oldest and newest timestamps
    oldest_timestamp = min(all_timestamps)
    now = datetime.now()
    
    # Compute max_days (days between oldest signal and now)
    max_days = max(1, (now - oldest_timestamp).days)
    
    # If data is too recent (all signals within 1 day), set reasonable defaults
    if max_days <= 1:
        max_days = 7  # Default to 7 days for slider to work
    
    # Compute default as ALL days (show all historical signals for weak signal accumulation)
    default_days = max_days
    
    # Ensure default doesn't exceed max
    default_days = min(default_days, max_days)
    
    return (1, max_days, default_days)


def filter_clusters_by_time(
    clusters: List[Dict[str, Any]],
    days: int
) -> List[Dict[str, Any]]:
    """
    Filter clusters to show only signals from the last N days.
    
    Args:
        clusters: List of cluster dictionaries
        days: Number of days to look back
    
    Returns:
        List of filtered clusters with updated signal_count and growth metrics.
        Only includes clusters with at least 2 signals in the time window.
    """
    if not clusters:
        return []
    
    now = datetime.now()
    cutoff_time = now - timedelta(days=days)
    
    filtered_clusters = []
    
    for cluster in clusters:
        original_signals = cluster.get("signals", [])
        original_count = len(original_signals)
        
        # Filter signals by timestamp
        recent_signals = []
        for signal in original_signals:
            timestamp_str = signal.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp >= cutoff_time:
                        recent_signals.append(signal)
                except (ValueError, TypeError):
                    # If timestamp is invalid, include the signal
                    recent_signals.append(signal)
            else:
                # If no timestamp, include the signal
                recent_signals.append(signal)
        
        filtered_signal_count = len(recent_signals)
        
        # Only keep clusters with at least 1 signal in the time window
        if filtered_signal_count >= 1:
            # Create a copy of the cluster with filtered data
            filtered_cluster = {**cluster}
            filtered_cluster["signals"] = recent_signals
            filtered_cluster["signal_count"] = filtered_signal_count
            
            # Compute growth ratio (recent / total)
            growth_ratio = filtered_signal_count / original_count if original_count > 0 else 0.0
            filtered_cluster["growth_ratio"] = growth_ratio
            
            # Also filter embeddings if present
            if "embeddings" in cluster and len(cluster["embeddings"]) == original_count:
                # Map filtered signals to their original indices
                filtered_embeddings = []
                for i, signal in enumerate(original_signals):
                    if signal in recent_signals:
                        filtered_embeddings.append(cluster["embeddings"][i])
                filtered_cluster["embeddings"] = filtered_embeddings
            
            filtered_clusters.append(filtered_cluster)
    
    return filtered_clusters
