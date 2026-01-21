# test_temporal_merging.py

"""
Test script to validate temporal weak-signal accumulation.
This simulates the scenario where similar signals appear across multiple "days".
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.embeddings.embedding_model import EmbeddingModel
from src.clustering.cluster_evolution import evolve_clusters
from src.clustering.intra_batch_cluster import cluster_batch
from datetime import datetime

def create_mock_signals(day_signals):
    """Create mock signals with timestamps for different days"""
    signals = []
    signal_id = 0

    for day, texts in day_signals.items():
        for text in texts:
            signals.append({
                "signal_id": f"mock_{signal_id}",
                "text": text,
                "timestamp": f"2026-01-{day:02d}T10:00:00.000000",
                "source": "mock_feed",
                "domain": "test",
                "subdomain": "test",
                "metadata": {}
            })
            signal_id += 1

    return signals

def simulate_day_run(existing_candidates, new_signals, embedding_model):
    """Simulate one day of processing"""

    # Convert signals to signals_with_embeddings format
    signals_with_embeddings = []
    for signal in new_signals:
        embedding = embedding_model.embed(signal["text"])
        signals_with_embeddings.append({
            "signal": signal,
            "embedding": embedding
        })

    # Intra-batch clustering (within this day's signals)
    batch_clusters = cluster_batch(signals_with_embeddings, similarity_threshold=0.45)

    print(f"Day processing: {len(new_signals)} new signals → {len(batch_clusters)} batch clusters")

    # Evolve clusters (merge batch clusters into existing candidates)
    updated_candidates = evolve_clusters(
        existing_candidates=existing_candidates,
        new_batch_clusters=batch_clusters,
        embedding_model=embedding_model,
        similarity_threshold=0.60  # Lower threshold for easier merging
    )

    return updated_candidates

def main():
    print("=== Testing Temporal Weak-Signal Accumulation ===\n")

    embedding_model = EmbeddingModel()

    # Simulate signals appearing over 3 days
    # Day 1: Initial signals about AI power consumption
    day1_signals = [
        "AI data centers are consuming massive amounts of electricity",
        "Machine learning workloads require specialized cooling systems",
        "GPU clusters need high-power electrical infrastructure"
    ]

    # Day 2: Similar signals about the same topic
    day2_signals = [
        "Deep learning models are driving up energy costs significantly",
        "Neural network training requires enormous computational power",
        "AI chips generate substantial heat that needs cooling solutions"
    ]

    # Day 3: More signals on the evolving topic
    day3_signals = [
        "Large language models consume electricity equivalent to small cities",
        "Transformer architectures demand massive parallel processing",
        "AI inference workloads are becoming power-intensive"
    ]

    # Start with empty candidates
    candidates = []

    print("Day 1: Processing initial signals...")
    day1_mock_signals = create_mock_signals({1: day1_signals})
    candidates = simulate_day_run(candidates, day1_mock_signals, embedding_model)

    print(f"After Day 1: {len(candidates)} total candidate clusters")
    for i, c in enumerate(candidates):
        print(f"  Cluster {i+1}: {c['signal_count']} signals")

    print("\nDay 2: Processing similar signals...")
    day2_mock_signals = create_mock_signals({2: day2_signals})
    candidates = simulate_day_run(candidates, day2_mock_signals, embedding_model)

    print(f"After Day 2: {len(candidates)} total candidate clusters")
    for i, c in enumerate(candidates):
        print(f"  Cluster {i+1}: {c['signal_count']} signals")

    print("\nDay 3: Processing more related signals...")
    day3_mock_signals = create_mock_signals({3: day3_signals})
    candidates = simulate_day_run(candidates, day3_mock_signals, embedding_model)

    print(f"After Day 3: {len(candidates)} total candidate clusters")
    for i, c in enumerate(candidates):
        print(f"  Cluster {i+1}: {c['signal_count']} signals")

    print("\n=== VALIDATION ===")
    total_signals = sum(c['signal_count'] for c in candidates)
    expected_signals = len(day1_signals) + len(day2_signals) + len(day3_signals)

    print(f"Total signals accumulated: {total_signals}")
    print(f"Expected signals: {expected_signals}")
    print(f"Signals preserved: {'✓' if total_signals == expected_signals else '✗'}")

    # Check if merging occurred (fewer clusters than total batches)
    total_batches = 3  # One batch per day
    print(f"Clusters created: {len(candidates)} (vs {total_batches} batches)")
    print(f"Merging occurred: {'✓' if len(candidates) < total_batches else '✗'}")

    if len(candidates) == 1 and total_signals == expected_signals:
        print("\n🎉 SUCCESS: Temporal accumulation working! Signals merged across days.")
    else:
        print("\n❌ ISSUE: Temporal accumulation not working properly.")

if __name__ == "__main__":
    main()