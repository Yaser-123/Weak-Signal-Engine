# test_time_filter.py
# Test dynamic time filtering

import json
from src.dashboard.time_filter import compute_time_slider_bounds, filter_clusters_by_time
from datetime import datetime

# Load clusters
with open("candidate_clusters.json", "r", encoding="utf-8") as f:
    clusters = json.load(f)

print(f"Loaded {len(clusters)} clusters")

# Test compute_time_slider_bounds
min_days, max_days, default_days = compute_time_slider_bounds(clusters)

print("\n" + "="*60)
print("TIME SLIDER BOUNDS")
print("="*60)
print(f"Min days: {min_days}")
print(f"Max days: {max_days}")
print(f"Default days (30% of max, min 7): {default_days}")

# Find oldest timestamp
all_timestamps = []
for cluster in clusters:
    for signal in cluster.get("signals", []):
        timestamp_str = signal.get("timestamp")
        if timestamp_str:
            all_timestamps.append(datetime.fromisoformat(timestamp_str))

oldest = min(all_timestamps)
newest = max(all_timestamps)
now = datetime.now()

print(f"\nOldest signal: {oldest.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Newest signal: {newest.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Time span: {(newest - oldest).days} days")

# Test filtering at different time ranges
test_ranges = [1, 7, 30, max_days]

print("\n" + "="*60)
print("TIME FILTER RESULTS")
print("="*60)

for days in test_ranges:
    filtered = filter_clusters_by_time(clusters, days)
    
    total_signals_before = sum(len(c.get("signals", [])) for c in clusters)
    total_signals_after = sum(c.get("signal_count", 0) for c in filtered)
    
    print(f"\nLast {days} days:")
    print(f"  Clusters: {len(clusters)} → {len(filtered)}")
    print(f"  Signals: {total_signals_before} → {total_signals_after}")
    print(f"  Active (≥3 signals): {len([c for c in filtered if c['signal_count'] >= 3])}")
    
    if filtered:
        avg_growth = sum(c.get("growth_ratio", 0) for c in filtered) / len(filtered)
        print(f"  Avg growth ratio: {avg_growth:.2%}")

print("\n" + "="*60)
